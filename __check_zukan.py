import json

# Check ZukanIndexSuffix for relevant pals
with open('Exports/Pal/Content/Pal/DataTable/Character/DT_PalMonsterParameter.json') as f:
    raw = json.load(f)

rows = {}
if isinstance(raw, list):
    for t in raw:
        if isinstance(t, dict):
            rows.update(t.get('Rows', {}))
elif isinstance(raw, dict):
    rows = raw.get('Rows', {})

for k in ('ThunderBird_Ice', 'Umihebi', 'ThunderBird', 'GhostRabbit', 'DarkScorpion', 'BlueSkyDragon'):
    v = rows.get(k, {})
    if v:
        tribe = v.get('Tribe', '')
        if isinstance(tribe, str) and tribe.startswith('EPalTribeID::'):
            tribe = tribe[13:]
        rank = v.get('CombiRank', '?')
        zukan = v.get('ZukanIndex', '?')
        suffix = v.get('ZukanIndexSuffix', '')
        predator = v.get('Predator', False)
        ign = v.get('IgnoreCombi', False)
        print(f'{k:20s} tribe={tribe:20s} rank={rank:>4} zukan={str(zukan):>4} suffix={str(suffix):>2} predator={predator} ignore={ign}')
