from typing import Sequence, Any
import uuid as _stdlib_uuid
from palworld_save_tools.archive import *
def player_info_reader(reader: FArchiveReader) -> dict[str, Any]:
    return {'player_uid': reader.guid(), 'player_info': {'last_online_real_time': reader.i64(), 'player_name': reader.fstring()}}
def player_info_writer(writer: FArchiveWriter, p: dict[str, Any]) -> None:
    writer.guid(p['player_uid'])
    writer.i64(p['player_info']['last_online_real_time'])
    writer.fstring(p['player_info']['player_name'])
def decode(reader: FArchiveReader, type_name: str, size: int, path: str) -> dict[str, Any]:
    if type_name != 'MapProperty':
        raise Exception(f'Expected MapProperty, got {type_name}')
    value = reader.property(type_name, size, path, nested_caller_path=path)
    group_map = value['value']
    for group in group_map:
        group_type = group['value']['GroupType']['value']['value']
        group_bytes = group['value']['RawData']['value']['values']
        group['value']['RawData']['value'] = decode_bytes(reader, group_bytes, group_type)
    return value
def decode_bytes(parent_reader: FArchiveReader, group_bytes: Sequence[int], group_type: str) -> dict[str, Any]:
    reader = parent_reader.internal_copy(bytes(group_bytes), debug=False)
    group_data = {'group_type': group_type, 'group_id': reader.guid(), 'group_name': reader.fstring(), 'individual_character_handle_ids': reader.tarray(instance_id_reader)}
    if group_type in ['EPalGroupType::Guild', 'EPalGroupType::IndependentGuild', 'EPalGroupType::Organization']:
        group_data |= {'org_type': reader.byte()}
    if group_type == 'EPalGroupType::Organization':
        group_data |= {'trailing_bytes': reader.byte_list(12)}
    if group_type == 'EPalGroupType::Guild':
        guild: dict[str, Any] = {'leading_bytes': reader.byte_list(4), 'base_ids': reader.tarray(uuid_reader), 'unknown_1': reader.i32(), 'base_camp_level': reader.i32(), 'map_object_instance_ids_base_camp_points': reader.tarray(uuid_reader), 'guild_name': reader.fstring(), 'last_guild_name_modifier_player_uid': reader.guid(), 'unknown_2': reader.byte_list(4)}
        remaining = reader.read_to_end()
        guild['_opaque_all_remaining_bytes'] = remaining
        try:
            new_r = FArchiveReader(remaining, debug=False)
            if len(remaining) >= 4 and remaining[:4] == b'\x00\x00\x00\x00':
                guild['unknown_guild_field'] = new_r.byte_list(4)
            guild['admin_player_uid'] = new_r.guid()
            guild['unknown_3'] = new_r.i32()
            guild['unknown_4'] = new_r.byte_list(4)
            guild['unknown_5'] = new_r.u16()
            guild['unknown_6'] = new_r.i32()
            guild['unknown_7'] = new_r.i32()
            guild['unknown_8'] = new_r.i32()
            guild['unknown_9'] = new_r.i32()
            raw = new_r.read_to_end()
            guild['_opaque_raw'] = raw
            nplayers = []
            if len(raw) >= 4:
                pr = FArchiveReader(raw, debug=False)
                count = pr.i32()
                if 0 <= count <= 1000:
                    for _ in range(count):
                        try:
                            lo = pr.i64()
                            nm = pr.fstring()
                            pr.byte_list(31)
                            if _is_valid_player_name(nm):
                                nplayers.append({'player_uid': '', 'player_info': {'last_online_real_time': lo, 'player_name': nm}})
                            else:
                                break
                        except Exception:
                            break
            if nplayers:
                guild['players'] = nplayers
                guild['_format_version'] = 'new'
        except Exception:
            pass
        if '_format_version' not in guild or guild.get('players', []) == []:
            try:
                old_r = FArchiveReader(remaining, debug=False)
                guild['_opaque_players_bytes'] = remaining
                if len(remaining) >= 4 and remaining[:4] == b'\x00\x00\x00\x00':
                    guild['unknown_guild_field'] = old_r.byte_list(4)
                guild['admin_player_uid'] = old_r.guid()
                nplayers = []
                count = old_r.u32()
                if 0 <= count <= 1000:
                    for _ in range(count):
                        try:
                            uid = old_r.guid()
                            lo = old_r.i64()
                            nm = old_r.fstring()
                            nplayers.append({'player_uid': str(uid), 'player_info': {'last_online_real_time': lo, 'player_name': nm}})
                        except Exception:
                            break
                if nplayers:
                    guild['players'] = nplayers
                    guild['trailing_bytes'] = [int(b) for b in old_r.read_to_end()]
                    guild['_format_version'] = 'old'
            except Exception:
                pass
        if '_format_version' not in guild and len(remaining) >= 100:
            try:
                scan_r = FArchiveReader(remaining, debug=False)
                if len(remaining) >= 4 and remaining[:4] == b'\x00\x00\x00\x00':
                    scan_r.byte_list(4)
                scan_admin = scan_r.guid()
                guild['admin_player_uid'] = str(scan_admin)
                scan_r = FArchiveReader(remaining, debug=False)
                nplayers = _scan_players_from_raw(remaining)
                if nplayers:
                    guild['players'] = nplayers
                    guild['_opaque_all_remaining_for_encode'] = remaining
                    guild['_format_version'] = 'new'
            except Exception:
                pass
        if '_format_version' not in guild:
            guild['players'] = []
            guild['trailing_bytes'] = []
            guild['_format_version'] = 'opaque_full'
        
        group_data |= guild
    if group_type == 'EPalGroupType::IndependentGuild':
        guild: dict[str, Any] = {'base_camp_level': reader.i32(), 'map_object_instance_ids_base_camp_points': reader.tarray(uuid_reader), 'guild_name': reader.fstring()}
        group_data |= guild
        indie = {'player_uid': reader.guid(), 'guild_name_2': reader.fstring(), 'player_info': {'last_online_real_time': reader.i64(), 'player_name': reader.fstring()}}
        group_data |= indie
    if not reader.eof():
        group_data['unknown_bytes'] = reader.read_to_end()
    return group_data
