import os
from palsav import json_tools
from PySide6.QtWidgets import QApplication, QMessageBox
from i18n import t
from palworld_aio import constants
from resource_resolver import resource_path
from palworld_aio.utils import are_equal_uuids, as_uuid, sav_to_gvasfile, gvasfile_to_sav
from palworld_aio.managers.data_manager import delete_player
from palsav.core import compress_gvas_to_sav
from palobject import SKP_PALWORLD_CUSTOM_PROPERTIES
def _load_exp_data():
    base_dir = constants.get_base_path()
    exp_file = resource_path(base_dir, 'game_data', 'pal_exp_table.json')
    try:
        return json_tools.load(exp_file)
    except Exception as e:
        print(f'Error loading EXP_DATA from {exp_file}: {e}')
        return {}
EXP_DATA = _load_exp_data()
def rename_player(player_uid, new_name):
    if not constants.loaded_level_json:
        return False
    p_uid_clean = str(player_uid).replace('-', '')
    wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
    for g in wsd['GroupSaveDataMap']['value']:
        raw = g['value']['RawData']['value']
        found = False
        for p in raw.get('players', []):
            uid = str(p.get('player_uid', '')).replace('-', '')
            if uid == p_uid_clean:
                p.setdefault('player_info', {})['player_name'] = new_name
                found = True
                break
        if found:
            break
    char_map = wsd.get('CharacterSaveParameterMap', {}).get('value', [])
    for entry in char_map:
        raw = entry.get('value', {}).get('RawData', {}).get('value', {})
        sp = raw.get('object', {}).get('SaveParameter', {})
        if sp.get('struct_type') != 'PalIndividualCharacterSaveParameter':
            continue
        sp_val = sp.get('value', {})
        if not sp_val.get('IsPlayer', {}).get('value'):
            continue
        uid_obj = entry.get('key', {}).get('PlayerUId', {})
        uid = str(uid_obj.get('value', '')).replace('-', '') if isinstance(uid_obj, dict) else ''
        if uid == p_uid_clean:
            sp_val.setdefault('NickName', {})['value'] = new_name
            break
    return True
def get_player_info(player_uid):
    if not constants.loaded_level_json:
        return None
    uid_clean = str(player_uid).replace('-', '').lower()
    wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
    tick = wsd['GameTimeSaveData']['value']['RealDateTimeTicks']['value']
    for g in wsd['GroupSaveDataMap']['value']:
        if g['value']['GroupType']['value']['value'] != 'EPalGroupType::Guild':
            continue
        gid = str(g['key'])
        gname = g['value']['RawData']['value'].get('guild_name', 'Unknown Guild')
        for p in g['value']['RawData']['value'].get('players', []):
            uid = str(p.get('player_uid', '')).replace('-', '').lower()
            if uid == uid_clean:
                name = p.get('player_info', {}).get('player_name', 'Unknown')
                last = p.get('player_info', {}).get('last_online_real_time')
                from ..utils import format_duration_short
                lastseen = 'Unknown' if last is None else format_duration_short((tick - last) / 10000000.0)
                level = constants.player_levels.get(uid, '?')
                pals = constants.PLAYER_PAL_COUNTS.get(uid, 0)
                return {'uid': player_uid, 'name': name, 'level': level, 'pals': pals, 'lastseen': lastseen, 'guild_id': gid, 'guild_name': gname}
    return None
def get_player_pal_count(player_uid):
    uid = str(player_uid).replace('-', '').lower()
    return constants.PLAYER_PAL_COUNTS.get(uid, 0)
def unlock_viewing_cage(player_uid):
    if not constants.current_save_path:
        return False
    uid_clean = str(player_uid).replace('-', '').upper()
    sav_file = os.path.join(constants.current_save_path, 'Players', f'{uid_clean}.sav')
    if not os.path.exists(sav_file):
        return False
    try:
        gvas = sav_to_gvasfile(sav_file)
        save_data = gvas.properties.get('SaveData', {}).get('value', {})
        if 'bIsViewingCageCanUse' not in save_data:
            return False
        if save_data['bIsViewingCageCanUse']['value']:
            return True
        save_data['bIsViewingCageCanUse']['value'] = True
        gvasfile_to_sav(gvas, sav_file)
        return True
    except Exception as e:
        print(f'Error unlocking viewing cage: {e}')
        return False
