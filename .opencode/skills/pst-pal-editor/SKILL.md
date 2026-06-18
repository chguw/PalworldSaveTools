---
name: pst-pal-editor
description: The pal editing engine (edit_pals.py, 5454 lines) — pal data model (every SaveParameter field with type-wrapper shapes), editing operations, illegal pal detection, pal generation, container/slot model, game data binding, and the PalEditorWidget UI. Load when editing pal logic, stats, skills, IVs, containers, or illegal detection.
---

# PST Pal Editor Engine (edit_pals.py)

## Classes (23)
Key ones:
- **PalEditorWidget** (4367, QWidget) — main composition: partyPanel (5×PartySlotWidget) + palboxPanel (5×6 grid of 30 PalboxSlotWidget, 32 boxes) + PalInfoWidget. Hotkeys Q/E=box nav, F=focus info.
- **PalInfoWidget** (2046, QFrame) — THE detailed editor panel. Signal pal_data_changed. All click-edit handlers.
- **PalIcon** (315) / **PalCardWidget** (516) — grid cells with badges (boss/lucky/awake/dna/fav).
- **PartySlotWidget** (628) / **PalboxSlotWidget** (947) — slot widgets. Signals: clicked, rightClicked(slot,action), entered, left. Double-click→delete/add.
- **PalFrame** (5278) — legacy display frame; **holds global game-data maps** (_NAMEMAP, _PASSMAP, _SKILLMAP, _PASSRANK, _PASSFLAGS) via _load_maps(5300).
- **PalCreateDialog** (5075) — searchable species picker → _generate_pal_save_param → append to save+container+guild.
- **BulkSyncPalDialog** (4196) — copy _EDITABLE_KEYS from one pal to same-species pals.

## Pal data model (THE save structure)
Access path: `entry['value']['RawData']['value']['object']['SaveParameter']['value']` → flat dict of `{field: typed_wrapper}`.

**Type-wrapper shapes:**
- ByteProperty: `{id,type:'ByteProperty',value:{type:'None',value:<int>}}`
- IntProperty/Int64Property: `{id,type,value:<int>}`
- FloatProperty: `{id,type,value:<float>}`
- BoolProperty: `{id,type,value:<bool>}`
- NameProperty/StrProperty: `{id,type,value:<str>}`
- EnumProperty: `{id,type,value:{type:<EnumType>,value:<EnumStr>}}`
- StructProperty(FixedPoint64): HP stored ×1000: `{struct_type:'FixedPoint64',value:{Value:{value:<int>}}}`
- StructProperty(Guid): `{struct_type:'Guid',value:<uuid-str>}`
- ArrayProperty(Name/Enum): `{array_type,value:{values:[<str>...]}}`

**Editable fields + legal ranges:**
| Field | Wrapper | Range | Notes |
|---|---|---|---|
| CharacterID | NameProperty | valid asset | BOSS_ prefix = boss |
| Level | Byte/Int | 1-80 | illegal if >80 |
| Exp | Int64 | from pal_exp_table | _set_level sets both |
| Gender | Enum EPalGenderType | ::Male/::Female | toggle |
| NickName | StrProperty | str | |
| Hp/MaxHP | Struct FixedPoint64 (×1000) | | recalced via calculate_max_hp |
| Talent_HP/Talent_Shot/Talent_Defense | Byte | 0-100 (IVs) | illegal if >100 |
| Rank_HP/Rank_Attack/Rank_Defence/Rank_CraftSpeed | Byte | 0-20 (souls) | illegal if >20 |
| Rank | Byte | 1-5 (condenser stars) | illegal if >5 |
| FriendshipPoint | Int | 0-200000 | trust; thresholds from friendship.json |
| PassiveSkillList | Array(Name) | ≤4 | illegal if >4; _set_passive_skill caps [:4] |
| EquipWaza | Array(Enum EPalWazaID::) | ≤3 non-empty | illegal if >3; _set_active_skill caps [:3] |
| MasteredWaza | Array(Enum) | unbounded | learnable; _learn_all_skills fills |
| IsRarePal | Bool | | "lucky"/shiny |
| bIsAwakening | Bool | | awakened (×1.028 HP) |
| bImportedCharacter | Bool | | "DNA/imported" flag |
| FavoriteIndex | Byte | 0-3 | lock level |
| FullStomach | Float | ~0-300 | hunger |
| SanityValue | Float | 0-100 | SAN |
| SlotId | Struct PalCharacterSlotId | | {ContainerId:{ID:{Guid}}, SlotIndex:{Int}} |
| OwnerPlayerUId | Struct(Guid) | | owner |

**Stat formulas (utils.py):**
- calculate_max_hp(205): `floor(500 + 5·lvl + hp_scaling·0.5·lvl·(1+IV·0.3/100)·α)·(1+condenser_bonus)·(1+soul·0.03)·(1+trust·0.03)·awaken(1.028)` ×1000; α=1.087 if boss/lucky; condenser_bonus=(Rank-1)·0.05.
- calculate_shot_attack(218) / calculate_defense(239) / calculate_attack(229): similar scaling.

