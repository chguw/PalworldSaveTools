import os
from palworld_save_tools.archive import UUID
from i18n import t
from palworld_aio import constants
from palworld_aio.utils import are_equal_uuids, as_uuid, fast_deepcopy
from palworld_aio.data_manager import delete_base_camp
def move_player_to_guild(player_uid, target_guild_id):
    if not constants.current_save_path or not constants.loaded_level_json:
        return False
    wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
    group_map = wsd['GroupSaveDataMap']['value']
    base_list = wsd.get('BaseCampSaveData', {}).get('value', [])
    def nu(x):
        return str(x).replace('-', '').lower()
    player_uid_clean = nu(player_uid)
    target_gid_clean = nu(target_guild_id)
    zero = UUID.from_str('00000000-0000-0000-0000-000000000000')
    origin_group = target_group = found = None
    for g in group_map:
        try:
            if g['value']['GroupType']['value']['value'] != 'EPalGroupType::Guild':
                continue
            raw = g['value']['RawData']['value']
            if nu(g['key']) == target_gid_clean:
                target_group = g
            for p in raw.get('players', []):
                if nu(p.get('player_uid', '')) == player_uid_clean:
                    origin_group = g
                    found = p
        except:
            pass
    if not found:
        return False
    if not target_group:
        return False
    if origin_group is target_group:
        return True
    origin_raw = origin_group['value']['RawData']['value']
    newplayers = [p for p in origin_raw.get('players', []) if nu(p.get('player_uid', '')) != player_uid_clean]
    origin_raw['players'] = newplayers
    if not newplayers:
        gid = origin_group['key']
        for b in base_list[:]:
            try:
                if are_equal_uuids(b['value']['RawData']['value'].get('group_id_belong_to'), gid):
                    delete_base_camp(b, gid, constants.loaded_level_json)
            except:
                pass
        group_map.remove(origin_group)
    else:
        admin = nu(origin_raw.get('admin_player_uid', ''))
        if admin not in {nu(p['player_uid']) for p in newplayers}:
            origin_raw['admin_player_uid'] = newplayers[0]['player_uid']
    target_raw = target_group['value']['RawData']['value']
    tplayers = target_raw.get('players', [])
    if all((nu(p['player_uid']) != player_uid_clean for p in tplayers)):
        tplayers.append(found)
    target_raw['players'] = tplayers
    if nu(target_raw.get('admin_player_uid', '')) not in {nu(p['player_uid']) for p in tplayers}:
        target_raw['admin_player_uid'] = found['player_uid']
    new_gid_obj = target_raw['group_id']
    cmap = wsd['CharacterSaveParameterMap']['value']
    moved_instance_ids = []
    for character in cmap:
        try:
            raw = character['value']['RawData']['value']
            sp = raw['object']['SaveParameter']['value']
            if nu(sp.get('OwnerPlayerUId', {}).get('value')) == player_uid_clean:
                inst = character['key']['InstanceId']['value']
                moved_instance_ids.append(inst)
                raw['group_id'] = new_gid_obj
                sp['OwnerPlayerUId']['value'] = found['player_uid']
                try:
                    if 'MapObjectConcreteInstanceIdAssignedToExpedition' in sp:
                        del sp['MapObjectConcreteInstanceIdAssignedToExpedition']
                except:
                    pass
        except:
            pass
    if origin_group:
        try:
            origin_raw = origin_group['value']['RawData']['value']
            origin_handles = origin_raw.get('individual_character_handle_ids', [])
            if isinstance(origin_handles, list):
                origin_handles[:] = [h for h in origin_handles if str(h.get('instance_id', '')) not in moved_instance_ids]
                seen = {}
                unique_handles = []
                for h in origin_handles:
                    try:
                        inst = str(h['instance_id'])
                        if inst not in seen:
                            seen[inst] = True
                            unique_handles.append(h)
                    except:
                        unique_handles.append(h)
                origin_handles[:] = unique_handles
        except:
            pass
    for entry in group_map:
        try:
            raw = entry['value']['RawData']['value']
            if raw.get('group_id') != new_gid_obj:
                continue
            handles = raw.get('individual_character_handle_ids')
            if not isinstance(handles, list):
                handles = []
                raw['individual_character_handle_ids'] = handles
            seen = {}
            unique_handles = []
            for h in handles:
                try:
                    inst = str(h['instance_id'])
                    if inst not in seen:
                        seen[inst] = True
                        unique_handles.append(h)
                except:
                    unique_handles.append(h)
            handles[:] = unique_handles
            existing = set(seen.keys())
            for inst in moved_instance_ids:
                inst_str = str(inst)
                if inst_str not in existing:
                    handles.append({'guid': zero, 'instance_id': inst})
                    existing.add(inst_str)
            break
        except:
            pass
    return True
