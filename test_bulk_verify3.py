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

src_path = r'C:\Users\Administrator\Desktop\PST_v2.0.0\TestSaves\CharacterTransfer\PylarLatest_clean'
tgt_path = r'C:\Users\Administrator\Desktop\PST_v2.0.0\TestSaves\CharacterTransfer\BetaTest_clean'
outdir = r'C:\Users\Administrator\Desktop\PST_v2.0.0\TestSaves\CharacterTransfer\test_bulk_output4'
os.makedirs(outdir + '/Players', exist_ok=True)

player_uids = [f.replace('.sav', '') for f in os.listdir(src_path + '/Players') if f.endswith('.sav') and not f.endswith('_dps.sav')]
print('Players:', player_uids)

src_gvas = load_sav(src_path + '/Level.sav')
src_wsd = src_gvas.properties['worldSaveData']['value']
tgt_gvas = load_sav(tgt_path + '/Level.sav')
tgt_wsd = tgt_gvas.properties['worldSaveData']['value']

modified_targets_data = {}

for i, uid in enumerate(player_uids):
    host_gvas = load_sav(os.path.join(src_path, 'Players', uid + '.sav'))
    host_json = host_gvas.properties
    host_sd = host_json['SaveData']['value']

    # BULK: deepcopy source .sav for target
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

    modified_targets_data[uid] = (fast_deepcopy(targ_json), targ_gvas, uid)

# Write level
write_sav(tgt_gvas, outdir + '/Level.sav')
for uid, (_, gvas_obj, _) in modified_targets_data.items():
    write_sav(gvas_obj, os.path.join(outdir, 'Players', uid + '.sav'))

# VERIFY: check player.sav container IDs vs level.sav
print('\n=== VERIFICATION ===')
check_lvl = load_sav(outdir + '/Level.sav')
c_wsd = check_lvl.properties['worldSaveData']['value']

all_ok = True
for uid in player_uids:
    check_pl = load_sav(os.path.join(outdir, 'Players', uid + '.sav'))
    pl_sd = check_pl.properties['SaveData']['value']
    pl_inv = pl_sd['InventoryInfo']['value']
    pl_ids = set()
    for k in ['CommonContainerId','EssentialContainerId','WeaponLoadOutContainerId','PlayerEquipArmorContainerId','FoodEquipContainerId']:
        pl_ids.add(str(pl_inv[k]['value']['ID']['value']))
    
    # Also check char containers
    pal_id = str(pl_sd['PalStorageContainerId']['value']['ID']['value'])
    oto_id = str(pl_sd['OtomoCharacterContainerId']['value']['ID']['value'])
    
    lvl_item_ids = {str(c['key']['ID']['value']) for c in c_wsd.get('ItemContainerSaveData',{}).get('value',[])}
    lvl_char_ids = {str(c['key']['ID']['value']) for c in c_wsd.get('CharacterContainerSaveData',{}).get('value',[])}
    
    item_ok = pl_ids.issubset(lvl_item_ids)
    char_ok = {pal_id, oto_id}.issubset(lvl_char_ids)
    
    status = 'OK' if (item_ok and char_ok) else 'MISMATCH'
    if not all_ok or not item_ok or not char_ok:
        all_ok = False
        if not item_ok:
            print(f'  Player {uid[:16]} ITEM containers mismatch: {pl_ids - lvl_item_ids}')
        if not char_ok:
            print(f'  Player {uid[:16]} CHAR containers mismatch: missing {pal_id if pal_id not in lvl_char_ids else ""} {oto_id if oto_id not in lvl_char_ids else ""}')

if all_ok:
    print('ALL OK: every player.sav container ID exists in level.sav')
else:
    print('MISMATCH FOUND')