def get_level_from_exp(exp):
    for level in range(80, 0, -1):
        if exp >= EXP_DATA[str(level)]['TotalEXP']:
            return level
    return 1
def set_player_level(player_uid, new_level):
    if not constants.loaded_level_json:
        return False
    if new_level < 1 or new_level > 80:
        return False
    uid_clean = str(player_uid).replace('-', '')
    wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
    char_map = wsd.get('CharacterSaveParameterMap', {}).get('value', [])
    for entry in char_map:
        raw = entry.get('value', {}).get('RawData', {}).get('value', {})
        sp = raw.get('object', {}).get('SaveParameter', {})
        if sp.get('struct_type') != 'PalIndividualCharacterSaveParameter':
            continue
        sp_val = sp.get('value', {})
        if not sp_val.get('IsPlayer', {}).get('value'):
            continue
        uid_obj = entry.get('key', {}).get('PlayerUId', {})
        uid = str(uid_obj.get('value', '')).replace('-', '') if isinstance(uid_obj, dict) else ''
        if uid == uid_clean:
            if 'Level' not in sp_val:
                sp_val['Level'] = {}
            if 'value' not in sp_val['Level']:
                sp_val['Level']['value'] = {}
            sp_val['Level']['value']['value'] = new_level
            if 'Exp' not in sp_val:
                sp_val['Exp'] = {'value': EXP_DATA[str(new_level)]['TotalEXP']}
            else:
                sp_val['Exp']['value'] = EXP_DATA[str(new_level)]['TotalEXP']
            constants.player_levels[uid] = new_level
            return True
    return False
def set_player_tech_points(player_uid, new_tech_points):
    if not constants.current_save_path:
        return False
    uid_clean = str(player_uid).replace('-', '').upper()
    sav_file = os.path.join(constants.current_save_path, 'Players', f'{uid_clean}.sav')
    if not os.path.exists(sav_file):
        return False
    try:
        from palworld_aio.utils import sav_to_gvasfile, gvasfile_to_sav
        gvas = sav_to_gvasfile(sav_file)
        save_data = gvas.properties.get('SaveData', {}).get('value', {})
        if 'TechnologyPoint' not in save_data:
            save_data['TechnologyPoint'] = {'id': None, 'value': 0, 'type': 'IntProperty'}
        save_data['TechnologyPoint']['value'] = new_tech_points
        if 'bossTechnologyPoint' not in save_data:
            save_data['bossTechnologyPoint'] = {'id': None, 'value': 0, 'type': 'IntProperty'}
        save_data['bossTechnologyPoint']['value'] = new_tech_points
        gvasfile_to_sav(gvas, sav_file)
        return True
    except Exception as e:
        print(f'Error setting tech points: {e}')
        return False
def set_player_boss_tech_points(player_uid, new_boss_tech_points):
    if not constants.current_save_path:
        return False
    uid_clean = str(player_uid).replace('-', '').upper()
    sav_file = os.path.join(constants.current_save_path, 'Players', f'{uid_clean}.sav')
    if not os.path.exists(sav_file):
        return False
    try:
        from palworld_aio.utils import sav_to_gvasfile, gvasfile_to_sav
        gvas = sav_to_gvasfile(sav_file)
        save_data = gvas.properties.get('SaveData', {}).get('value', {})
        if 'bossTechnologyPoint' not in save_data:
            save_data['bossTechnologyPoint'] = {'id': None, 'value': 0, 'type': 'IntProperty'}
        save_data['bossTechnologyPoint']['value'] = new_boss_tech_points
        gvasfile_to_sav(gvas, sav_file)
        return True
    except Exception as e:
        print(f'Error setting boss tech points: {e}')
        return False