def _scan_players_from_raw(data: bytes) -> list[dict[str, Any]]:
    players = []
    idx = 0
    while idx < len(data) - 16:
        marker = data.find(b'\x01\x00\x00\x00', idx)
        if marker < 0:
            break
        if marker + 16 > len(data):
            break
        try:
            pr = FArchiveReader(data[marker + 4:], debug=False)
            lo = pr.i64()
            nm = pr.fstring()
            if _is_valid_player_name(nm):
                players.append({'player_uid': '', 'player_info': {'last_online_real_time': lo, 'player_name': nm}})
                rest = pr.read_to_end()
                more = _scan_more_players(rest)
                players.extend(more)
                break
        except Exception:
            pass
        idx = marker + 4
    if not players:
        brute_off = 0
        while brute_off < len(data) - 12:
            try:
                pr = FArchiveReader(data[brute_off:], debug=False)
                lo = pr.i64()
                nm = pr.fstring()
                if _is_valid_player_name(nm):
                    players.append({'player_uid': '', 'player_info': {'last_online_real_time': lo, 'player_name': nm}})
                    brute_off += len(data[brute_off:]) - len(pr.read_to_end())
                else:
                    brute_off += 1
            except Exception:
                brute_off += 1
    return players
def _scan_more_players(data: bytes) -> list[dict[str, Any]]:
    players = []
    start = 1 if len(data) > 0 and data[0] == 1 else 0
    pos = start
    while pos < len(data) - 12:
        try:
            pr = FArchiveReader(data[pos:], debug=False)
            uid = pr.guid()
            lo = pr.i64()
            nm = pr.fstring()
            if _is_valid_player_name(nm):
                players.append({'player_uid': str(uid), 'player_info': {'last_online_real_time': lo, 'player_name': nm}})
                consumed = len(data[pos:]) - len(pr.read_to_end())
                pos += consumed
                continue
        except Exception:
            pass
        try:
            pr = FArchiveReader(data[pos:], debug=False)
            lo = pr.i64()
            nm = pr.fstring()
            if _is_valid_player_name(nm):
                players.append({'player_uid': '', 'player_info': {'last_online_real_time': lo, 'player_name': nm}})
                consumed = len(data[pos:]) - len(pr.read_to_end())
                pos += consumed
                continue
        except Exception:
            pass
        pos += 1
    return players
def _is_valid_player_name(name: str) -> bool:
    if not name or len(name) < 1 or len(name) > 50:
        return False
    stripped = name.rstrip('\x00')
    if not stripped or len(stripped) < 1:
        return False
    has_printable = any((c.isalnum() or c in ' _-.:' for c in stripped))
    if not has_printable:
        return False
    if any((c in '\x00\x01\x02\x03\x04\x05\x06\x07\x08\x0b\x0c\x0e\x0f' for c in stripped)):
        return False
    try:
        stripped.encode('utf-8')
        return True
    except Exception:
        return False
