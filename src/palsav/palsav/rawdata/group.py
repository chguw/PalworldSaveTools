from typing import Sequence

from palsav.archive import *

V1_MARKER = b"\x02\x00\x00\x00\x02\x03\x00\x00\x00\x00"


def player_info_reader(reader: FArchiveReader) -> dict[str, Any]:
    return {
        "player_uid": reader.guid(),
        "player_info": {
            "last_online_real_time": reader.i64(),
            "player_name": reader.fstring(),
        },
    }


def player_info_writer(writer: FArchiveWriter, p: dict[str, Any]) -> None:
    writer.guid(p["player_uid"])
    writer.i64(p["player_info"]["last_online_real_time"])
    writer.fstring(p["player_info"]["player_name"])


def decode(
    reader: FArchiveReader, type_name: str, size: int, path: str
) -> dict[str, Any]:
    if type_name != "MapProperty":
        raise Exception(f"Expected MapProperty, got {type_name}")
    value = reader.property(type_name, size, path, nested_caller_path=path)
    # Decode the raw bytes and replace the raw data
    group_map = value["value"]
    for group in group_map:
        group_type = group["value"]["GroupType"]["value"]["value"]
        group_bytes = group["value"]["RawData"]["value"]["values"]
        group["value"]["RawData"]["value"] = decode_bytes(
            reader, group_bytes, group_type
        )
    return value


def decode_bytes(
    parent_reader: FArchiveReader, group_bytes: Sequence[int], group_type: str
) -> dict[str, Any]:
    reader = parent_reader.internal_copy(coerce_bytes(group_bytes), debug=False)
    group_data = {
        "group_type": group_type,
        "group_id": reader.guid(),
        "group_name": reader.fstring(),
        "individual_character_handle_ids": reader.tarray(instance_id_reader),
    }
    if group_type in [
        "EPalGroupType::Guild",
        "EPalGroupType::IndependentGuild",
        "EPalGroupType::Organization",
    ]:
        group_data |= {"org_type": reader.byte()}

    if group_type == "EPalGroupType::Organization":
        group_data |= {"trailing_bytes": reader.byte_list(12)}
        if not reader.eof():
            group_data |= {"unknown_bytes": reader.read_to_end()}
        return group_data

    if group_type == "EPalGroupType::IndependentGuild":
        group_data |= {
            "base_camp_level": reader.i32(),
            "map_object_instance_ids_base_camp_points": reader.tarray(uuid_reader),
            "guild_name": reader.fstring(),
            "player_uid": reader.guid(),
            "guild_name_2": reader.fstring(),
            "player_info": {
                "last_online_real_time": reader.i64(),
                "player_name": reader.fstring(),
            },
        }
        if not reader.eof():
            group_data |= {"unknown_bytes": reader.read_to_end()}
        return group_data

    if group_type == "EPalGroupType::Guild":
        group_data |= {
            "leading_bytes": reader.byte_list(4),
            "base_ids": reader.tarray(uuid_reader),
            "unknown_1": reader.i32(),
            "base_camp_level": reader.i32(),
            "map_object_instance_ids_base_camp_points": reader.tarray(uuid_reader),
            "guild_name": reader.fstring(),
            "last_guild_name_modifier_player_uid": reader.guid(),
            "unknown_2": reader.byte_list(4),
        }

        # Newer save versions embed admin_player_uid + players after a V1 marker
        # that appears inside the remaining bytes. Detect it and parse the tail
        # with a sub-reader so we can round-trip saves without raising.
        remaining = reader.read_to_end()
        v1_offset = remaining.find(V1_MARKER)
        if v1_offset >= 0:
            if v1_offset > 0:
                group_data |= {"_pre_v1_bytes": remaining[:v1_offset]}
            group_data |= {"_v1_header": V1_MARKER}
            post_v1 = remaining[v1_offset + len(V1_MARKER):]
            use_u8 = v1_offset > 0
        else:
            # Pre-V1 (or unknown) layout: try to read admin/players directly,
            # otherwise preserve as opaque trailing bytes.
            post_v1 = remaining
            use_u8 = False

        if post_v1:
            sub = parent_reader.internal_copy(post_v1, debug=False)
            try:
                admin_player_uid = sub.guid()
                player_count = sub.i32()
                players: list[dict[str, Any]] = []
                for _ in range(player_count):
                    entry: dict[str, Any] = {
                        "player_uid": sub.guid(),
                        "player_info": {
                            "last_online_real_time": sub.i64(),
                            "player_name": sub.fstring(),
                        },
                    }
                    if use_u8 and not sub.eof():
                        entry["_u8_flag"] = sub.byte()
                    players.append(entry)
                group_data |= {"admin_player_uid": admin_player_uid}
                group_data |= {"players": players}
                trailing = sub.read_to_end()
                if trailing:
                    group_data |= {"_trailing_bytes": trailing}
            except Exception:
                group_data |= {"_raw_tail": post_v1}
        elif not group_data.get("players"):
            # Ensure the structure has a players list so downstream code is happy.
            group_data |= {"players": []}

    if not reader.eof():
        group_data |= {"unknown_bytes": reader.read_to_end()}
    return group_data


