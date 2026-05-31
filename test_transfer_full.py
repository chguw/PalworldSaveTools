import sys, os, pickle
sys.path.insert(0, 'src')
from palworld_save_tools.palsav import decompress_sav_to_gvas, compress_gvas_to_sav
from palworld_save_tools.paltypes import PALWORLD_TYPE_HINTS, PALWORLD_CUSTOM_PROPERTIES
from palworld_save_tools.gvas import GvasFile

def load_sav(p):
    with open(p,'rb') as f:
        raw,_ = decompress_sav_to_gvas(f.read())
    return GvasFile.read(raw, PALWORLD_TYPE_HINTS, PALWORLD_CUSTOM_PROPERTIES, allow_nan=True)

src = r'C:\Users\Administrator\Desktop\PST_v2.0.0\TestSaves\CharacterTransfer\PylarLatest\Level.sav'
tgt = r'C:\Users\Administrator\Desktop\PST_v2.0.0\TestSaves\CharacterTransfer\BetaTest\Level.sav'
outdir = r'C:\Users\Administrator\Desktop\PST_v2.0.0\TestSaves\CharacterTransfer\test_output'
os.makedirs(outdir + '/Players', exist_ok=True)

src_gvas = load_sav(src)
tgt_gvas = load_sav(tgt)

player_uid = 'F8829FDD000000000000000000000000'
pl_gvas = load_sav(os.path.join(os.path.dirname(src), 'Players', player_uid + '.sav'))

tgt_wsd = tgt_gvas.properties['worldSaveData']['value']
src_wsd = src_gvas.properties['worldSaveData']['value']
psd = pl_gvas.properties['SaveData']['value']

char_ids = {psd['PalStorageContainerId']['value']['ID']['value'], psd['OtomoCharacterContainerId']['value']['ID']['value']}
inv = psd['InventoryInfo']['value']
item_ids = {inv['CommonContainerId']['value']['ID']['value'], inv['EssentialContainerId']['value']['ID']['value'], inv['WeaponLoadOutContainerId']['value']['ID']['value'], inv['PlayerEquipArmorContainerId']['value']['ID']['value'], inv['FoodEquipContainerId']['value']['ID']['value']}

print('Char container IDs:', [str(x) for x in char_ids])
print('Item container IDs:', [str(x) for x in item_ids])

tgt_wsd.setdefault('CharacterContainerSaveData', {'value': []})
tgt_wsd.setdefault('ItemContainerSaveData', {'value': []})

for clist, ids in [('CharacterContainerSaveData', char_ids), ('ItemContainerSaveData', item_ids)]:
    existing = {c['key']['ID']['value'] for c in tgt_wsd[clist]['value']}
    copied = 0
    for c in src_wsd.get(clist, {}).get('value', []):
        cid = c['key']['ID']['value']
        if cid in ids and cid not in existing:
            tgt_wsd[clist]['value'].append(pickle.loads(pickle.dumps(c, -1)))
            copied += 1
    print(clist + ': copied ' + str(copied) + ' containers')

print('Target char containers: ' + str(len(tgt_wsd['CharacterContainerSaveData']['value'])))
print('Target item containers: ' + str(len(tgt_wsd['ItemContainerSaveData']['value'])))

data = tgt_gvas.write(PALWORLD_CUSTOM_PROPERTIES)
t = 50
with open(outdir + '/Level.sav', 'wb') as f:
    f.write(compress_gvas_to_sav(data, t))

print('Level.sav written successfully')