def rebuild_all_players_pals():
    if not constants.loaded_level_json or not constants.current_save_path:
        return False
    try:
        wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
        cmap = wsd['CharacterSaveParameterMap']['value']
        containers = wsd['CharacterContainerSaveData']['value']
        gmap = wsd['GroupSaveDataMap']['value']
        mapobjs = wsd.get('MapObjectSaveData', {}).get('value', {}).get('values', [])
    except:
        return False
    zero = UUID.from_str('00000000-0000-0000-0000-000000000000')
    used_ids = {str(ch['key']['InstanceId']['value']) for ch in cmap if 'key' in ch}
    def bump_guid_str(s):
        v = str(s).lower()
        t = str.maketrans('0123456789abcdef', '123456789abcdef0')
        bumped = v.translate(t)
        while bumped in used_ids:
            bumped = bumped.translate(t)
        used_ids.add(bumped)
        return bumped
    players_folder = os.path.join(constants.current_save_path, 'Players')
    if not os.path.isdir(players_folder):
        return False
    def nu(x):
        return str(x).replace('-', '').lower()
    real_players = {p.get('player_uid') for g in gmap for p in g.get('value', {}).get('RawData', {}).get('value', {}).get('players', []) if p.get('player_uid')}
    id_map = {}
    new_params = []
    for ch in cmap:
        try:
            raw = ch['value']['RawData']['value']
            sp = raw['object']['SaveParameter']['value']
            owner = sp['OwnerPlayerUId']['value']
            if owner not in real_players:
                continue
        except:
            continue
        cp = fast_deepcopy(ch)
        old_inst = cp['key']['InstanceId']['value']
        new_inst = UUID.from_str(bump_guid_str(old_inst))
        id_map[str(old_inst)] = new_inst
        cp['key']['InstanceId']['value'] = new_inst
        raw2 = cp['value']['RawData']['value']
        sp2 = raw2['object']['SaveParameter']['value']
        sp2['OwnerPlayerUId']['value'] = owner
        gid = next((g['value']['RawData']['value'].get('group_id') for g in gmap if nu(owner) in {nu(p['player_uid']) for p in g['value']['RawData']['value'].get('players', [])}), zero)
        raw2['group_id'] = gid
        try:
            del sp2['MapObjectConcreteInstanceIdAssignedToExpedition']
        except:
            pass
        new_params.append(cp)
    for c in containers:
        try:
            for s in c['value']['Slots']['value']['values']:
                inst = s.get('RawData', {}).get('value', {}).get('instance_id')
                if inst and str(inst) in id_map:
                    s['RawData']['value']['instance_id'] = id_map[str(inst)]
        except:
            pass
    for m in mapobjs:
        try:
            aid = m['Model']['value']['RawData']['value'].get('assigned_individual_character_handle_id')
            if aid and str(aid['instance_id']) in id_map:
                aid['instance_id'] = id_map[str(aid['instance_id'])]
        except:
            pass
    for g in gmap:
        try:
            raw = g['value']['RawData']['value']
            for h in raw.get('worker_character_handle_ids', []):
                if str(h['instance_id']) in id_map:
                    h['instance_id'] = id_map[str(h['instance_id'])]
            handles = raw.get('individual_character_handle_ids', [])
            if not isinstance(handles, list):
                handles = []
                raw['individual_character_handle_ids'] = handles
            handles[:] = [h for h in handles if str(h.get('instance_id', '')) not in id_map]
            seen = {}
            unique_handles = []
            for h in handles:
                try:
                    inst = str(h['instance_id'])
                    if inst not in seen:
                        seen[inst] = True
                        unique_handles.append(h)
                except:
                    unique_handles.append(h)
            handles[:] = unique_handles
            for old_id, new_id in id_map.items():
                handles.append({'guid': zero, 'instance_id': new_id})
        except:
            pass
    final_cmap = []
    for ch in cmap:
        try:
            raw = ch['value']['RawData']['value']
            sp = raw['object']['SaveParameter']['value']
            if sp['OwnerPlayerUId']['value'] in real_players:
                continue
        except:
            pass
        final_cmap.append(ch)
    final_cmap.extend(new_params)
    wsd['CharacterSaveParameterMap']['value'] = final_cmap
    return True
