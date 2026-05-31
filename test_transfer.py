import sys, os, json, shutil
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))
from palworld_save_tools.palsav import decompress_sav_to_gvas, compress_gvas_to_sav
from palworld_save_tools.paltypes import PALWORLD_TYPE_HINTS, PALWORLD_CUSTOM_PROPERTIES
from palworld_save_tools.gvas import GvasFile
from palworld_save_tools.archive import UUID

def load_sav(path):
    with open(path, 'rb') as f:
        raw, _ = decompress_sav_to_gvas(f.read())
    return GvasFile.read(raw, PALWORLD_TYPE_HINTS, PALWORLD_CUSTOM_PROPERTIES, allow_nan=True)

def write_sav(gvas, path):
    data = gvas.write(PALWORLD_CUSTOM_PROPERTIES)
    t = 50 if 'Pal.PalworldSaveGame' in gvas.header.save_game_class_name or 'Pal.PalLocalWorldSaveGame' in gvas.header.save_game_class_name else 49
    tmp = path + '.tmp'
    with open(tmp, 'wb') as f:
        f.write(compress_gvas_to_sav(data, t))
    os.replace(tmp, path)

def dump_json(obj, path):
    with open(path, 'w') as f:
        json.dump(obj, f, indent=2, default=str)

def main():
    src_level_path = sys.argv[1]
    tgt_level_path = sys.argv[2]
    player_uid = sys.argv[3].upper()
    out_dir = sys.argv[4] if len(sys.argv) > 4 else 'transfer_test_output'
    os.makedirs(out_dir, exist_ok=True)

    print(f'Source: {src_level_path}')
    print(f'Target: {tgt_level_path}')
    print(f'Player: {player_uid}')
    print(f'Output: {out_dir}')

    # Load source level
    src_gvas = load_sav(src_level_path)
    src_level = src_gvas.properties['worldSaveData']['value']
    print(f'Source level loaded. CharSaveParamMap entries: {len(src_level.get("CharacterSaveParameterMap",{}).get("value",[]))}')

    # Load target level
    tgt_gvas = load_sav(tgt_level_path)
    tgt_level = tgt_gvas.properties['worldSaveData']['value']
    print(f'Target level loaded. CharSaveParamMap entries: {len(tgt_level.get("CharacterSaveParameterMap",{}).get("value",[]))}')

    # Load player .sav from source
    src_players_dir = os.path.join(os.path.dirname(src_level_path), 'Players')
    player_sav_path = os.path.join(src_players_dir, f'{player_uid}.sav')
    player_gvas = load_sav(player_sav_path)
    player_json = player_gvas.properties
    print(f'Player .sav loaded from source Players/')

    # Extract container IDs BEFORE transfer
    inv_info = player_json['SaveData']['value']['InventoryInfo']['value']
    src_container_ids = {
        'CommonContainerId': inv_info['CommonContainerId']['value']['ID']['value'],
        'EssentialContainerId': inv_info['EssentialContainerId']['value']['ID']['value'],
        'WeaponLoadOutContainerId': inv_info['WeaponLoadOutContainerId']['value']['ID']['value'],
        'PlayerEquipArmorContainerId': inv_info['PlayerEquipArmorContainerId']['value']['ID']['value'],
        'FoodEquipContainerId': inv_info['FoodEquipContainerId']['value']['ID']['value'],
    }
    print(f'Player container IDs (from source .sav):')
    for k, v in src_container_ids.items():
        print(f'  {k}: {v}')

    # Check which player containers exist in target level BEFORE transfer
    tgt_item_containers = {c['key']['ID']['value'] for c in tgt_level.get('ItemContainerSaveData', {}).get('value', [])}
    print(f'\nTarget level ItemContainerSaveData has {len(tgt_item_containers)} containers total')
    for k, cid in src_container_ids.items():
        found = cid in tgt_item_containers
        print(f'  {k} container {"FOUND" if found else "MISSING"} in target level')

    # Check which player containers exist in SOURCE level
    src_item_containers = {c['key']['ID']['value'] for c in src_level.get('ItemContainerSaveData', {}).get('value', [])}
    print(f'\nSource level ItemContainerSaveData has {len(src_item_containers)} containers total')
    for k, cid in src_container_ids.items():
        found = cid in src_item_containers
        print(f'  {k} container {"FOUND" if found else "MISSING"} in source level')

    # Dump item container IDs from both levels
    print(f'\n=== ITEM CONTAINER IDS IN TARGET LEVEL ===')
    for c in tgt_level.get('ItemContainerSaveData', {}).get('value', []):
        cid = c['key']['ID']['value']
        match = '<<< PLAYER' if str(cid).replace('-','').lower() in [str(v).replace('-','').lower() for v in src_container_ids.values()] else ''
        print(f'  {cid} {match}')

    print(f'\n=== ITEM CONTAINER IDS IN SOURCE LEVEL ===')
    for c in src_level.get('ItemContainerSaveData', {}).get('value', []):
        cid = c['key']['ID']['value']
        match = '<<< PLAYER' if str(cid).replace('-','').lower() in [str(v).replace('-','').lower() for v in src_container_ids.values()] else ''
        print(f'  {cid} {match}')

    # Dump character container IDs from target level
    print(f'\n=== CHAR CONTAINER IDS IN TARGET LEVEL ===')
    for c in tgt_level.get('CharacterContainerSaveData', {}).get('value', []):
        cid = c['key']['ID']['value']
        print(f'  {cid}')

    # Dump character container IDs from source level
    print(f'\n=== CHAR CONTAINER IDS IN SOURCE LEVEL ===')
    for c in src_level.get('CharacterContainerSaveData', {}).get('value', []):
        cid = c['key']['ID']['value']
        print(f'  {cid}')

    # Save full JSON dumps for comparison
    dump_json({
        'player_container_ids': {k: str(v) for k, v in src_container_ids.items()},
        'target_level_item_container_ids': [str(c['key']['ID']['value']) for c in tgt_level.get('ItemContainerSaveData', {}).get('value', [])],
        'source_level_item_container_ids': [str(c['key']['ID']['value']) for c in src_level.get('ItemContainerSaveData', {}).get('value', [])],
        'target_level_char_container_ids': [str(c['key']['ID']['value']) for c in tgt_level.get('CharacterContainerSaveData', {}).get('value', [])],
        'source_level_char_container_ids': [str(c['key']['ID']['value']) for c in src_level.get('CharacterContainerSaveData', {}).get('value', [])],
    }, os.path.join(out_dir, 'pre_transfer_analysis.json'))

    print(f'\n=== ANALYSIS COMPLETE ===')
    print(f'Note: If player container IDs shown above are NOT found in the target level,')
    print(f'transfer_character_only() must copy them from source level.')
    print(f'If they ARE found in target level, the player already exists in target world.')
    print(f'Full dumps saved to {out_dir}/')

if __name__ == '__main__':
    main()
