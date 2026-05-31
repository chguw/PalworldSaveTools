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

src_path = r'C:\Users\Administrator\Desktop\PST_v2.0.0\TestSaves\CharacterTransfer\PylarLatest'
tgt_path = r'C:\Users\Administrator\Desktop\PST_v2.0.0\TestSaves\CharacterTransfer\BetaTest'
outdir = r'C:\Users\Administrator\Desktop\PST_v2.0.0\TestSaves\CharacterTransfer\test_bulk_output2'
os.makedirs(outdir + '/Players', exist_ok=True)

player_uids = [f.replace('.sav', '') for f in os.listdir(src_path + '/Players') if f.endswith('.sav')]
print('Players:', player_uids)

src_gvas = load_sav(src_path + '/Level.sav')
src_wsd = src_gvas.properties['worldSaveData']['value']

tgt_gvas = load_sav(tgt_path + '/Level.sav')
tgt_wsd = tgt_gvas.properties['worldSaveData']['value']

# BULK LOOP
for i, uid in enumerate(player_uids):
    host_gvas = load_sav(os.path.join(src_path, 'Players', uid + '.sav'))
    host_json = host_gvas.properties
    host_sd = host_json['SaveData']['value']

    # BULK APPROACH: deepcopy source
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

    for clist, ids in [('CharacterContainerSaveData', src_char_ids), ('ItemContainerSaveData', src_item_ids)]:
        existing = {c['key']['ID']['value'] for c in tgt_wsd[clist]['value']}
        for c in src_wsd.get(clist, {}).get('value', []):
            cid = c['key']['ID']['value']
            if cid in ids and cid not in existing:
                tgt_wsd[clist]['value'].append(fast_deepcopy(c))

    # Store player GvasFile (like modified_targets_data)
    write_sav(targ_gvas, os.path.join(outdir, 'Players', uid + '.sav'))

# Write level
write_sav(tgt_gvas, outdir + '/Level.sav')

# ===== VERIFY =====
print('\n=== VERIFICATION ===')
check_lvl = load_sav(outdir + '/Level.sav')
c_wsd = check_lvl.properties['worldSaveData']['value']

for uid in player_uids:
    check_pl = load_sav(os.path.join(outdir, 'Players', uid + '.sav'))
    pl_sd = check_pl.properties['SaveData']['value']
    pl_inv = pl_sd['InventoryInfo']['value']
    pl_ids = {str(x) for x in [
        pl_inv['CommonContainerId']['value']['ID']['value'],
        pl_inv['EssentialContainerId']['value']['ID']['value'],
        pl_inv['WeaponLoadOutContainerId']['value']['ID']['value'],
        pl_inv['PlayerEquipArmorContainerId']['value']['ID']['value'],
        pl_inv['FoodEquipContainerId']['value']['ID']['value'],
    ]}

    lvl_ids = {str(c['key']['ID']['value']) for c in c_wsd.get('ItemContainerSaveData',{}).get('value',[])}
    overlap = pl_ids & lvl_ids
    print(f'Player {uid[:16]}...: player.sav has {len(pl_ids)} IDs, level has {len(lvl_ids)} item containers, overlap: {len(overlap)}/5')
    if len(overlap) < 5:
        for pid in pl_ids:
            if pid not in lvl_ids:
                print(f'  MISSING from level: {pid}')
