---
name: pst-game-data
description: Schemas of all 11 resources/game_data/*.json files, the 6 app config presets in src/data/configs/, the i18n system (8 languages, t() lookup, English fallback), the resources/assets directory layout, and resource resolution (dev vs frozen builds). Load when editing game data, configs, i18n, or asset paths.
---

# PST Game Data, Configs, i18n, Resources

## Game data JSON (resources/game_data/) — 11 files

### characters.json (1.79MB) — THE pal/NPC reference
Schema: `{ pals:[PalObj], npcs:[NpcObj], friendship:{rank:{...}} }`. ~743 pals, ~413 npcs, 14 friendship ranks.
PalObj: `{ name, asset (UE internal), icon ("/icons/pals/T_X_icon_normal.webp"), elements:{ElemName:{name,icon,icon_large,icon_passive_base}}, stats:{hp,melee_attack,shot_attack,defense,support,craft_speed,max_full_stomach,food_amount,element_type1,element_type2,zukan_index,rarity,size,rarity,run_speed,ride_sprint_speed}, scaling:{hp,attack,defense}, friendship_hp/shotattack/defense (float), work_suitabilities:{EmitFlame,Watering,Seeding,GenerateElectricity,Handcraft,Collection,Deforest,Mining,OilExtraction,ProductMedicine,Cool,Transport,MonsterFarm}, partner_skill, description (may have {placeholders}, [ICON:..], [ELEM:..]), passives:[str] }`.
NpcObj: `{ name, asset, icon }` (simple).
Keyed by: list arrays; matched by `asset` field.

### skills.json (1.92MB) — passives + active skills + elements
Schema: `{ passives:[PassiveObj], skills:[SkillObj], elements:[ElementObj] }`. ~1905 passives, ~375 skills, 9 elements.
PassiveObj: `{ name, asset, rank, icon, description, effect1-4 (float), efftype1-3 (EPalPassiveSkillEffectType::), add_pal/add_rare_pal/add_world_tree_pal/add_mutation_pal/add_armor/add_accessory/add_weapon (bool), invoke_always, category }`.
SkillObj: `{ name, asset, element, power, cooldown, description }`.
ElementObj: `{ name (internal: Normal/Fire/Water/...), display (UI: Neutral/Fire/...), index (0-8), color (hex), icons:{passive_base,large,palstatus,small} }`.

### items.json (1.29MB) — item DB
Schema: `{ items:[ItemObj] }`. 2470 items. ItemObj: `{ name, asset (item ID), icon, rarity (0-4), type_a (EPalItemTypeA::), type_b (EPalItemTypeB::), description, sort_id }`.

### world.json (611KB) — structures + technology + lab research
Schema: `{ structures:[StructObj], technology:[TechObj], lab_research:{id:{...}} }`. ~1089 structures, ~588 tech, ~168 research.
StructObj/TechObj: `{ name, asset, icon, type (TechObj: "standard"|"boss"), description }`.
lab_research entry: `{ TextId, LabCategoryWorkSuitability, LabCategorySubType, AssignDefineId, RequiredWorkAmount, ResearchSpaceBlueprintClassName, ResearchSpaceClassPath{AssetPathName,SubPathString}, RequiredResearchId (prereq or "None"), Material1-4_Id/Count, EffectType, EffectValue, EffectOptionWorkSuitability, EffectOptionItemType, EffectDescriptionTextIdOverwrite, bIsEssential }`.

### pal_exp_table.json (25.8KB)
Schema: `{ "<level_str>"(1-100): {DropEXP,NextEXP,PalNextEXP,TotalEXP,PalTotalEXP,BuildEXP,CraftEXP,PalBuildEXP,PalCraftEXP} }`. 100 entries.

### boss_mapping.json (27KB)
Schema: `{ boss_defeat_flag_map: { "<reward_id>": [str]|str } }`. 99 entries. Maps boss defeat reward flags → associated map object instance names.

### reference_unlock_data.json (10.4KB)
4 keys: `FastTravelPointUnlockFlag_guids`([str] ~182 GUIDs), `FindAreaFlagMap_keys`([str] ~123 areas), `UnlockedWorldMapFlags`({MainMap:bool,Tree:bool}), `AreaBarrierUnlockFlags_guids`([str] 6 GUIDs).

### relic_data.json (3.9KB)
Schema: `{ "EPalRelicType::<Name>": {cumulative_max, max_rank, per_rank:[int]} }`. 13 types (CapturePower, ClimbSpeed, ExpBonus, FoodDecayReduction, ...).

### friendship.json (1.3KB)
Schema: `{ "<rank>": {FriendshipRank, RequiredPoint} }`. 14 ranks (Friendship_Rank_Minus3..10). **Duplicate of characters.json friendship block.**

### uidata.json (1.7KB)
Schema: `{ ui_icons: { "<key>": "/icons/ui/..." } }`. ~25 UI icon mappings.

### world_map_areas.json (3.5KB)
Schema: `{ areas:[str] }`. ~123 valid world map area identifiers.

## App configs (src/data/configs/) — 6 files
- **config.json**: `{ lang }` — user UI language.
- **zone_exclusions.json**: `{ zones:[{name,x1,y1,x2,y2,enabled,id} | {name,type:"polygon",points:[{x,y}],enabled,id}], version }`. Map exclusion zones.
- **base_inventory_loadouts.json**: `{ MedRack:{regular:[ItemRef],key_items:[ItemRef]}, GuildChest:{...} }`. ItemRef={id,qty,name}.
- **equipment_loadouts.json**: `{ Meta:{regular:[],key_items:[],equipment:{weapon1-6,head,body,accessory1-4,shield,glider,food1-5,sphere_mod:{id,qty,name}}} }`.
- **inventory_loadouts.json**: `{ MetaInventory:{regular:[ItemRef],key_items:[ItemRef]} }`.
- **passive_loadouts.json**: `{ "<name>":[4 passive asset names] }`. 13 presets (Speedster, Immortality, Aegis, ...).

## i18n system (src/i18n/__init__.py, 67 lines)
- **8 languages**: en_US, zh_CN, ru_RU, fr_FR, es_ES, de_DE, ja_JP, ko_KR.
- `_RES: {lang: {key:text}}` — **ALL 8 loaded into memory simultaneously** by load_resources().
- `init_language(default='zh_CN')` — reads config.json lang, falls back to default. **NOTE: defaults to Chinese, not English.**
- `t(key, default=_DEF, **fmt)`: lookup `_RES[_LANG]` → fallback `_RES['en_US']` → return key itself (or default). Applies str.format(**fmt) if kwargs.
- `set_language(lang)`: validates against _SUPPORTED_LANGS, persists to config.json.
- Translation files: flat `{key:value}` dicts, ~1884 keys, keys are English strings (identity-mapped in en_US). `{placeholder}` formatting.
- `resources/i18n/config.json`: NOT a lang registry — mixed settings file (lang + showiconinlist + checkstartlogs + base.radius.* UI strings).

## Resource resolution (src/resource_resolver.py + boot_paths.py)
**Dual-mode**: works dev (running from source) and frozen (Nuitka/cx_Freeze).
- `_compute_binary_root()` (resource_resolver:5): checks sys._PST_BINARY_ROOT → sys.executable dir for resources/ → parent → walks up 5 dirs from __file__ → fallback. Cached in sys._PST_BINARY_ROOT.
- boot_paths.py: ROOT_DIR, SRC_DIR, RESOURCES_DIR, DATA_DIR, CONFIG_DIR, GUI_DIR(=resources/ui/themes), ASSETS_DIR.
- `_RESOURCE_MAP` (resource_resolver:44-99): legacy/flat name → canonical resources/ path aliases (logo.png→assets/branding/logo.png, etc). `_FLAT_KEYS` for quick matching.
- `resource_path(base_dir, *parts)`: joins parts, looks up _RESOURCE_MAP, returns os.path.join(base_dir,'resources',mapped).

## resources/ directory structure
```
resources/
├── assets/{branding(6 png), fonts(HackNerdFont.ttf), icons/{app(4), game(12 webp)}, maps(T_WorldMap.webp,T_TreeMap.webp)}
├── certs/cacert.pem
├── game_data/*.json(11) + icons/{elements(36),items(905),npcs(32),pals(456),passives(6),structures(533),technologies(460),ui(27)}
├── i18n/{__init__.py, config.json, icon(3 ico), <8 lang>.json}
├── readme/README.<7 locales>.md (NO en_US — root README.md is English)
├── tab_guide/{__init__.py, <8 short-code dirs: de/en/es/fr/ja/ko/ru/zh>/<10 html each>}
└── ui/themes/darkmode.qss
```
**Note inconsistency**: readme/ uses full locale codes (xx_XX), tab_guide/ uses short codes (xx).

## tab_guide (80 HTML files)
8 lang dirs × 10 sections: intro, players, guilds, bases, base_inventory, player_inventory, pal_editor, map, exclusions, tools. Rendered by TabGuideDialog.

## GOTCHAS
- `src/data/icon/` (paladius.ico, xenolord.ico) = **ORPHANED CRUFT** — zero code references. Safe to remove.
- friendship.json duplicates characters.json's friendship block.
- init_language defaults to zh_CN (Chinese) if config.json missing — could surprise non-Chinese users running fresh.
- i18n config.json is a mixed settings+strings file, not a pure language registry.