def set_player_stats(player_uid, stat_changes, unused_stat_points=None):
    if not constants.loaded_level_json:
        return False
    uid_clean = str(player_uid).replace('-', '')
    wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
    char_map = wsd.get('CharacterSaveParameterMap', {}).get('value', [])
    for entry in char_map:
        raw = entry.get('value', {}).get('RawData', {}).get('value', {})
        sp = raw.get('object', {}).get('SaveParameter', {})
        if sp.get('struct_type') != 'PalIndividualCharacterSaveParameter':
            continue
        sp_val = sp.get('value', {})
        if not sp_val.get('IsPlayer', {}).get('value'):
            continue
        uid_obj = entry.get('key', {}).get('PlayerUId', {})
        uid = str(uid_obj.get('value', '')).replace('-', '') if isinstance(uid_obj, dict) else ''
        if uid == uid_clean:
            if 'GotStatusPointList' in sp_val:
                got_status_list = sp_val['GotStatusPointList']['value']['values']
                for status_item in got_status_list:
                    if 'StatusName' in status_item and 'StatusPoint' in status_item:
                        if isinstance(status_item['StatusPoint'], dict):
                            if 'value' in status_item['StatusPoint']:
                                if isinstance(status_item['StatusName'], dict) and 'value' in status_item['StatusName']:
                                    stat_name = status_item['StatusName']['value']
                                    if stat_name in stat_changes:
                                        status_item['StatusPoint']['value'] = stat_changes[stat_name]
            if 'GotExStatusPointList' in sp_val:
                got_ex_status_list = sp_val['GotExStatusPointList']['value']['values']
                for status_item in got_ex_status_list:
                    if 'StatusName' in status_item and 'StatusPoint' in status_item:
                        if isinstance(status_item['StatusPoint'], dict):
                            if 'value' in status_item['StatusPoint']:
                                if isinstance(status_item['StatusName'], dict) and 'value' in status_item['StatusName']:
                                    stat_name = status_item['StatusName']['value']
                                    if stat_name in stat_changes:
                                        status_item['StatusPoint']['value'] = stat_changes[stat_name]
            if 'UnusedStatusPoint' in sp_val:
                if isinstance(sp_val['UnusedStatusPoint'], dict) and 'value' in sp_val['UnusedStatusPoint']:
                    if unused_stat_points is not None:
                        sp_val['UnusedStatusPoint']['value'] = unused_stat_points
                    else:
                        sp_val['UnusedStatusPoint']['value'] = 0
            return True
    return False
EFFIGY_ITEM_IDS = ['Relic_01', 'Relic_02', 'Relic_03', 'Relic_04', 'Relic_05', 'Relic_06', 'Relic_07', 'Relic_08', 'Relic_09', 'Relic_10', 'Relic_11', 'Relic_12', 'Relic']
def _load_relic_data():
    relic_path = resource_path(constants.get_base_path(), 'game_data', 'relic_data.json')
    try:
        data = json_tools.load(relic_path)
        cumax = {k: v['cumulative_max'] for k, v in data.items()}
        maxrank = {k: v['max_rank'] for k, v in data.items()}
        return (cumax, maxrank)
    except Exception:
        return ({}, {})