def encode(writer: FArchiveWriter, property_type: str, properties: dict[str, Any]) -> int:
    if property_type != 'MapProperty':
        raise Exception(f'Expected MapProperty, got {property_type}')
    del properties['custom_type']
    group_map = properties['value']
    for group in group_map:
        if 'values' in group['value']['RawData']['value']:
            continue
        p = group['value']['RawData']['value']
        encoded_bytes = encode_bytes(p)
        group['value']['RawData']['value'] = {'values': [b for b in encoded_bytes]}
    return writer.property_inner(property_type, properties)
def encode_bytes(p: dict[str, Any]) -> bytes:
    writer = FArchiveWriter()
    writer.guid(p['group_id'])
    writer.fstring(p['group_name'])
    writer.tarray(instance_id_writer, p['individual_character_handle_ids'])
    if p['group_type'] in ['EPalGroupType::Guild', 'EPalGroupType::IndependentGuild', 'EPalGroupType::Organization']:
        writer.byte(p['org_type'])
    if p['group_type'] == 'EPalGroupType::Organization':
        writer.write(bytes(p['trailing_bytes']))
    if p['group_type'] == 'EPalGroupType::IndependentGuild':
        writer.guid(p['player_uid'])
        writer.fstring(p['guild_name_2'])
        writer.i64(p['player_info']['last_online_real_time'])
        writer.fstring(p['player_info']['player_name'])
    if p['group_type'] == 'EPalGroupType::Guild':
        writer.write(bytes(p['leading_bytes']))
        writer.tarray(uuid_writer, p['base_ids'])
        writer.i32(p['unknown_1'])
        writer.i32(p['base_camp_level'])
        writer.tarray(uuid_writer, p['map_object_instance_ids_base_camp_points'])
        writer.fstring(p['guild_name'])
        writer.guid(p['last_guild_name_modifier_player_uid'])
        writer.write(bytes(p['unknown_2']))
        format_version = p.get('_format_version', 'new')
        if format_version == 'opaque_full' and '_opaque_all_remaining_bytes' in p:
            writer.write(bytes(p['_opaque_all_remaining_bytes']))
        elif format_version == 'old' and '_opaque_players_bytes' in p:
            writer.write(bytes(p['_opaque_players_bytes']))
            if '_trailing_unknown' in p:
                writer.write(bytes(p['_trailing_unknown']))
        elif format_version == 'old':
            writer.guid(p['admin_player_uid'])
            writer.i32(len(p['players']))
            for player in p['players']:
                uid = player.get('player_uid', '')
                if isinstance(uid, str) and uid:
                    uid = _stdlib_uuid.UUID(uid)
                elif isinstance(uid, _stdlib_uuid.UUID):
                    pass
                else:
                    uid = _stdlib_uuid.UUID('00000000-0000-0000-0000-000000000000')
                writer.guid(uid)
                writer.i64(player['player_info']['last_online_real_time'])
                writer.fstring(player['player_info']['player_name'])
            if 'trailing_bytes' in p:
                writer.write(bytes(p['trailing_bytes']))
            if '_trailing_unknown' in p:
                writer.write(bytes(p['_trailing_unknown']))
        elif '_opaque_all_remaining_for_encode' in p:
            writer.write(bytes(p['_opaque_all_remaining_for_encode']))
        else:
            if 'unknown_guild_field' in p:
                writer.write(bytes(p['unknown_guild_field']))
            writer.guid(p['admin_player_uid'])
            writer.i32(p.get('unknown_3', 0))
            writer.write(bytes(p.get('unknown_4', [0, 1, 0, 0])))
            writer.u16(p.get('unknown_5', 0))
            writer.i32(p.get('unknown_6', 0))
            writer.i32(p.get('unknown_7', 0))
            writer.i32(p.get('unknown_8', 0))
            writer.i32(p.get('unknown_9', 0))
            if '_opaque_raw' in p:
                writer.write(bytes(p['_opaque_raw']))
            else:
                players = p.get('players', [])
                writer.i32(len(players))
                for player in players:
                    writer.i64(player['player_info']['last_online_real_time'])
                    writer.fstring(player['player_info']['player_name'])
                    writer.write(bytes(31))
    if 'trailing_bytes' in p and p['group_type'] != 'EPalGroupType::Guild':
        writer.write(bytes(p['trailing_bytes']))
    encoded_bytes = writer.bytes()
    return encoded_bytes