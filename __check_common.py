import json

with open('Exports/Pal/Content/Pal/DataTable/Character/DT_PalMonsterParameter_Common.json') as f:
    raw = json.load(f)

rows = {}
if isinstance(raw, list):
    for t in raw:
        if isinstance(t, dict):
            rows.update(t.get('Rows', {}))
elif isinstance(raw, dict):
    rows = raw.get('Rows', {})

# Search for Umihebi in Common
for k, v in sorted(rows.items()):
    tribe = v.get('Tribe', '')
    if isinstance(tribe, str) and tribe.startswith('EPalTribeID::'):
        tribe = tribe[14:]
    if 'umibe' in tribe.lower():
        rank = v.get('CombiRank', '?')
        rar = v.get('Rarity', '?')
        ign = v.get('IgnoreCombi', False)
        print(f'{k}: tribe={tribe} rank={rank} rarity={rar} ignore={ign}')

# Also check the main file again for Umihebi
with open('Exports/Pal/Content/Pal/DataTable/Character/DT_PalMonsterParameter.json') as f:
    raw = json.load(f)

rows = {}
if isinstance(raw, list):
    for t in raw:
        if isinstance(t, dict):
            rows.update(t.get('Rows', {}))
elif isinstance(raw, dict):
    rows = raw.get('Rows', {})

print('--- Main file ---')
for k, v in sorted(rows.items()):
    tribe = v.get('Tribe', '')
    if isinstance(tribe, str) and tribe.startswith('EPalTribeID::'):
        tribe = tribe[14:]
    if 'umibe' in tribe.lower():
        rank = v.get('CombiRank', '?')
        rar = v.get('Rarity', '?')
        ign = v.get('IgnoreCombi', False)
        print(f'{k}: tribe={tribe} rank={rank} rarity={rar} ignore={ign}')