def rebuild_all_guilds():
    if not constants.current_save_path or not constants.loaded_level_json:
        return False
    wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
    def nu(x):
        return str(x).replace('-', '').lower()
    zero = UUID.from_str('00000000-0000-0000-0000-000000000000')
    group_map = wsd['GroupSaveDataMap']['value']
    cmap = wsd['CharacterSaveParameterMap']['value']
    guilds = {}
    base_pals_by_gid = {}
    for ch in cmap:
        try:
            rawf = ch['value']['RawData']['value']
            raw = rawf.get('object', {}).get('SaveParameter', {}).get('value', {})
            owner = raw.get('OwnerPlayerUId', {}).get('value')
            if not owner:
                gid = rawf.get('group_id')
                if gid:
                    gid_str = nu(gid)
                    if gid_str not in base_pals_by_gid:
                        base_pals_by_gid[gid_str] = []
                    base_pals_by_gid[gid_str].append(ch)
        except:
            pass
    for g in group_map:
        try:
            if g['value']['GroupType']['value']['value'] == 'EPalGroupType::Guild':
                gid = g['key']
                raw = g['value']['RawData']['value']
                players = raw.get('players', [])
                guilds[nu(gid)] = {'gid': gid, 'group': g, 'players': players, 'handles': raw.get('individual_character_handle_ids', [])}
        except:
            pass
    for ginfo in guilds.values():
        g_gid = ginfo['gid']
        players_clean = {nu(p['player_uid']) for p in ginfo['players']}
        pals = []
        for ch in cmap:
            try:
                rawf = ch['value']['RawData']['value']
                raw = rawf.get('object', {}).get('SaveParameter', {}).get('value', {})
                owner = raw.get('OwnerPlayerUId', {}).get('value')
                if owner and nu(owner) in players_clean:
                    pals.append(ch)
                    continue
            except:
                pass
        gid_str = nu(g_gid)
        if gid_str in base_pals_by_gid:
            pals.extend(base_pals_by_gid[gid_str])
        ginfo['pals'] = pals
    for ginfo in guilds.values():
        gid = ginfo['gid']
        handles = ginfo['handles']
        seen = {}
        unique_handles = []
        for h in handles:
            try:
                inst = nu(h['instance_id'])
                if inst not in seen:
                    seen[inst] = True
                    unique_handles.append(h)
            except:
                unique_handles.append(h)
        handles[:] = unique_handles
        existing = set(seen.keys())
        for ch in ginfo['pals']:
            try:
                inst = ch['key']['InstanceId']['value']
                inst_clean = nu(inst)
                rawf = ch['value']['RawData']['value']
                rawf['group_id'] = gid
                sp = rawf['object']['SaveParameter']['value']
                try:
                    if 'MapObjectConcreteInstanceIdAssignedToExpedition' in sp:
                        del sp['MapObjectConcreteInstanceIdAssignedToExpedition']
                except:
                    pass
                if inst_clean not in existing:
                    handles.append({'guid': zero, 'instance_id': inst})
                    existing.add(inst_clean)
            except:
                pass
    duplicates = debug_check_duplicate_handles()
    if duplicates:
        print(f'DUPLICATE HANDLES DETECTED: {duplicates}')
    return True
