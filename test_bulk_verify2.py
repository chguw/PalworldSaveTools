import sys, os, pickle
sys.path.insert(0, 'src')
from palworld_save_tools.palsav import decompress_sav_to_gvas, compress_gvas_to_sav
from palworld_save_tools.paltypes import PALWORLD_TYPE_HINTS, PALWORLD_CUSTOM_PROPERTIES
from palworld_save_tools.gvas import GvasFile

def load_sav(p):
    with open(p,'rb') as f:
        raw,_ = decompress_sav_to_gvas(f.read())
    return GvasFile.read(raw, PALWORLD_TYPE_HINTS, PALWORLD_CUSTOM_PROPERTIES, allow_nan=True)

def write_sav(gvas, path):
    data = gvas.write(PALWORLD_CUSTOM_PROPERTIES)
    t = 50
    with open(path, 'wb') as f:
        f.write(compress_gvas_to_sav(data, t))

def fast_deepcopy(obj):
    return pickle.loads(pickle.dumps(obj, -1))

# Use CLEAN copies
src_path = r'C:\Users\Administrator\Desktop\PST_v2.0.0\TestSaves\CharacterTransfer\PylarLatest_clean'
tgt_path = r'C:\Users\Administrator\Desktop\PST_v2.0.0\TestSaves\CharacterTransfer\BetaTest_clean'
outdir = r'C:\Users\Administrator\Desktop\PST_v2.0.0\TestSaves\CharacterTransfer\test_bulk_output3'
os.makedirs(outdir + '/Players', exist_ok=True)

player_uids = [f.replace('.sav', '') for f in os.listdir(src_path + '/Players') if f.endswith('.sav')]
# Skip the dps_ version, only take real players
player_uids = [u for u in player_uids if not u.endswith('_dps')]
print('Players to transfer:', player_uids)

src_gvas = load_sav(src_path + '/Level.sav')
src_wsd = src_gvas.properties['worldSaveData']['value']

tgt_gvas = load_sav(tgt_path + '/Level.sav')
tgt_wsd = tgt_gvas.properties['worldSaveData']['value']

print('Target original item containers:', len(tgt_wsd.get('ItemContainerSaveData',{}).get('value',[])))
print('Target original char containers:', len(tgt_wsd.get('CharacterContainerSaveData',{}).get('value',[])))

modified_targets_data = {}

