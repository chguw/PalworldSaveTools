<!--
  INSTRUCTIONS: how auto-load memory works
  ─────────────────────────────────────────
  This file is listed in .opencode/opencode.jsonc under "instructions".
  That means its content is injected into every agent session automatically —
  no need to @-mention or manually load it.

  To auto-load ADDITIONAL files, add paths to the "instructions" array:
    "instructions": [
      ".opencode/instructions/memory.md",
      ".opencode/instructions/rules.md",
      "docs/STYLEGUIDE.md"
    ]

  To use SKILLS (on-demand deep dives) instead:
  - Put SKILL.md in .opencode/skills/<name>/SKILL.md
  - Agents will see it listed and can load with skill({ name: "..." })

  Edit this file freely — changes apply next session.
-->

# PST (PalworldSaveTools) v2.0.0

## Agent Rules
- **DO NOT commit or push without explicit instruction.** Wait for `"commit and push"`.
- Ask before making structural changes or adding files.
- Keep responses terse.

## Project Purpose
Desktop GUI + CLI toolkit for editing, repairing, transferring, and converting Palworld save files. Operates on `Level.sav`, per-player `.sav`, and Xbox GamePass (UWP) containers.

## Tech Stack
- **Language:** Python >=3.11
- **GUI:** PySide6 (Qt6), frameless QMainWindow, Fusion style
- **Package mgr:** `uv` (workspace), pip fallback
- **Build:** Nuitka (primary, --onefile), cx_Freeze + Inno Setup (Win installer)
- **Serialization:** `palsav-flex` (custom fork of palworld-save-tools) — UE GVAS binary
- **Compression:** Oodle (Kraken) via `palooz` (C++ ext), zlib fallback
- **Testing:** pytest (dynamic-import registry), structural audit harness
- **CI:** GitHub Actions (5 workflows)
- **i18n:** Custom flat-dict, 8 languages, English fallback

## Key Architecture
- **3-layer save pipeline:** SAV bytes <-> GVAS (UE struct) <-> Python dict/JSON
- **Global state hub:** `palworld_aio.constants` module globals — no DI, mutated in place
- **13 manager modules:** SaveManager (QObject singleton), PlayerManager, GuildManager, etc.
- **God-class MainWindow:** 2144 lines, 4 main tabs + 5 tab classes
- **Two write strategies:** Level.sav deferred (in-memory → explicit Save), player .savs immediate
- **CLI ≠ GUI divergence:** GUI skips decode for 6 large opaque properties (foliage, map-object transforms)

## Pal Editor — Bulk & Mass Actions (Jun 17 session)
### Context Menu (`editor/edit_pals.py`, `ui/tabs/base_inventory_tab.py`)
- `build_pal_context_menu` → `ScrollableContextMenu` (scrollable, gradient bg, border-radius 6px, QGraphicsDropShadowEffect)
- Keys dispatched via string-key `popup.exec_()` → `elif` chain in `contextMenuEvent` + `_on_slot_right_clicked` / `_on_pal_right_clicked`

### Clone Pal (`_clone_pal` in `editor/edit_pals.py`)
- Uses `_generate_pal_save_param` skeleton (same as add pal) → fresh `InstanceId`, correct `OwnerPlayerUId`, guild registration
- Then copies ALL source fields into skeleton via `for field in source_raw:` (skips `SlotId`/`OwnerPlayerUId`)
- Guild lookup uses `self.player_uid`, not source pal's owner
- Base pals clone (`base_inventory_tab.py` `elif action == 'clone'`) uses `copy.deepcopy` directly

### Bulk Operations (`_bulk_rename_pal`, `_bulk_feed_pal`, `_bulk_heal_pal`)
- `_gather_same_species_items(sender)` collects all same-species pals (party + palbox) by `CharacterID` (strips `boss_` prefix)
- `FramelessDialog` + `QScrollArea` + checkbox list per pal
- `_bulk_feed_pal`: `FullStomach→max`, `SanityValue→100`, clears `WorkerSick`/`PhysicalHealth`/`HungerType`/`FoodWithStatusEffect`/`Tiemr_FoodWithStatusEffect`/`FoodRegeneEffectInfo`
- `_bulk_heal_pal`: same + HP restore to max (via `calculate_max_hp`)

