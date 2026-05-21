#!/usr/bin/env python3
"""
Temp diagnostic script: loads a save file and parses items/pals/etc
as PST would, reporting which names/icons resolve correctly and which don't.

Usage:
    python scripts/diagnose_save.py [save_path_or_dir]

If no path given, uses EntSave/ in the project root.
"""

import os
import sys
import json

SRC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src')
sys.path.insert(0, SRC_DIR)
os.environ.setdefault('PST_SRC_DIR', SRC_DIR)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

from palworld_save_tools import json_tools
from palworld_save_tools.archive import UUID as _UUID
from palworld_aio.utils import sav_to_json


def _str_uuid(val):
    if isinstance(val, _UUID):
        return str(val)
    if isinstance(val, dict):
        return str(val.get('value', ''))
    return str(val) if val else ''


def load_json(path):
    if not os.path.exists(path):
        return None
    try:
        return json_tools.load(path)
    except Exception as e:
        print(f"  ERROR loading {path}: {e}")
        return None


def main():
    if len(sys.argv) > 1:
        save_path = sys.argv[1]
    else:
        save_path = os.path.join(BASE_DIR, 'EntSave')

    resources_dir = os.path.join(BASE_DIR, 'resources', 'game_data')

    # Load game data
    paldata = load_json(os.path.join(resources_dir, 'paldata.json')) or {}
    itemdata = load_json(os.path.join(resources_dir, 'itemdata.json')) or {}
    npcdata = load_json(os.path.join(resources_dir, 'npcdata.json')) or {}

    pals_list = paldata.get('pals', [])
    items_list = itemdata.get('items', [])
    npcs_list = npcdata.get('npcs', [])

    pal_asset_map = {p['asset'].lower(): p for p in pals_list}
    item_asset_map = {i['asset'].lower(): i for i in items_list}
    npc_asset_map = {n['asset'].lower(): n for n in npcs_list}

    # Also build a "stripped" pal map for the edit_pals.py lookup pattern
    pal_asset_map_stripped = {}
    for p in pals_list:
        asset_lower = p['asset'].lower()
        pal_asset_map_stripped[asset_lower] = p
        # Also index by stripped boss_ prefix (as edit_pals.py does)
        stripped = asset_lower.replace('boss_', '').replace('b_o_s_s_', '')
        if stripped != asset_lower:
            if stripped not in pal_asset_map_stripped:
                pal_asset_map_stripped[stripped] = p
            else:
                # Conflict - two pals might map to same stripped name
                pal_asset_map_stripped[stripped] = p

    # Verify icon files exist
    icon_dir = os.path.join(resources_dir, 'icons')
    missing_pal_icons = []
    for p in pals_list:
        icon_rel = p.get('icon', '')
        if icon_rel:
            icon_path = os.path.join(resources_dir, icon_rel.lstrip('/'))
            if not os.path.exists(icon_path):
                missing_pal_icons.append((p['asset'], icon_rel))

    missing_item_icons = []
    for i in items_list:
        icon_rel = i.get('icon', '')
        if icon_rel:
            icon_path = os.path.join(resources_dir, icon_rel.lstrip('/'))
            if not os.path.exists(icon_path):
                missing_item_icons.append((i['asset'], icon_rel))

    # Load the save
    if os.path.isdir(save_path):
        level_sav = os.path.join(save_path, 'Level.sav')
        players_dir = os.path.join(save_path, 'Players')
    else:
        level_sav = save_path if save_path.endswith('.sav') else None
        players_dir = None

    print("=" * 70)
    print("  PST Save Diagnostic Tool")
    print("=" * 70)

    if level_sav and os.path.exists(level_sav):
        print(f"\nLoading Level.sav: {level_sav}")
        try:
            level_json = sav_to_json(level_sav)
        except Exception as e:
            print(f"  ERROR loading Level.sav: {e}")
            level_json = None
    else:
        print(f"\nLevel.sav not found at: {level_sav}")
        level_json = None

    if not level_json:
        print("\nERROR: Could not load save file.")
        sys.exit(1)

    wsd = level_json.get('properties', {}).get('worldSaveData', {}).get('value', {})

    # ------------------------------------------------------------------
    # 1. ITEM ANALYSIS
    # ------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("  SECTION 1: Item Container Analysis")
    print("=" * 70)

    item_containers = wsd.get('ItemContainerSaveData', {}).get('value', [])
    print(f"\n  Total containers in Level.sav: {len(item_containers)}")

    all_item_ids_found = {}  # static_id -> count
    unknown_items = {}       # static_id -> count (not in itemdata)

    for cont in item_containers:
        slots = cont.get('value', {}).get('Slots', {}).get('value', {}).get('values', [])
        for slot in slots:
            raw = slot.get('RawData', {})
            raw_value = raw.get('value', {}) if isinstance(raw, dict) else {}
            if isinstance(raw_value, dict):
                item_data = raw_value.get('item', {})
                static_id = item_data.get('static_id', '') if isinstance(item_data, dict) else ''
                count = raw_value.get('count', 1) if isinstance(raw_value, dict) else 1
                if static_id:
                    all_item_ids_found[static_id] = all_item_ids_found.get(static_id, 0) + count
                    if static_id.lower() not in item_asset_map:
                        unknown_items[static_id] = unknown_items.get(static_id, 0) + count

    print(f"  Unique item static_ids found: {len(all_item_ids_found)}")
    print(f"  Items NOT in itemdata.json: {len(unknown_items)}")
    if unknown_items:
        print("\n  --- Unknown Items (missing from itemdata.json) ---")
        for item_id, count in sorted(unknown_items.items(), key=lambda x: -x[1]):
            print(f"    {item_id:<50} count={count}")

    # Also check player inventories
    print("\n  --- Player Save Files ---")
    if players_dir and os.path.isdir(players_dir):
        sav_files = [f for f in os.listdir(players_dir) if f.endswith('.sav')]
        print(f"  Found {len(sav_files)} player save files")
        unknown_player_items = {}
        known_player_items = {}
        player_char_ids = {}

        for sav_file in sav_files:
            sav_path = os.path.join(players_dir, sav_file)
            try:
                player_json = sav_to_json(sav_path)
            except Exception as e:
                print(f"    ERROR loading {sav_file}: {e}")
                continue

            props = player_json.get('properties', {})
            save_data = props.get('SaveData', {}).get('value', {})
            inv_info = save_data.get('InventoryInfo', {}).get('value', {})

            # Container IDs for this player
            container_refs = {
                'CommonContainerId': inv_info.get('CommonContainerId', {}).get('value', {}).get('ID', {}).get('value', ''),
                'EssentialContainerId': inv_info.get('EssentialContainerId', {}).get('value', {}).get('ID', {}).get('value', ''),
                'WeaponLoadOutContainerId': inv_info.get('WeaponLoadOutContainerId', {}).get('value', {}).get('ID', {}).get('value', ''),
                'PlayerEquipArmorContainerId': inv_info.get('PlayerEquipArmorContainerId', {}).get('value', {}).get('ID', {}).get('value', ''),
                'FoodEquipContainerId': inv_info.get('FoodEquipContainerId', {}).get('value', {}).get('ID', {}).get('value', ''),
                'DropSlotContainerId': inv_info.get('DropSlotContainerId', {}).get('value', {}).get('ID', {}).get('value', ''),
            }

            # Find actual container data from Level.sav
            for cont_type, cont_id in container_refs.items():
                if not cont_id:
                    continue
                cont_id_low = _str_uuid(cont_id).replace('-', '').lower()
                for cont in item_containers:
                    cid = cont.get('key', {}).get('ID', {}).get('value', '')
                    cid_str = _str_uuid(cid)
                    if cid_str and cid_str.replace('-', '').lower() == cont_id_low:
                        slots = cont.get('value', {}).get('Slots', {}).get('value', {}).get('values', [])
                        for slot in slots:
                            raw = slot.get('RawData', {})
                            raw_value = raw.get('value', {}) if isinstance(raw, dict) else {}
                            if isinstance(raw_value, dict):
                                item_data = raw_value.get('item', {})
                                static_id = item_data.get('static_id', '') if isinstance(item_data, dict) else ''
                                count = raw_value.get('count', 1) if isinstance(raw_value, dict) else 1
                                if static_id:
                                    if static_id.lower() not in item_asset_map:
                                        unknown_player_items[static_id] = unknown_player_items.get(static_id, 0) + count
                                    else:
                                        known_player_items[static_id] = known_player_items.get(static_id, 0) + count

            # Character ID (pal) in player save
            character_id = save_data.get('CharacterID', {}).get('value', '')
            if character_id:
                player_char_ids[sav_file] = character_id

        if unknown_player_items:
            print("\n  --- Unknown Items in Player Inventories ---")
            for item_id, count in sorted(unknown_player_items.items(), key=lambda x: -x[1]):
                icon_path = f'/icons/items/{item_id}.webp'
                full_icon = os.path.join(resources_dir, 'icons', 'items', f'{item_id}.webp')
                icon_exists = os.path.exists(full_icon)
                print(f"    {item_id:<50} count={count:<5} icon_exists={icon_exists}")
                # Check with different naming patterns
                for alt in [f'T_itemicon_{item_id}.webp', f'T_itemicon_{item_id}.png', f'{item_id}.png']:
                    alt_path = os.path.join(resources_dir, 'icons', 'items', alt)
                    if os.path.exists(alt_path):
                        print(f"      -> Found alternative: {alt}")

        print(f"\n  Known items in player inventories: {len(known_player_items)} unique types")
    else:
        print("  No player saves directory found")

    # Also scan guild chests
    guild_extra_map = wsd.get('GuildExtraSaveDataMap', {}).get('value', [])
    print(f"\n  Guild storage entries: {len(guild_extra_map)}")
    unknown_guild_items = {}
    for guild_entry in guild_extra_map:
        guild_storage = guild_entry.get('value', {}).get('GuildItemStorage', {})
        raw_data = guild_storage.get('value', {}).get('RawData', {}).get('value', {})
        # Try to find container_id from raw_data and cross-reference
        container_id = raw_data.get('container_id', '')
        if container_id:
            cont_id_low = _str_uuid(container_id).replace('-', '').lower()
            for cont in item_containers:
                cid = cont.get('key', {}).get('ID', {}).get('value', '')
                cid_str = _str_uuid(cid)
                if cid_str and cid_str.replace('-', '').lower() == cont_id_low:
                    slots = cont.get('value', {}).get('Slots', {}).get('value', {}).get('values', [])
                    for slot in slots:
                        raw = slot.get('RawData', {})
                        raw_value = raw.get('value', {}) if isinstance(raw, dict) else {}
                        if isinstance(raw_value, dict):
                            item_data = raw_value.get('item', {})
                            static_id = item_data.get('static_id', '') if isinstance(item_data, dict) else ''
                            count = raw_value.get('count', 1) if isinstance(raw_value, dict) else 1
                            if static_id and static_id.lower() not in item_asset_map:
                                unknown_guild_items[static_id] = unknown_guild_items.get(static_id, 0) + count

    if unknown_guild_items:
        print("\n  --- Unknown Items in Guild Storage ---")
        for item_id, count in sorted(unknown_guild_items.items(), key=lambda x: -x[1]):
            print(f"    {item_id:<50} count={count}")

    # ------------------------------------------------------------------
    # 2. PAL / CHARACTER ANALYSIS
    # ------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("  SECTION 2: Character (Pal/NPC) Analysis")
    print("=" * 70)

    char_map = wsd.get('CharacterSaveParameterMap', {}).get('value', [])
    print(f"\n  Total characters in save: {len(char_map)}")

    unknown_pals = {}
    known_pals = {}
    pal_icon_status = {'found': 0, 'missing': []}
    boss_variants_mismatch = []

    for entry in char_map:
        raw = entry.get('value', {}).get('RawData', {}).get('value', {})
        sp = raw.get('object', {}).get('SaveParameter', {})
        if sp.get('struct_type') != 'PalIndividualCharacterSaveParameter':
            continue
        sp_val = sp.get('value', {})
        cid = sp_val.get('CharacterID', {}).get('value', '')

        if not cid:
            continue

        cid_lower = cid.lower()

        # Method 1: Direct lookup in paldata
        direct_match = cid_lower in pal_asset_map

        # Method 2: Stripped lookup (as edit_pals.py does)
        cid_stripped = cid_lower.replace('boss_', '').replace('b_o_s_s_', '')
        stripped_match = cid_stripped in pal_asset_map_stripped if not direct_match else False

        # Method 3: Stripped lookup but comparing with original paldata assets
        stripped_match_original = False
        stripped_pal_asset = None
        if not direct_match:
            for pal_asset, pal_data in pal_asset_map.items():
                pal_stripped = pal_asset.replace('boss_', '').replace('b_o_s_s_', '')
                if pal_stripped == cid_stripped:
                    stripped_match_original = True
                    stripped_pal_asset = pal_asset
                    break

        # Check icon resolution
        icon_works = False
        if direct_match:
            pal_entry = pal_asset_map[cid_lower]
            icon_rel = pal_entry.get('icon', '')
            if icon_rel:
                icon_full = os.path.join(resources_dir, icon_rel.lstrip('/'))
                icon_works = os.path.exists(icon_full)

        if direct_match:
            known_pals[cid] = known_pals.get(cid, 0) + 1
            if not icon_works:
                pal_entry = pal_asset_map[cid_lower]
                pal_icon_status['missing'].append(cid)
        elif stripped_match_original:
            # This is the bug case: stripped match works but direct doesn't
            boss_variants_mismatch.append({
                'character_id': cid,
                'stripped_id': cid_stripped,
                'actual_asset': stripped_pal_asset,
                'display_name': pal_asset_map.get(stripped_pal_asset, {}).get('name', '?')
            })
            # Check if stripping also finds the icon
            pal_entry = pal_asset_map.get(stripped_pal_asset, {})
            icon_rel = pal_entry.get('icon', '')
            if icon_rel:
                icon_full = os.path.join(resources_dir, icon_rel.lstrip('/'))
                if not os.path.exists(icon_full):
                    pal_icon_status['missing'].append(cid)
            known_pals[cid] = known_pals.get(cid, 0) + 1
        else:
            # Check NPC data
            npc_match = cid_lower in npc_asset_map
            if npc_match:
                known_pals[cid] = known_pals.get(cid, 0) + 1
            else:
                unknown_pals[cid] = unknown_pals.get(cid, 0) + 1

    print(f"  Known characters (in paldata/npcdata): {sum(known_pals.values())} instances, {len(known_pals)} unique")
    print(f"  Unknown characters (NOT in paldata/npcdata): {sum(unknown_pals.values())} instances, {len(unknown_pals)} unique")

    if unknown_pals:
        print("\n  --- Unknown Character IDs ---")
        for cid, count in sorted(unknown_pals.items(), key=lambda x: -x[1]):
            icon_path_guess = os.path.join(resources_dir, 'icons', 'pals', f'{cid.lower().replace("boss_", "").replace("b_o_s_s_", "")}.webp')
            icon_exists = os.path.exists(icon_path_guess)
            print(f"    {cid:<50} count={count:<5}  guessed_icon_exists={icon_exists}")

    if boss_variants_mismatch:
        print("\n  --- BOSS Variants with Stripped Prefix Match (BUG: edit_pals strips boss_ before lookup) ---")
        for item in boss_variants_mismatch:
            print(f"    CharacterID: {item['character_id']:<40} Stripped: {item['stripped_id']:<30} -> Actual asset: {item['actual_asset']}")
            print(f"      Would show name: {item['display_name']} (lookup FAILS because asset name doesn't match stripped ID)")

    # ------------------------------------------------------------------
    # 3. ICON FILE REPORT
    # ------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("  SECTION 3: Icon File Report")
    print("=" * 70)

    print(f"\n  Pal icons referenced but missing on disk: {len(missing_pal_icons)}")
    for asset, icon_rel in missing_pal_icons[:20]:
        print(f"    {asset:<40} -> {icon_rel}")
    if len(missing_pal_icons) > 20:
        print(f"    ... and {len(missing_pal_icons) - 20} more")

    print(f"\n  Item icons referenced but missing on disk: {len(missing_item_icons)}")
    for asset, icon_rel in missing_item_icons[:20]:
        print(f"    {asset:<40} -> {icon_rel}")
    if len(missing_item_icons) > 20:
        print(f"    ... and {len(missing_item_icons) - 20} more")

    # ------------------------------------------------------------------
    # 4. ANALYSIS SUMMARY
    # ------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("  SECTION 4: Summary & Recommendations")
    print("=" * 70)

    issues_found = []

    if unknown_items:
        issues_found.append(f"  [{len(unknown_items)} unknown items in save] - Add to itemdata.json or check naming")

    if unknown_pals:
        issues_found.append(f"  [{len(unknown_pals)} unknown character IDs in save] - Missing from paldata.json")

    if boss_variants_mismatch:
        issues_found.append(f"  [{len(boss_variants_mismatch)} BOSS variants] - edit_pals.py strips 'boss_' before lookup, causing icon/name mismatch")

    if missing_pal_icons:
        issues_found.append(f"  [{len(missing_pal_icons)} missing pal icon files on disk]")

    if missing_item_icons:
        issues_found.append(f"  [{len(missing_item_icons)} missing item icon files on disk]")

    if not issues_found:
        print("\n  No issues detected! All items, pals, and icons resolve correctly.")
    else:
        print(f"\n  {len(issues_found)} issue(s) detected:")
        for issue in issues_found:
            print(f"  {issue}")

    print("\n" + "=" * 70)
    print("  Diagnostic complete.")
    print("=" * 70)


if __name__ == '__main__':
    main()
