import sys; sys.path.insert(0, 'src')
from palworld_save_tools.palsav import decompress_sav_to_gvas
from palworld_save_tools.paltypes import PALWORLD_TYPE_HINTS, PALWORLD_CUSTOM_PROPERTIES
from palworld_save_tools.gvas import GvasFile

outdir = r'C:\Users\Administrator\Desktop\PST_v2.0.0\TestSaves\CharacterTransfer\test_bulk_output4'
for uid in ['00000000000000000000000000000001', 'F8829FDD000000000000000000000000']:
    path = outdir + '/Players/' + uid + '.sav'
    with open(path,'rb') as f:
        raw, _ = decompress_sav_to_gvas(f.read())
    gvas = GvasFile.read(raw, PALWORLD_TYPE_HINTS, PALWORLD_CUSTOM_PROPERTIES, allow_nan=True)
    sd = gvas.properties['SaveData']['value']
    inv = sd['InventoryInfo']['value']
    print(uid[:16] + '... class: ' + gvas.header.save_game_class_name)
    print('  PalStorage: ' + str(sd['PalStorageContainerId']['value']['ID']['value']))
    for k in ['CommonContainerId','EssentialContainerId','WeaponLoadOutContainerId','PlayerEquipArmorContainerId','FoodEquipContainerId']:
        print('  ' + k + ': ' + str(inv[k]['value']['ID']['value']))