RELIC_CUMULATIVE_MAX, RELIC_MAX_RANK = _load_relic_data()
RELIC_TO_STATUS_NAME = {'EPalRelicType::CapturePower': '捕獲率', 'EPalRelicType::HungerReduction': '空腹率低減', 'EPalRelicType::SwimSpeed': '泳ぎ速度', 'EPalRelicType::FoodDecayReduction': '食料腐敗低減', 'EPalRelicType::JumpPower': 'ジャンプ力', 'EPalRelicType::GliderSpeed': '滑空速度', 'EPalRelicType::ClimbSpeed': '崖登り速度', 'EPalRelicType::StatusAilmentResist': '状態異常耐性', 'EPalRelicType::ExpBonus': '経験値ボーナス', 'EPalRelicType::RainbowPassiveRate': '虹パッシブ率', 'EPalRelicType::MoveSpeed': '移動速度アップ', 'EPalRelicType::SphereHoming': 'パルスフィアホーミング', 'EPalRelicType::StaminaReduction': 'スタミナ消費軽減'}
def add_all_effigies_to_players(player_uids, quantity=999):
    if not constants.loaded_level_json:
        return 0
    if not constants.current_save_path:
        return 0
    from palworld_aio.utils import sav_to_gvasfile, gvasfile_to_sav
    from palworld_aio.inventory.inventory_manager import PlayerInventory
    total = 0
    level_changed = False
    for uid in player_uids:
        uid_clean = str(uid).replace('-', '').upper()
        players_dir = os.path.join(constants.current_save_path, 'Players')
        if not os.path.isdir(players_dir):
            continue
        inv = PlayerInventory(uid_clean)
        inv.load()
        gvas = inv.player_gvas
        rd = gvas.properties['SaveData']['value']['RecordData']['value']
        if 'RelicPossessNumMap' not in rd:
            rd['RelicPossessNumMap'] = {'key_type': 'EnumProperty', 'value_type': 'IntProperty', 'key_struct_type': None, 'value_struct_type': None, 'id': None, 'value': [], 'type': 'MapProperty'}
        rmap = rd['RelicPossessNumMap']
        rmap['value'] = [{'key': rk, 'value': max_val} for rk, max_val in RELIC_CUMULATIVE_MAX.items()]
        if 'RelicPossessNum' not in rd:
            rd['RelicPossessNum'] = {'id': None, 'value': 0, 'type': 'IntProperty'}
        rd['RelicPossessNum']['value'] = sum((e.get('value', 0) for e in rmap['value']))
        if rd.get('RelicBonusExpTableIndex', {}).get('value', 0) < 9999:
            rd['RelicBonusExpTableIndex'] = {'id': None, 'value': 9999, 'type': 'IntProperty'}
        if inv:
            key_cont = inv.get_container('key')
            if key_cont:
                for item_id in EFFIGY_ITEM_IDS:
                    existing_slot = [s for s in key_cont.slots if s.get('item_id') == item_id]
                    if existing_slot:
                        old_qty = existing_slot[0].get('stack_count', 0)
                        key_cont.set_item_count(existing_slot[0]['slot_index'], old_qty + quantity)
                    else:
                        key_cont.add_item(item_id, quantity)
                    total += quantity
                wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
                item_containers = wsd.get('ItemContainerSaveData', {}).get('value', [])
                container_lookup = {}
                for c in item_containers:
                    cid = c.get('key', {}).get('ID', {}).get('value', '')
                    if cid:
                        container_lookup[cid] = c
                for ctype, container in inv.containers.items():
                    cid = str(container.container_id)
                    if cid in container_lookup:
                        raw_slots = container._standardized_container.get_raw_slots()
                        container_lookup[cid]['value']['Slots']['value']['values'] = raw_slots
                from palworld_aio.inventory.dynamic_item import sync_dynamic_items_with_registry
                sync_dynamic_items_with_registry(inv.containers)
        sav_path = os.path.join(players_dir, f'{uid_clean}.sav')
        gvasfile_to_sav(gvas, sav_path)
        wsd = constants.loaded_level_json['properties']['worldSaveData']['value']
        cmap = wsd.get('CharacterSaveParameterMap', {}).get('value', [])
        for entry in cmap:
            raw = entry.get('value', {}).get('RawData', {}).get('value', {})
            sp = raw.get('object', {}).get('SaveParameter', {})
            if sp.get('struct_type') != 'PalIndividualCharacterSaveParameter':
                continue
            sv = sp.get('value', {})
            if not sv.get('IsPlayer', {}).get('value'):
                continue
            uo = entry.get('key', {}).get('PlayerUId', {})
            eu = str(uo.get('value', '')).replace('-', '').lower() if isinstance(uo, dict) else ''
            if eu == uid_clean:
                sl = sv.setdefault('GotStatusPointList', {}).setdefault('value', {}).setdefault('values', [])
                seen_names = {s.get('StatusName', {}).get('value', ''): s for s in sl}
                for rk, stat_name in RELIC_TO_STATUS_NAME.items():
                    max_val = RELIC_MAX_RANK.get(rk, 99)
                    if stat_name in seen_names:
                        if seen_names[stat_name]['StatusPoint']['value'] != max_val:
                            seen_names[stat_name]['StatusPoint']['value'] = max_val
                            level_changed = True
                    else:
                        sl.append({'StatusName': {'id': None, 'value': stat_name, 'type': 'NameProperty'}, 'StatusPoint': {'id': None, 'value': max_val, 'type': 'IntProperty'}})
                        level_changed = True
                break
    if level_changed:
        constants.dirty = True
        g = constants.loaded_level_json.gvas_file
        t = 50 if 'Pal.PalworldSaveGame' in g.header.save_game_class_name else 49
        data = compress_gvas_to_sav(g.write(SKP_PALWORLD_CUSTOM_PROPERTIES), t)
        with open(os.path.join(constants.current_save_path, 'Level.sav'), 'wb') as f:
            f.write(data)
    if total:
        constants.dirty = True
    return total
def adjust_player_level(player_uid, target_level):
    if target_level < 1 or target_level > 80:
        return False
    current_level = constants.player_levels.get(str(player_uid).replace('-', ''), 1)
    if current_level == target_level:
        return True
    return set_player_level(player_uid, target_level)