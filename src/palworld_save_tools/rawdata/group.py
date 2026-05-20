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
        guild: dict[str, Any] = {
            'leading_bytes': reader.byte_list(4),
            'base_ids': reader.tarray(uuid_reader),
            'unknown_1': reader.i32(),
            'base_camp_level': reader.i32(),
            'map_object_instance_ids_base_camp_points': reader.tarray(uuid_reader),
            'guild_name': reader.fstring(),
            'last_guild_name_modifier_player_uid': reader.guid(),
            'unknown_2': reader.byte_list(4)
        }
        
        remaining = reader.read_to_end()
        
        def detect_format():
            if len(remaining) < 16:
                return 'unknown'
            print(f"[GROUP_DEBUG] First 4 bytes: {remaining[:4].hex()}")
            if len(remaining) >= 4 and remaining[:4] == b'\x00\x00\x00\x00':
                return 'new'
            return 'old'
        
        format_version = detect_format()
        
        if format_version == 'old':
            guild['_opaque_players_bytes'] = remaining
            
            r = FArchiveReader(remaining, debug=False)
            guild['admin_player_uid'] = r.guid()
            
            try:
                type_name = r.fstring()
            except:
                type_name = ""
            
            try:
                count = r.i32()
                
                players = []
                for i in range(count):
                    try:
                        uid = r.guid()
                        last_online = r.i64()
                        name = r.fstring()
                        players.append({'player_uid': str(uid), 'player_info': {'last_online_real_time': last_online, 'player_name': name}})
                    except Exception as e:
                        print(f"[GROUP_DEBUG] Error reading player {i}: {e}")
                        break
                
                trailing = r.byte_list(4)
                
                guild['players'] = players
                guild['trailing_bytes'] = trailing
            except Exception as e:
                print(f"[GROUP_DEBUG] OLD parsing failed: {e}")
                players = []
                guild['players'] = players
                guild['trailing_bytes'] = []
            
            if not r.eof():
                guild['_trailing_unknown'] = r.read_to_end()
            guild['_format_version'] = 'old'
            print(f"[GROUP_DEBUG] OLD format: {guild['guild_name']} parsed {len(guild['players'])} players")
            for i, p in enumerate(guild['players']):
                print(f"[GROUP_DEBUG]   Player {i}: {p.get('player_info', {}).get('player_name', 'Unknown')} ({p.get('player_uid', 'No UID')})")
        else:
            try:
                if len(remaining) >= 4 and remaining[:4] == b'\x00\x00\x00\x00':
                    guild['unknown_guild_field'] = reader.byte_list(4)
                guild['admin_player_uid'] = reader.guid()
                guild['unknown_3'] = reader.i32()
                guild['unknown_4'] = reader.byte_list(4)
                guild['unknown_5'] = reader.u16()
                guild['unknown_6'] = reader.i32()
                raw = reader.read_to_end()
                
                players = []
                if len(raw) >= 4:
                    pr = FArchiveReader(raw, debug=False)
                    count = pr.i32()
                    for i in range(count):
                        try:
                            uid = pr.guid()
                            last_online = pr.i64()
                            name = pr.fstring()
                            try:
                                pr.byte_list(31)
                            except:
                                pass
                            players.append({'player_uid': str(uid), 'player_info': {'last_online_real_time': last_online, 'player_name': name}})
                        except Exception:
                            pass
                guild['players'] = players
                guild['_format_version'] = 'new'
                print(f"[GROUP_DEBUG] NEW format: {guild['guild_name']} parsed {len(guild['players'])} players")
            except Exception as e:
                print(f"[GROUP_DEBUG] NEW format parsing failed: {e}, falling back to OLD format")
                r = FArchiveReader(remaining, debug=False)
                guild['admin_player_uid'] = r.guid()
                remaining_after_admin = r.read_to_end()
                
                try:
                    type_name = r.fstring()
                except:
                    type_name = ""
                
                count = r.i32()
                
                players = []
                for i in range(count):
                    try:
                        uid = r.guid()
                        last_online = r.i64()
                        name = r.fstring()
                        players.append({'player_uid': str(uid), 'player_info': {'last_online_real_time': last_online, 'player_name': name}})
                    except Exception:
                        break
                
                trailing = r.byte_list(4)
                
                guild['players'] = players
                guild['trailing_bytes'] = trailing
                guild['_opaque_players_bytes'] = remaining_after_admin
                if not r.eof():
                    guild['_trailing_unknown'] = r.read_to_end()
                guild['_format_version'] = 'old'
                print(f"[GROUP_DEBUG] OLD fallback: {guild['guild_name']} parsed {len(guild['players'])} players")
        
        group_data |= guild
    
    if group_type == 'EPalGroupType::IndependentGuild':
        guild: dict[str, Any] = {'base_camp_level': reader.i32(), 'map_object_instance_ids_base_camp_points': reader.tarray(uuid_reader), 'guild_name': reader.fstring()}
        group_data |= guild
        indie = {'player_uid': reader.guid(), 'guild_name_2': reader.fstring(), 'player_info': {'last_online_real_time': reader.i64(), 'player_name': reader.fstring()}}
        group_data |= indie
    
    if not reader.eof():
        group_data['unknown_bytes'] = reader.read_to_end()
    
    return group_data

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
        was_modified = p.get('_was_modified', False)
        
        if format_version == 'old' and '_opaque_players_bytes' in p:
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
        else:
            if 'unknown_guild_field' in p:
                writer.write(bytes(p['unknown_guild_field']))
            writer.guid(p['admin_player_uid'])
            writer.i32(p.get('unknown_3', 0))
            writer.write(bytes(p.get('unknown_4', [0, 0, 1, 0])))
            writer.u16(p.get('unknown_5', 0))
            writer.i32(p.get('unknown_6', 0))
            players = p.get('players', [])
            writer.i32(len(players))
            for player in players:
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
                writer.write(bytes(31))
    
    if 'trailing_bytes' in p and p['group_type'] != 'EPalGroupType::Guild':
        writer.write(bytes(p['trailing_bytes']))
    
    encoded_bytes = writer.bytes()
    return encoded_bytes