### Restore All / Max All Buttons
- **edit_pals.py**: Two buttons in palbox header (right of stretch, before ◀▶). Apply to party + ALL palbox pages (all 960 slots, not just current page).
- **base_inventory_tab.py**: Two buttons in page_row (leftmost, before ◀▶). Apply to all base worker pals.
- Both methods clear selection highlight + show No Pal Data after operation.
- Button text refreshed via `refresh_labels()`.
- Visibility toggled in show/hide blocks.
- **Restore All**: HP/FullStomach/SanityValue restore + sickness cleanup.
- **Max All**: Two-phase — first max stats (Talents(100)/Ranks(20)/Condenser(5)/Friendship(200k)/Awakening/Level 80/Work Suitabilities(10)), then restore (same as Restore All). HP recalc in phase 2 uses the now-maxed stats so it's correct on first click.
- Uses `_set_work_suitability` for work suitability maxing.
- `_generate_pal_save_param` (add pal + clone skeleton) now sets `FullStomach` from pal base data + `SanityValue` 100.

### i18n Key Pattern
- Bulk: `edit_pals.bulk_heal_desc`, `edit_pals.restore_all`/`_confirm`/`_success`, `edit_pals.max_all`/`_confirm`/`_success`
- Base: `base_inventory.restore_all`/`_confirm`/`_success`, `base_inventory.max_all`/`_confirm`/`_success`
- Script at `scripts/scrs/add_translation_keys.py` — add keys to `NEW_TRANSLATIONS` dict, then run

### Selection Highlight Gotchas
- `_BasePalIcon._build()` saves `was_selected = self.selected` at start, re-applies `slot_selected` at end if True
- Simply setting `_selected_idx = -1` does NOT clear the visual highlight
- Must call `widget.set_selected(False)` on the old widget BEFORE any `_rebuild()` or `update_display()`
- Same pattern in edit_pals.py: `_clear_party_highlight()` + `_clear_palbox_highlight()` before `set_clicked_pal(None)`

## Game Data ETL — Structure Icons & Descriptions (Jun 20 session)
### `scripts/scrs/update_game_data.py`
- **Structure descs**: `resolve_struct_desc` reads `DT_BuildObjectDescText_Common.json` + CI fallback map. Resolves `BUILDOBJECT_DESC_<id>` per struct. 545/1089 with descs. Resolves rich text tags.
- **Structure icon CI fallback**: case-insensitive icon row lookup for structures. 11 more icons.
- **Tech desc CI fallback**: `tech_desc_l10n_ci`, `build_desc_l10n_ci`, `item_desc_l10n_ci` maps used in `update_technology_data()`. Fixes ItemBooth (key `BUILDOBJECT_DESC_ITEMBooth` vs `BUILDOBJECT_DESC_ItemBooth`).
- **Unknown icon fallback**: copies `T_icon_unknown.webp` to `icons/structures/` on first missing icon; subsequent entries get that fallback path.
- **Dead icon path cleanup**: structures with no icon file on disk store `''` instead of broken fallback.
- **Hardcoded exclusion removal**: removed 27-struct exclusion list from `_load_structure_data()` — desc filter catches all junk.
- **Desc filters**: Universal `desc.lower() not in ('en text','en_text','none','-','---')` applied in GuildItemPickerDialog, GuildStructurePickerDialog, ItemPickerDialog, PlayerTechnologyActionDialog, PlayerItemActionDialog.

### Grenade Quantity Fix
- `ItemPickerDialog` + `PlayerItemActionDialog`: exempt `EPalItemTypeB::WeaponThrowObject` from `SINGLETON_TYPE_A` check. Type B stored in `Qt.UserRole+5`.
- `inventory_tab.py` equip slots: context menu shows "Edit Quantity" for `slot_type in ('food', 'weapon')` (was `'food'` only). `_add_to_equip_slot` passes `hide_quantity=slot_type not in ('food', 'weapon')` — picker handles grenade exemption internally.