## Pal generation
**_generate_pal_save_param(character_id, nickname, owner_uid, container_id, slot_index, group_id=None)** (1808): builds full cmap entry. Defaults: Gender=Female, Talent_*=100 (maxed IVs), FullStomach=150, Hp=calculate_max_hp(lvl1,100iv). EquipWaza=[Unique_Roll] only for SheepBall. OwnedTime=638486453957560000. NO Level/Exp/Rank/souls given (game defaults).

**_register_pal_instance_to_guild(instance_id, group_id)** (1731): appends {guid,instance_id} to GroupSaveDataMap matching guild's individual_character_handle_ids.

**Create wiring** (PalCreateDialog._on_create 5235): resolve group_id from player's guild → compute slot ((box-1)*30+slot) → append cmap entry → append CharacterContainerSaveData slot → register to guild → increment PLAYER_PAL_COUNTS.

## Editing operations
All mutate self._raw in place then self._refresh() (4011).
| Op | Method(line) | Edits |
|---|---|---|
| Level | _set_level(3543) | Level,Exp,Hp,MaxHP |
| Stars/Rank | _on_star_click(3457) | Rank (cycles 1-5) |
| IVs | _on_talent_click(3575) | Talent_HP/Shot/Defense (0-100) |
| Souls | _on_soul_click(3591) | Rank_HP/Attack/Defence/CraftSpeed (0-20) |
| Gender | _on_gender_click(3446) | Gender enum |
| Nickname | _on_name_click(3431) | NickName |
| Boss toggle | _toggle_boss_raw(1613) | CharacterID (BOSS_ prefix), IsRarePal |
| Lucky toggle | _toggle_lucky_raw(1623) | IsRarePal, CharacterID |
| Awakened | _toggle_awake_raw(1631) | bIsAwakening |
| DNA/imported | _toggle_dna_raw(1633) | bImportedCharacter |
| Favorite/lock | _set_fav_raw(1635) | FavoriteIndex (0-3) |
| Trust | _on_trust_click(3520) | FriendshipPoint |
| Active skill | _set_active_skill(3666) | EquipWaza (caps [:3]) |
| Passive skill | _set_passive_skill(3679) | PassiveSkillList (caps [:4]) |
| Learn all | _learn_all_skills_raw(1560) | MasteredWaza(full)+EquipWaza(≤3 by power) |
| Work suitability | _set_work_suitability(1678) | GotWorkSuitabilityAddRankList |
| Max all | _max_stats_raw(1713) | IVs=100,souls=20,Rank=5,trust=200k,awake,WS=10,lvl=80 |
| Bulk sync | BulkSyncPalDialog._on_apply(4327) | copies _EDITABLE_KEYS to same-species |

**NO in-place species swap** — species change only via BOSS_ toggle or delete+create.
**NO move-between-containers** — transfer = delete+create. All DnD explicitly disabled (setAcceptDrops(False)).

_EDITABLE_KEYS(4195): Level,Exp,Gender,Talent_*,Rank_*,Rank,FriendshipPoint,IsRarePal,bIsAwakening,bImportedCharacter,FavoriteIndex,EquipWaza,MasteredWaza,PassiveSkillList,Hp,MaxHP,GotWorkSuitabilityAddRankList.

## Illegal pal detection (func_manager.py)
**check_is_illegal_pal(1637)** → (is_illegal, markers). Thresholds: Level>80, any IV>100, any Soul>20, Passives>4, ActiveSkills>3(non-empty), Rank>5.
**fix_illegal_pals_in_save(1857)**: clamps to ceilings (Level→80+Exp, IVs→100, souls→20, Rank→5, passives→[:4], active→[:3]). Processes CharacterSaveParameterMap + per-player *_dps.sav via ProcessPoolExecutor.
**remove_invalid_pals_from_save(881)**: drops cmap entries whose CharacterID ∉ characters.json pals∪npcs.
**remove_invalid_passives_from_save(1248)**: removes PassiveSkillList entries ∉ skills.json passives.

## Container/slot model
- Party container = player .sav SaveData.OtomoCharacterContainerId.ID; palbox = PalStorageContainerId.ID. DPS file = <uid>_dps.sav.
- CharacterContainerSaveData: {key:{ID:{Guid}}, value:{Slots:{values:[{SlotIndex,RawData:{instance_id}}]}}}.
- Palbox: 32 boxes × 30 slots (5×6). abs_index = (box-1)*30 + slot. Party: 5 slots.
- ContainerOwnership.build(cmap,container_data): majority-vote maps instance→container→owner. get_effective_owner(66) resolves base-worker pals.
- PLAYER_PAL_COUNTS[uid] tracks counts; incremented on create, decremented on delete.

## Game data binding
PalFrame._load_maps(5300): _NAMEMAP(pals+npcs), _PASSMAP(passives), _SKILLMAP(skills), _PAL_ZUKAN(zukan_index), _PASSRANK/_PASSFLAGS. All via data_manager.load_game_data_map(file,key) → {asset.lower():name}. Passives filtered: category=='SortDisplayable' AND no add_weapon/armor/accessory.
get_pal_base_data(cid)(93): lazy characters.json cache, backfills from boss_/gym variants.
Passive rank colors: _RANK_COLORS(839) maps -99/1/2/4/5; ≥5=world_tree overlay, ≥4=legend.