def encode(
    writer: FArchiveWriter, property_type: str, properties: dict[str, Any]
) -> int:
    if property_type != "MapProperty":
        raise Exception(f"Expected MapProperty, got {property_type}")
    del properties["custom_type"]
    group_map = properties["value"]
    for group in group_map:
        if "values" in group["value"]["RawData"]["value"]:
            continue
        p = group["value"]["RawData"]["value"]
        encoded_bytes = encode_bytes(p)
        group["value"]["RawData"]["value"] = {"values": encoded_bytes}
    return writer.property_inner(property_type, properties)


def encode_bytes(p: dict[str, Any]) -> bytes:
    writer = FArchiveWriter()
    writer.guid(p["group_id"])
    writer.fstring(p["group_name"])
    writer.tarray(instance_id_writer, p["individual_character_handle_ids"])
    if p["group_type"] in [
        "EPalGroupType::Guild",
        "EPalGroupType::IndependentGuild",
        "EPalGroupType::Organization",
    ]:
        writer.byte(p["org_type"])

    gt = p["group_type"]
    if gt == "EPalGroupType::Organization":
        writer.write(coerce_bytes(p["trailing_bytes"]))
        if "unknown_bytes" in p:
            writer.write(coerce_bytes(p["unknown_bytes"]))
        return writer.bytes()

    if gt == "EPalGroupType::IndependentGuild":
        writer.i32(p["base_camp_level"])
        writer.tarray(uuid_writer, p["map_object_instance_ids_base_camp_points"])
        writer.fstring(p["guild_name"])
        writer.guid(p["player_uid"])
        writer.fstring(p["guild_name_2"])
        writer.i64(p["player_info"]["last_online_real_time"])
        writer.fstring(p["player_info"]["player_name"])
        if "unknown_bytes" in p:
            writer.write(coerce_bytes(p["unknown_bytes"]))
        return writer.bytes()

    if gt == "EPalGroupType::Guild":
        writer.write(coerce_bytes(p["leading_bytes"]))
        writer.tarray(uuid_writer, p["base_ids"])
        writer.i32(p["unknown_1"])
        writer.i32(p["base_camp_level"])
        writer.tarray(uuid_writer, p["map_object_instance_ids_base_camp_points"])
        writer.fstring(p["guild_name"])
        writer.guid(p["last_guild_name_modifier_player_uid"])
        writer.write(coerce_bytes(p["unknown_2"]))

        if "_raw_tail" in p:
            writer.write(coerce_bytes(p["_raw_tail"]))
        elif "admin_player_uid" in p:
            # V1 layout (with header bytes) takes precedence; otherwise emit
            # the flat admin/players/trailing layout used by older saves and
            # by code that constructs synthetic guild entries.
            if "_pre_v1_bytes" in p:
                writer.write(coerce_bytes(p["_pre_v1_bytes"]))
            if "_v1_header" in p:
                writer.write(coerce_bytes(p["_v1_header"]))
            writer.guid(p["admin_player_uid"])
            players = p.get("players", [])
            writer.i32(len(players))
            for pl in players:
                writer.guid(pl["player_uid"])
                writer.i64(pl["player_info"]["last_online_real_time"])
                writer.fstring(pl["player_info"]["player_name"])
                if "_u8_flag" in pl:
                    writer.byte(pl["_u8_flag"])
            if "_trailing_bytes" in p:
                writer.write(coerce_bytes(p["_trailing_bytes"]))
            elif "trailing_bytes" in p:
                # Flat-layout fallback (e.g. synthetic guild entries).
                writer.write(coerce_bytes(p["trailing_bytes"]))

        if "unknown_bytes" in p:
            writer.write(coerce_bytes(p["unknown_bytes"]))
        return writer.bytes()

    return writer.bytes()