### NPC Work Suitabilities (this session)
- **Missing data source**: `update_npc_data()` never loaded `DT_PalHumanParameter.json` (433 entries, each with 13 `WorkSuitability_*` fields + stats). Only loaded icon/name from `DT_PalBossNPCIcon.json`.
- **Fix**: `update_npc_data()` now loads human params and injects `work_suitabilities` + `stats` into each NPC entry.
- **Pal array merge**: `update_pal_descriptions()` also loads human params and merges WS/stats into elementless `pals[]` entries (humans in monster params table). 369/384 human pal entries gain non-zero WS.
- **Lookup fix**: `data.py` `_load_pal_base_data()` now also caches `npcs[]` array entries as fallback (not overwriting `pals[]`).
- **Result**: Human NPCs (Soldiers, Hunters, Believers, Traders, etc.) now display work suitabilities in pal editor and base inventory.

## Key Items — Double-Click Delete Fix (Jun 23 session)
### Problem
`InventoryContainer.get_items()` / `get_slot_at()` omitted `container_type` from returned dicts. `_delete_item_direct` fell back to `'main'` for all items → key items double-click tried to delete from wrong container (silent no-op). Bounty tokens (synthetic `is_bounty=True`) were also not handled by `_delete_item_direct` (context menu `_delete_item` had the check, double-click didn't).

### Fix
- `InventoryContainer.__init__` accepts `container_type` param, stored as `self._container_type`
- `get_items()` and `get_slot_at()` include `'container_type': self._container_type` in returned dicts
- `PlayerInventory.load()` passes `container_type=` when creating containers
- `_delete_item_direct` now checks `is_bounty` first → calls `remove_bounty_item()` for synthetic tokens, else removes from container with correct `container_type`

Files: `inventory/inventory_manager.py:200,207,214,246,327`, `ui/tabs/inventory_tab.py:1567`

## Level.sav Debug — Orphaned BossReward Containers (Jun 23 session)
### CLI Usage
```
uv run python -m palsav.cli convert --to-json --output out.json in.sav
```

### ViperGeek save analysis (`OfficialWorld` save)
- **UID**: `00000000-0000-0000-0000-000000000001` (placeholder admin UID, all zeros+1)
- **All 6 player containers** (main/key/weapons/armor/foodbag/drop): zero `BossDefeatReward_*` items
- **23 NormalBossDefeatFlag entries**: NONE match any `boss_mapping.json` spawner key → `_bounty_tokens` dict empty → PST shows no synthetic tokens
- **Game shows items anyway**: game generates them from flag keys PST's mapping doesn't cover (e.g. `81_1_grass_FBOSS_11` not in mapping, but `81_1_grass_FBOSS_14` for Anubis is)

### Legacy Container `419aef792ddd`
- World container (GroupId=0, no guild/player owner), 200 slots
- Holds 4 old bugged `BossDefeatReward_*` items from v1.1.88 era (when items were stored in containers, not flags)
- Not accessible from any Player Inventory tab → only shows in Base Inventory tab
- Other 8 user-reported tokens (Azurobe, Jetragon, Menasting Terra, Bushi, Dazzi Noct, Faleris Aqua, Gildane, Nyafia) don't exist as items anywhere in Level.sav

## Bounty Tokens & Boss Defeat Flags (Jun 22 session)
### Storage (player `.sav` only)
Bounty tokens (`BossDefeatReward_*`) are **not** stored as items in Level.sav containers. They're tracked purely via the player `.sav`:
- `RecordData.NormalBossDefeatFlag` — `MapProperty` of `{boss_key: True}`
- `RecordData.BossDefeatExpBonusTableIndex` — total boss kill count int
- `bossTechnologyPoint` — total unique boss types int
- `RecordData.FindAreaFlagMap` — discovered area flags (some bosses also require area discovery)

**Never add bounty tokens to Level.sav containers** — the game reads them from player save only and shows duplicates if also in container.

### Boss Mapping (`resources/game_data/boss_mapping.json`)
Generated by `update_game_data.py:update_boss_mapping()` using two-phase approach:
- **Phase 1:** `UI/DT_BossSpawnerLoactionData.json` — authoritative field boss flag mapping (89 items)
- **Phase 2:** `Spawner/DT_PalWildSpawner.json` — fallback for sealed realm bosses (10 items)
- 5 expected unmatched: `BossRush`, `FlowerPrince`, `Mothman`, `PyramidTurtle`/`_Neutral` (dead entries)

Each item has **exactly 1 key** (the unique boss spawner ID). Only `BOSS_`-prefixed `Pal_1` entries are used.

### Shared key issue
`worldtree_9_55_WorldTreeAura` is shared by `HerculesBeetle` (Warsect) and `LazyDragon_Electric` (Relaxaurus). The reverse map (`_build_reverse_boss_map`) now maps `{key: [item_id1, item_id2]}` (multi-value) so both items appear in `_bounty_tokens`.

### API
- `PlayerInventory.add_item()` — early return for `BossDefeatReward_*`: skips container, calls `_ensure_boss_defeat_flags` + `_save_player_sav` + `_load_bounty_tokens`
- `PlayerInventory.remove_item()` — cleans boss flags from player save, still removes from container for old-save migration
- `PlayerInventory.update_quantity()` — now calls `_save_player_sav()`
- `PlayerInventory._cleanup_boss_defeat_flags()` — removes ALL mapping keys for given item_id
- `PlayerInventory.get_bounty_token_items()` — returns synthetic slot entries for key items grid
- `remove_item_from_players()` — bulk path calls `_cleanup_boss_defeat_flags_in_save_data()`
- `add_item_to_players()` — bulk path implemented (was a stub returning 0)

### UI display
Bounty tokens merge into the key items grid via `_refresh_display()` → `get_bounty_token_items(existing_slot_count)`. Synthetic slots use slot indices starting after the last occupied container slot. Marked with `is_bounty: True`.

### Known game behavior (current beta)
When loading a save with externally-added `NormalBossDefeatFlag` entries, the game may **regenerate/wipe** the entire field if it detects inconsistency. This is a game-side issue, not a PST bug. Workaround: load save in game first, then re-add bounties in PST.

### CLI cross-platform fix (`palsav/cli.py`)
`os.execv` replaced with `subprocess.run` fallback for non-Unix platforms (Windows). PYTHONHASHSEED re-exec works on all OS now.

## Base Inventory — Structure Filter (Jun 23 session)
### Concept
- **Item filter**: Guilds → Bases → Containers → Items (filtered in grid)
- **Structure filter**: Guilds → Bases → Structure instances (replaces container list)
- The two filters are mutually exclusive: activating one clears the other

### Location
`base_inventory_tab.py:BaseInventoryTab`, methods:
- `_show_structure_picker()`, `_on_structure_action_selected()` — dialog + state
- `_filter_guilds_and_bases_by_structure()` — calls `find_structure_locations_efficient()`, stores `_structure_locations`, filters `_guilds_data`
- `_load_bases_for_guild_filtered_by_structure()` — filters bases using `_structure_locations[guild_key]`
- `_load_structures_for_base()` — replaces container list when structure filter active:
  - **Container-type structures** (ItemChest_04, Fridge, Booth): loads all containers via `load_containers_for_base()`, filters to those with matching `map_object_id`, shown as normal containers with items/slots in grid
  - **Non-container structures** (AncientFarmBlock, Monitoring Stand, decorations): no matching containers → shows structure instance entries via `add_structure_entry()` (icon + name, grid empty)
- `_clear_structure_filter()` — resets state, calls `_load_guilds()` then `_on_guild_changed()` to restore selection

### `ContainerListWidget` additions
- `add_structure_entry(structure_name, instance_id, structure_asset)` — adds a tree item with icon from `world.json` + structure name + truncated ID

### Data flow
- `_structure_locations`: `{guild_key: {base_key: [instance_id, ...]}}` (same shape as `_item_locations`)
- `find_structure_locations_efficient(asset)` iterates `MapObjectSaveData.values`, matches `MapObjectId`, checks `base_camp_id_belong_to`, resolves guild from `base_guild_lookup`
- UUID keys used without hyphens throughout for matching

## Booth (ItemBooth / PalBooth) Inventory
- Booths stored in Level.sav `PalMapObjectConcreteModelSaveData`. ItemBooth → `RawData.trade_infos`, PalBooth → `CharacterContainerSaveData`.
- ItemBooth deletion: `_remove_item_from_slot` detects `booth_type` → `del` from `trade_infos` list ref (shared via removed `list()` copy in `get_booth_item_contents()`).
- PalBooth deletion: `_delete_base_pal` also cleans up the CharacterContainer slot by identity-matching `container_slot` in `values` list and `del`'ing it, then decrementing `SlotNum`.
- Booth pal entries carry `booth_char_container` dict ref from `get_booth_pal_contents()` for slot cleanup.
- `unlock_all_private_chests` zeros `private_lock_player_uid` on all booths (skip removed).

### Clear Button Fix (Jun 23 session)
- **Problem**: `_clear_container` only called `manager.clear_container()` → cleared regular container items (payment items) but not booth-specific data. Booth trade infos (ItemBooth) or CharacterContainer+CharacterSaveParameterMap (PalBooth) were left untouched.
- **Fix**: `_clear_container` now checks `booth_type`:
  - `PalMapObjectItemBoothModel`: `booth_trade_infos.clear()`
  - `PalMapObjectPalBoothModel`: calls `_clear_pal_booth_slots()` helper
- `_clear_pal_booth_slots`: finds CharacterContainer by `booth_char_container_id`, iterates all slots to remove matching `CharacterSaveParameterMap` entries by `instance_id`, then clears slots + resets `SlotNum` to 0
- After booth-specific clear, calls `manager.clear_container()` for payment items, then `_on_container_selected()` to refresh full view
- `_on_container_selected` now calls `self.inventory_grid.refresh_labels()` in both non-booth `else` branches so tab_label resets from "Booth: ..." back to default when switching away from booth view

## Guild Binary Format — V1_MARKER Fix (Jun 21 session)
### Location: `src/palsav/palsav/rawdata/group.py` — `decode_bytes()` / `encode_bytes()`
### Problem
Newer Palworld versions (post-Feybreak?) prepend ~480 bytes of data **before** the known `V1_MARKER` (`02 00 00 00 02 03 00 00 00 00`) in the guild binary tail. The old code checked `post_unk2[:10] == V1_MARKER`, missing the marker when it wasn't at offset 0. The `try/except` at line 76 silently caught the parse failure and set `players: []`.

### Fix (commit `667370dd`)
- **Decode**: Changed `post_unk2[:10] == V1_MARKER` → `post_unk2.find(V1_MARKER) >= 0`. Pre-marker bytes saved as `_pre_v1_bytes` (bytes) for roundtrip. `_raw_tail` fallback uses `original_tail` (unmodified) so pre-V1 data isn't lost on error.
- **Encode**: Writes `_pre_v1_bytes` before the V1_MARKER bytes when present.
- **Roundtrip**: `_pre_v1_bytes` stored as raw `bytes`, written verbatim with `writer.write()`.

### Save Compatibility Verified
| Save | Pre-V1 bytes | Players parsed | CSPM match |
|------|-------------|----------------|------------|
| PylarLatest | 480B | 2 (Pylar, Primarina) | ✅ 2/2 |
| PylarOld | 0 (at offset 0) | 3 | 3/4 (1 player no guild) |
| Tenacity | 0 (at offset 0) | 2 (Mohri, Avitius) | 2/10 (others in unparsed guild) |
| EntUpdated | 0 (at offset 0) | 1 (Ent) | ✅ 1/1 |

### Debug Pattern
To inspect guild binary tail: search for `V1_MARKER` in `_raw_tail` bytes. If found at offset > 0, guild format was extended. If `_raw_tail` is set and V1_MARKER absent, there's a different format mismatch.

### `_u8_flag` — Spurious Flag Byte Bug (Jun 22 session)
**Problem** (`group.py:decode_bytes`): The decoder unconditionally read a `_u8_flag` byte after each player entry (unless at EOF). In the **pre-V1_MARKER** format, these flag bytes don't exist — the byte after each player's fstring is the **first byte of the next player's GUID**. This caused a 1-byte shift per player:
- **The Good Team** (5 players, ViperGeek's guild): 5× shift → parser overran buffer → `except` caught → `_raw_tail` fallback, **0 players** parsed
- **Maifest Destiny** (2 players): 1× shift → player 1 consumed `0x81` as flag=129 → player 2 GUID shifted → corrupted name/UID

**Fix** (`group.py:71`): Changed `if not sub.eof():` → `if group_data.get('_has_v1_marker') and not sub.eof():`. Only reads `_u8_flag` when V1_MARKER was present. Encoder already conditional (`if '_u8_flag' in p`), so roundtrip preserved for both formats.

**Diagnosis tools**: Convert Level.sav to JSON, load with `json_tools.load()`, inspect `_raw_tail` hex. Parsing same bytes with/without flag byte confirms alignment.

## Guild Manager — `_u8_flag` Guild Move Bug (Jun 21 session)
### Location: `src/palworld_aio/managers/guild_manager.py` — `move_player_to_guild()`
### Problem
When a guild admin is moved to another guild via `move_player_to_guild()`, their player entry carries the old `_u8_flag=1` (guild master rank byte). After the move, the target guild ends up with multiple players all having `_u8_flag=1`, making the game treat them all as guild masters. Players can't leave the guild or perform guild actions.

### Evidence (PylarOld save)
| Guild | Players | `_u8_flag` |
|-------|---------|-----------|
| PutaNation | Pylar | 1 (admin) |
| Unnamed Guild | Roxx | 1 (admin) |
| Unnamed Guild | DefNotPylar | 1 (admin) |

All were flagged as admin even though only Pylar was `admin_player_uid`.

### Fix (commit `343d5abb`)
- Reset `found['_u8_flag'] = 3` after appending the moved player to the target guild.
- Only set `found['_u8_flag'] = 1` if the player is explicitly elected admin via the empty-admin fallback (`admin_player_uid not in target player set`).
- Values inferred from save data: `1` = guild master/admin, `3` = regular member. Value `2` never observed.

### `make_member_leader` Fix (commit `36522918`)
- Previously only set `admin_player_uid`, leaving stale `_u8_flag` on all player entries. Promoted player kept old flag (usually 3), others might still have 1 from old admin role.
- Now iterates all guild players: sets `_u8_flag=1` on new leader, `_u8_flag=3` on everyone else.

## Conventions
- PascalCase for tabs/dialogs, snake_case for modules/utilities
- `t('key', default=...)` for i18n; all UI widgets implement `refresh_labels()`
- `backup_whole_directory()` before every destructive operation
- UUID normalization: `str(uid).lower().replace('-', '')`
- Roundtrip fidelity: trailing/unknown bytes captured verbatim via `trailing_unknown_bytes`
- No DnD in pal editor (pal transfer = delete + create)
- Structural audit runs every pytest session (checks file pairing, import graph, resource paths)

## Cross-Tab Player Selection Sync (Jun 22 session)
- **Problem**: Selecting a player in Pal Editor or Player Inventory tab only affected that tab.
- **Solution**: `select_player(uid, name, display)` / `clear_player()` on both `PalEditorTab` and `PlayerInventoryTab`. Each calls the other's method via `self.parent_window.<other_tab>.<method>()`.
- **Guard**: `_syncing` bool on each tab prevents re-entrant cross-calls → no infinite loops.
- **Refresh preservation**: Both `refresh()` methods now save `prev_uid` before rebuilding player list, then re-select if player still exists. Level edits no longer drop the selection.
- **Entry points wired**:
  - `_open_player_popup()` (both tabs) — user clicks "Select Player..."
  - `load_player()` (inventory) — called from Players tab right-click → "Edit Player Inventory"
  - `refresh()` (both) — called during `refresh_all()`; preserves selection across rebuilds
- **Files**: `ui/tabs/pal_editor_tab.py:59-72` (select_player/clear_player), `ui/tabs/inventory_tab.py:1049-1065` (select_player/clear_player), `151-163` (refresh preservation)

## Stat Formula — Game-Verified (Jun 25 session)
### Location: `src/palworld_aio/utils.py` (5 calculate_* functions)
### Formula Structure (from in-game breakdowns on 3 maxed pals):
```
base        = additive_const + floor(scaling × K × level × (1+IV) × (1+condenser))
subtotal    = base + trust_bonus + awakening_bonus     # additive
final       = floor(subtotal × (1+soul) × (1+passive)) # multiplicative
```

### Per-Stat Constants:
| Stat | Additive | K constant | Scaling source | Condenser |
|------|----------|------------|----------------|-----------|
| HP | `500 + 5×level` | 0.5 | `stats.hp` | `×1.cond` after base |
| ATK | `1.5×level` | 0.075 | `stats.shot_attack` | `×(1+cond)` in base |
| DEF | `0.75×level` | 0.075 | `scaling.defense` | `×(1+cond)` in base |
| WS | `70 + craft_speed×level//280` | — | `stats.craft_speed` | — |

### Condenser bonus: `(rank-1) × 0.05` for ALL stats (ATK/DEF was flat 5% bug)
### No alpha scaling for boss/lucky (multiplier is in monster's Hp stat — ratio 1.2×)
### Lucky non-boss pals: alpha=1.2 applied to hp_scaling (e.g. Anubis lucky: 120×1.2=144)

### Trust/Awake auto-formulas (approximate, need more data):
- **HP trust**: `int(level × rank × (hp_scaling/82.3 - f_hp×0.0181) + 0.5)`
- **ATK trust**: `level × rank × f_atk / 8.6`
- **DEF trust**: `level × rank × f_def / 8.5`
- **Awake (all)**: `base × 0.092` (ATK 0.092, DEF 0.094, HP 0.089)

### Passive Skill Parsing (`pal_info_display.py`):
- Only counts effects with target `ToSelf` or `ToSelfAndTrainer` (skips `ToTrainer`-only like Vanguard/Stronghold Strategist)
- `efftype1..4` now extracted correctly in ETL (previously missing `efftype4`)
- Condenser DOES NOT amplify passives (the +16% was from Dogen Emblem acc)

### Verified against game values:
| Pal | HP | ATK | DEF | WS |
|-----|-----|-----|-----|-----|
| Jetragon (lucky boss) | 18982 vs 18979 (+3) | 3175 ✅ | 2791 ✅ | 157 ✅ |
| Anubis (lucky) | 19332 vs 19337 (-5) | 2524 vs 2526 (-2) | 2118 vs 2116 (+2) | 494 ✅ |
| Solenne (lucky boss) | 18228 vs 18619 (-391) | 2726 vs 2722 (+4) | 2840 vs 2839 (+1) | ~157 |

### ETL Bug Fixed (`scripts/scrs/update_game_data.py`):
- `update_passive_data()` was missing `EffectType4` read → `efftype4` never written to output (caused MutationPal_Mutant's Defense+25% to be invisible)
- `TargetType1-4` fields now extracted and written to skills.json for target filtering

## README Translation (`scripts/scrs/translate_readme.py`)
After editing `README.md` (esp. adding/renaming sections), **re-run** the script to regenerate all 7 translated files:
```
python scripts/scrs/translate_readme.py all
```
Key gotchas if translations appear broken:
- **Stale files, not script bug** — check if the source README changed before assuming the script is wrong. Regenerate first.
- **Logo/asset paths in `HEADER_SECTION`** — must be relative to `resources/readme/` (i.e. `../assets/branding/...`), not root-level. The English `README.md` lives at repo root and uses `resources/assets/branding/...`; the translated copies live one level deeper at `resources/readme/README.xx_XX.md`.
- **Team section content** — the script auto-translates the whole body, including The Palworld Team subheadings and bios. If they're in English, the translated files are just stale.
