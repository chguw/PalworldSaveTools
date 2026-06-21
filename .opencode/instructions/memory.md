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

## Booth (ItemBooth / PalBooth) Inventory
- Booths stored in Level.sav `PalMapObjectConcreteModelSaveData`. ItemBooth → `RawData.trade_infos`, PalBooth → `CharacterContainerSaveData`.
- ItemBooth deletion: `_remove_item_from_slot` detects `booth_type` → `del` from `trade_infos` list ref (shared via removed `list()` copy in `get_booth_item_contents()`).
- PalBooth deletion: `_delete_base_pal` also cleans up the CharacterContainer slot by identity-matching `container_slot` in `values` list and `del`'ing it, then decrementing `SlotNum`.
- Booth pal entries carry `booth_char_container` dict ref from `get_booth_pal_contents()` for slot cleanup.
- `unlock_all_private_chests` zeros `private_lock_player_uid` on all booths (skip removed).

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

## Conventions
- PascalCase for tabs/dialogs, snake_case for modules/utilities
- `t('key', default=...)` for i18n; all UI widgets implement `refresh_labels()`
- `backup_whole_directory()` before every destructive operation
- UUID normalization: `str(uid).lower().replace('-', '')`
- Roundtrip fidelity: trailing/unknown bytes captured verbatim via `trailing_unknown_bytes`
- No DnD in pal editor (pal transfer = delete + create)
- Structural audit runs every pytest session (checks file pairing, import graph, resource paths)

## README Translation (`scripts/scrs/translate_readme.py`)
After editing `README.md` (esp. adding/renaming sections), **re-run** the script to regenerate all 7 translated files:
```
python scripts/scrs/translate_readme.py all
```
Key gotchas if translations appear broken:
- **Stale files, not script bug** — check if the source README changed before assuming the script is wrong. Regenerate first.
- **Logo/asset paths in `HEADER_SECTION`** — must be relative to `resources/readme/` (i.e. `../assets/branding/...`), not root-level. The English `README.md` lives at repo root and uses `resources/assets/branding/...`; the translated copies live one level deeper at `resources/readme/README.xx_XX.md`.
- **Team section content** — the script auto-translates the whole body, including The Palworld Team subheadings and bios. If they're in English, the translated files are just stale.