def make_member_leader(guild_id, player_uid):
    if not constants.loaded_level_json:
        return False
    wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
    group_data_list = wsd['GroupSaveDataMap']['value']
    for g in group_data_list:
        if are_equal_uuids(g['key'], guild_id):
            raw = g['value']['RawData']['value']
            raw['admin_player_uid'] = player_uid
            return True
    return False
def rename_guild(guild_id, new_name):
    if not constants.loaded_level_json:
        return False
    wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
    for g in wsd['GroupSaveDataMap']['value']:
        if are_equal_uuids(g['key'], guild_id):
            g['value']['RawData']['value']['guild_name'] = new_name
            gid_str = str(guild_id)
            for base_id, lookup_data in constants.base_guild_lookup.items():
                if lookup_data.get('GuildID') == gid_str:
                    constants.base_guild_lookup[base_id]['GuildName'] = new_name
            return True
    return False
def set_guild_level(guild_id, level):
    if not constants.loaded_level_json:
        return False
    level = max(1, min(30, level))
    wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
    for g in wsd['GroupSaveDataMap']['value']:
        if are_equal_uuids(g['key'], guild_id):
            g['value']['RawData']['value']['base_camp_level'] = level
            return True
    return False
def debug_check_duplicate_handles():
    if not constants.loaded_level_json:
        return None
    wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
    group_map = wsd['GroupSaveDataMap']['value']
    def nu(x):
        return str(x).replace('-', '').lower()
    all_handles = {}
    duplicates = {}
    for g in group_map:
        try:
            if g['value']['GroupType']['value']['value'] != 'EPalGroupType::Guild':
                continue
            gid = str(g['key'])
            handles = g['value']['RawData']['value'].get('individual_character_handle_ids', [])
            for h in handles:
                inst = str(h['instance_id'])
                key = nu(inst)
                if key in all_handles:
                    if key not in duplicates:
                        duplicates[key] = [all_handles[key]]
                    duplicates[key].append(gid)
                else:
                    all_handles[key] = gid
        except:
            pass
    return duplicates if duplicates else None
def level_up_guild_member(guild_id, player_uid):
    from .player_manager import adjust_player_level, get_level_from_exp
    if not is_player_in_guild(guild_id, player_uid):
        return False
    current_level = constants.player_levels.get(str(player_uid).replace('-', ''), 1)
    return adjust_player_level(player_uid, current_level + 1)
def level_down_guild_member(guild_id, player_uid):
    from .player_manager import adjust_player_level, get_level_from_exp
    if not is_player_in_guild(guild_id, player_uid):
        return False
    current_level = constants.player_levels.get(str(player_uid).replace('-', ''), 1)
    return adjust_player_level(player_uid, current_level - 1)
def set_guild_member_level(guild_id, player_uid, target_level):
    from .player_manager import adjust_player_level, get_level_from_exp
    if not is_player_in_guild(guild_id, player_uid):
        return False
    return adjust_player_level(player_uid, target_level)
def is_player_in_guild(guild_id, player_uid):
    if not constants.loaded_level_json:
        return False
    uid_clean = str(player_uid).replace('-', '').lower()
    gid_clean = str(guild_id).replace('-', '').lower()
    wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
    for g in wsd['GroupSaveDataMap']['value']:
        if g['value']['GroupType']['value']['value'] != 'EPalGroupType::Guild':
            continue
        if str(g['key']).replace('-', '').lower() == gid_clean:
            for p in g['value']['RawData']['value'].get('players', []):
                if str(p.get('player_uid', '')).replace('-', '').lower() == uid_clean:
                    return True
    return False