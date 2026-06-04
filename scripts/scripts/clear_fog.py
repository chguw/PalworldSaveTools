import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
from palsav.gvas import GvasFile
from palsav.palsav import decompress_sav_to_gvas, compress_gvas_to_sav
from palsav.paltypes import PALWORLD_TYPE_HINTS
from palobject import SKP_PALWORLD_CUSTOM_PROPERTIES
path = sys.argv[1]
with open(path, 'rb') as f:
    data = f.read()
raw_gvas, _ = decompress_sav_to_gvas(data)
gvas = GvasFile.read(raw_gvas, PALWORLD_TYPE_HINTS, SKP_PALWORLD_CUSTOM_PROPERTIES)
d = gvas.dump()
sd = d['properties']['SaveData']['value']
if 'WorldMapUISaveDataMap' in sd:
    for entry in sd['WorldMapUISaveDataMap']['value']:
        mask = entry['value']['MaskTextureData']['value']
        mask['values'] = b'\x00' * len(mask['values'])
    print('WorldMapUISaveDataMap fog cleared')
elif 'WorldMapMaskTextureV4' in sd:
    mask = sd['WorldMapMaskTextureV4']['value']
    mask['values'] = b'\x00' * len(mask['values'])
    print('WorldMapMaskTextureV4 fog cleared')
hl = sd.get('Local_HiddenLocationFlagMap', {}).get('value', [])
for entry in hl:
    entry['value'] = False
print(f'Hidden locations set: {len(hl)} entries')
ng = GvasFile.load(d)
st = 50 if 'Pal.PalWorldSaveGame' in ng.header.save_game_class_name or 'Pal.PalLocalWorldSaveGame' in ng.header.save_game_class_name else 49
sav = compress_gvas_to_sav(ng.write(SKP_PALWORLD_CUSTOM_PROPERTIES), st)
with open(path, 'wb') as f:
    f.write(sav)
print('Saved')