for i, uid in enumerate(player_uids):
    print(f'\n--- Player {i+1}: {uid[:16]}... ---')
    host_gvas = load_sav(os.path.join(src_path, 'Players', uid + '.sav'))
    host_json = host_gvas.properties
    host_sd = host_json['SaveData']['value']
    host_guid = uid

    targ_gvas = fast_deepcopy(host_gvas)
    targ_json = targ_gvas.properties
    targ_sd = targ_json['SaveData']['value']

    tgt_wsd.setdefault('CharacterContainerSaveData', {'value': []})
    tgt_wsd.setdefault('ItemContainerSaveData', {'value': []})

    src_inv = host_sd['InventoryInfo']['value']
    src_char_ids = {host_sd['PalStorageContainerId']['value']['ID']['value'], host_sd['OtomoCharacterContainerId']['value']['ID']['value']}
    src_item_ids = {v for v in [
        src_inv['CommonContainerId']['value']['ID']['value'],
        src_inv['EssentialContainerId']['value']['ID']['value'],
        src_inv['WeaponLoadOutContainerId']['value']['ID']['value'],
        src_inv['PlayerEquipArmorContainerId']['value']['ID']['value'],
        src_inv['FoodEquipContainerId']['value']['ID']['value'],
    ]}

    print('Source player container IDs:')
    for k in ['CommonContainerId','EssentialContainerId','WeaponLoadOutContainerId','PlayerEquipArmorContainerId','FoodEquipContainerId']:
        print(f'  {k}: {src_inv[k]["value"]["ID"]["value"]}')
    print(f'  PalStorage: {host_sd["PalStorageContainerId"]["value"]["ID"]["value"]}')
    print(f'  Otomo: {host_sd["OtomoCharacterContainerId"]["value"]["ID"]["value"]}')

    for clist, ids in [('CharacterContainerSaveData', src_char_ids), ('ItemContainerSaveData', src_item_ids)]:
        existing = {c['key']['ID']['value'] for c in tgt_wsd[clist]['value']}
        copied = 0
        for c in src_wsd.get(clist, {}).get('value', []):
            cid = c['key']['ID']['value']
            if cid in ids and cid not in existing:
                tgt_wsd[clist]['value'].append(fast_deepcopy(c))
                copied += 1
        print(f'  {clist}: copied {copied}')

    # Simulate transfer_inventory_only
    inv_src = {k: src_inv[k]['value']['ID']['value'] for k in ['CommonContainerId','EssentialContainerId','WeaponLoadOutContainerId','PlayerEquipArmorContainerId','FoodEquipContainerId']}
    inv_tgt = {k: targ_sd['InventoryInfo']['value'][k]['value']['ID']['value'] for k in ['CommonContainerId','EssentialContainerId','WeaponLoadOutContainerId','PlayerEquipArmorContainerId','FoodEquipContainerId']}
    inv_lookup_src = {v: k for k, v in inv_src.items()}
    inv_lookup_tgt = {v: k for k, v in inv_tgt.items()}
    containers_src = {}
    containers_tgt = {}
    for c in src_wsd.get('ItemContainerSaveData', {}).get('value', []):
        cid = c['key']['ID']['value']
        if cid in inv_lookup_src:
            containers_src[inv_lookup_src[cid]] = c
    for c in tgt_wsd.get('ItemContainerSaveData', {}).get('value', []):
        cid = c['key']['ID']['value']
        if cid in inv_lookup_tgt:
            containers_tgt[inv_lookup_tgt[cid]] = c
    found = set(containers_tgt.keys())
    print(f'  Inventory containers found in targ_lvl: {len(containers_tgt)} keys')
    for k in ['CommonContainerId','EssentialContainerId','WeaponLoadOutContainerId','PlayerEquipArmorContainerId','FoodEquipContainerId']:
        print(f'    {k}: {"YES" if k in found else "NO"}')

    modified_targets_data[uid] = (fast_deepcopy(targ_json), targ_gvas, host_guid)

# Write level.sav
write_sav(tgt_gvas, outdir + '/Level.sav')

# Write each player .sav
for uid, (_, gvas_obj, _) in modified_targets_data.items():
    write_sav(gvas_obj, os.path.join(outdir, 'Players', uid + '.sav'))

# ===== VERIFY =====
print('\n=== VERIFY WRITTEN FILES ===')
check_lvl = load_sav(outdir + '/Level.sav')
c_wsd = check_lvl.properties['worldSaveData']['value']
print('Level.sav item containers:', len(c_wsd.get('ItemContainerSaveData',{}).get('value',[])))
print('Level.sav char containers:', len(c_wsd.get('CharacterContainerSaveData',{}).get('value',[])))

for uid in player_uids:
    check_pl = load_sav(os.path.join(outdir, 'Players', uid + '.sav'))
    pl_sd = check_pl.properties['SaveData']['value']
    pl_inv = pl_sd['InventoryInfo']['value']
    pl_ids = set()
    for k in ['CommonContainerId','EssentialContainerId','WeaponLoadOutContainerId','PlayerEquipArmorContainerId','FoodEquipContainerId']:
        pl_ids.add(str(pl_inv[k]['value']['ID']['value']))
    
    lvl_ids = {str(c['key']['ID']['value']) for c in c_wsd.get('ItemContainerSaveData',{}).get('value',[])}
    overlap = pl_ids & lvl_ids
    status = 'OK' if len(overlap) == 5 else 'MISMATCH'
    print(f'Player {uid[:16]}...: player.sav has {len(pl_ids)} IDs, level has {len(lvl_ids)} item containers, overlap: {len(overlap)}/5 [{status}]')
    if len(overlap) < 5:
        for pid in sorted(pl_ids):
            if pid not in lvl_ids:
                print(f'  MISSING from level: {pid}')
        for lid in sorted(lvl_ids):
            if lid not in pl_ids:
                print(f'  EXTRA in level: {lid}')
