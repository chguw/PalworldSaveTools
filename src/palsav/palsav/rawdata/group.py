from typing import Sequence, Any
from palsav.archive import *
def player_info_writer(writer: FArchiveWriter, p: dict[str, Any]) -> None:
    if 'player_uid' in p:
        writer.guid(p['player_uid'])
        writer.i64(p['player_info']['last_online_real_time'])
        writer.fstring(p['player_info']['player_name'])
        if '_u8_flag' in p:
            writer.byte(p['_u8_flag'])
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
    group_data: dict[str, Any] = {'group_type': group_type, 'group_id': reader.guid(), 'group_name': reader.fstring(), 'individual_character_handle_ids': reader.tarray(instance_id_reader)}
    if group_type in ('EPalGroupType::Guild', 'EPalGroupType::IndependentGuild', 'EPalGroupType::Organization'):
        group_data['org_type'] = reader.byte()
    if group_type == 'EPalGroupType::Organization':
        group_data['trailing_bytes'] = [int(b) for b in reader.byte_list(12)]
        if not reader.eof():
            group_data['unknown_bytes'] = [int(b) for b in reader.read_to_end()]
        return group_data
    if group_type == 'EPalGroupType::IndependentGuild':
        group_data['base_camp_level'] = reader.i32()
        group_data['map_object_instance_ids_base_camp_points'] = reader.tarray(uuid_reader)
        group_data['guild_name'] = reader.fstring()
        group_data['player_uid'] = reader.guid()
        group_data['guild_name_2'] = reader.fstring()
        group_data['player_info'] = {'last_online_real_time': reader.i64(), 'player_name': reader.fstring()}
        if not reader.eof():
            group_data['unknown_bytes'] = [int(b) for b in reader.read_to_end()]
        return group_data
    if group_type not in ('EPalGroupType::Guild', 'EPalGroupType::Organization', 'EPalGroupType::IndependentGuild'):
        import sys as _sys
        print(f'group.py: unknown group_type {group_type}', file=_sys.stderr)
    if group_type == 'EPalGroupType::Guild':
        group_data['leading_bytes'] = [int(b) for b in reader.byte_list(4)]
        group_data['base_ids'] = reader.tarray(uuid_reader)
        group_data['unknown_1'] = reader.i32()
        group_data['base_camp_level'] = reader.i32()
        group_data['map_object_instance_ids_base_camp_points'] = reader.tarray(uuid_reader)
        group_data['guild_name'] = reader.fstring()
        group_data['last_guild_name_modifier_player_uid'] = reader.guid()
        group_data['unknown_2'] = [int(b) for b in reader.byte_list(4)]
        post_unk2 = reader.read_to_end()
        V1_MARKER = b'\x02\x00\x00\x00\x02\x03\x00\x00\x00\x00'
        if post_unk2[:10] == V1_MARKER:
            group_data['_has_v1_marker'] = True
            post_unk2 = post_unk2[10:]
        try:
            sub = parent_reader.internal_copy(bytes(post_unk2), debug=False)
            admin_player_uid = sub.guid()
            player_count = sub.i32()
            players = []
            for _ in range(player_count):
                puid = sub.guid()
                lt = sub.i64()
                nm = sub.fstring()
                if not sub.eof():
                    flag = sub.byte()
                    players.append({'player_uid': str(puid), 'player_info': {'last_online_real_time': lt, 'player_name': nm}, '_u8_flag': flag})
                else:
                    players.append({'player_uid': str(puid), 'player_info': {'last_online_real_time': lt, 'player_name': nm}})
            group_data['admin_player_uid'] = admin_player_uid
            group_data['players'] = players
            trailing_bytes = sub.read_to_end()
            if trailing_bytes:
                group_data['_trailing_bytes'] = [int(b) for b in trailing_bytes]
        except Exception:
            group_data['_raw_tail'] = post_unk2
        group_data.setdefault('players', [])
    if not reader.eof():
        group_data['unknown_bytes'] = [int(b) for b in reader.read_to_end()]
    return group_data
def encode(writer: FArchiveWriter, property_type: str, properties: dict[str, Any]) -> int:
    if property_type != 'MapProperty':
        raise Exception(f'Expected MapProperty, got {property_type}')
    del properties['custom_type']
    group_map = properties['value']
    for group in group_map:
        raw_val = group['value'].get('RawData', {}).get('value')
        if not raw_val or 'values' in raw_val:
            continue
        encoded_bytes = encode_bytes(raw_val)
        group['value']['RawData']['value'] = {'values': [b for b in encoded_bytes]}
    return writer.property_inner(property_type, properties)
def encode_bytes(p: dict[str, Any]) -> bytes:
    if 'values' in p:
        return bytes(p['values'])
    writer = FArchiveWriter()
    writer.guid(p['group_id'])
    writer.fstring(p['group_name'])
    writer.tarray(instance_id_writer, p['individual_character_handle_ids'])
    if p['group_type'] in ('EPalGroupType::Guild', 'EPalGroupType::IndependentGuild', 'EPalGroupType::Organization'):
        writer.byte(p['org_type'])
    if p['group_type'] == 'EPalGroupType::Organization':
        writer.write(bytes(p['trailing_bytes']))
        if 'unknown_bytes' in p:
            writer.write(bytes(p['unknown_bytes']))
        return writer.bytes()
    if p['group_type'] == 'EPalGroupType::Guild':
        writer.write(bytes(p['leading_bytes']))
        writer.tarray(uuid_writer, p['base_ids'])
        writer.i32(p['unknown_1'])
        writer.i32(p['base_camp_level'])
        writer.tarray(uuid_writer, p['map_object_instance_ids_base_camp_points'])
        writer.fstring(p['guild_name'])
        writer.guid(p['last_guild_name_modifier_player_uid'])
        writer.write(bytes(p['unknown_2']))
        if '_raw_tail' in p:
            writer.write(bytes(p['_raw_tail']))
        elif 'admin_player_uid' in p:
            if p.get('_has_v1_marker'):
                writer.write(b'\x02\x00\x00\x00\x02\x03\x00\x00\x00\x00')
            writer.guid(p['admin_player_uid'])
            writer.tarray(player_info_writer, p.get('players', []))
            if '_trailing_bytes' in p:
                writer.write(bytes(p['_trailing_bytes']))
            elif 'trailing_bytes' in p:
                writer.write(bytes(p['trailing_bytes']))
        if 'unknown_bytes' in p:
            writer.write(bytes(p['unknown_bytes']))
        return writer.bytes()
    if p['group_type'] == 'EPalGroupType::IndependentGuild':
        writer.i32(p['base_camp_level'])
        writer.tarray(uuid_writer, p['map_object_instance_ids_base_camp_points'])
        writer.fstring(p['guild_name'])
        writer.guid(p['player_uid'])
        writer.fstring(p['guild_name_2'])
        writer.i64(p['player_info']['last_online_real_time'])
        writer.fstring(p['player_info']['player_name'])
        if 'unknown_bytes' in p:
            writer.write(bytes(p['unknown_bytes']))
        return writer.bytes()
    return writer.bytes()