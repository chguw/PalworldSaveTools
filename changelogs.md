#2.0.8
- **Fixed `LocalData.sav` parsing** — `PalLocalWorldSaveGame` saves now load correctly (fixes parser under-consumption that skipped subsequent properties)
- **Bulk Sync (All Pals)** — sync stats/IVs/skills from any pal to all others across Party/Palbox/DPS. Work suitabilities are no longer copied cross-pal — each target keeps its natural suitabilities maxed to 10
- **Guild data fix** — `_u8_flag` → `role` migration prevents silent data loss on save
- **Fix Illegal Pals dialog** — per-player illegal pal counts, player selection, loading overlay, Select All/Deselect All
- **Restore Map** — also clears sky island cloud overlay so revealed map is fully visible
- **Fixed system32 crash** — all relative paths replaced with proper app data resolution; settings no longer lost in Nuitka onefile builds on restart
- **Open Data Folder** — menu item under AIO Tools opens app data directory in file manager
- **Removed auto-update** — kept version check + GitHub chip pulse; click still opens releases page
- **Work suitability icons** — fixed stale icon bug that let users inject illegal work suitabilities into any pal
- Bumped version to 2.0.8

#2.0.7
- **Per-item quantity cap** — non-stackable items (max_stack=1) stay limited to 1; all stackables uncapped to 999,999,999. Uses `max_stack` from generated game data
- **track user.cfg** — removed from `.gitignore`, now version-controlled
- **Abilities panel in Stats tab** — right side of Stats tab now shows relic abilities with toggles, icons, current values, and spinners. Supports edit and apply per player. Retranslates on language change
- **Translations: abilities keys** — added `inventory.abilities`, `inventory.abilities_apply`, `inventory.abilities_loaded`, `inventory.abilities_no_player_selected` in all 8 languages
- **NPC database expanded** — `update_npc_data()` now loads regular NPCs from `DT_PalCharacterIconDataTable.json` (not just boss NPCs). NPC count 33 → 369. Ammo Merchant and all trader/civilian variants now in DB
- **Sort no longer merges** — `_consolidate_container_slots` now just reorders by category/name. No stacking, no 9999 cap, gold and all items left untouched
- **Predator toggle** — paw icon button in pal editor info panel. Toggles `PREDATOR_` prefix. Filter toggle in Add New Pal and Bulk Pal Management dialogs. Red paw badge on thumbnail cards
- **Cheat mode** — bug icon toggle expands all caps to 255: level, IVs, souls, condenser rank, active skills (3→255), passive skills (4→255). Duplicate skills allowed, learnset bypassed. Skill pagination with mouse wheel scroll (3/page active, 4/page passive)
- **Max All Pals** — all 3 locations (pal editor, base inventory, menu→Functions) respect cheat mode caps. Double confirm dialog for menu version
- **Skill name fixes** — case-insensitive l10n lookup fixes "Thunder Rail" (was `Railbolt`). Partner skill names resolved from pal data
- **Add New Pal filter** — all filters removed: shows every entry in `_NAMEMAP`. Standard/Predator/Boss toggles all default to on
- Bumped version to 2.0.7
- **Bumped version to 2.0.7**

#2.0.6
- **Effigies now display in key items grid** — read from player `.sav` `RelicPossessNumMap` (bounty-token pattern)
- Edit/delete effigy count writes directly to `RelicPossessNumMap` (spendable at Statue of Power in-game)
- Add All Key Items prompts for effigy quantity per relic type
- Always show quantity badge on item/equip slots (count visible even at 1)
- XGP save picker (`pick_xgp_world`, `_load_xgp_save`) filters invalid saves via Level+LevelMeta+LocalData directory check
- Fixed `validate_xgp_save` `idx_path` resolution in `_load_xgp_save`
- `find_valid_saves` extracted as module-level function in `game_pass_save_fix.py`, reused in `restore_map.py`
- Theme/style consistency fixes for input dialogs
- Bumped version to `2.0.6`

#2.0.5
- `palsav` — fix `SetProperty` parsing + add missing type hint for `ValidatedStartPointIds`
- Pal editor — apply passive stat modifiers (MaxHP) to display and save writes
- Pal editor — scale current HP by passive multiplier for display consistency
- Breeding formula — align with palcalc: ceiling average for odd sums (`floor((A+B+1)/2)`)
- Update checker — use GitHub releases API instead of hardcoded `APP_VERSION`

#2.0.4
- Linux builds now produce a portable AppImage instead of a raw onefile binary
- Discord notifications upgraded to rich embeds with GitHub and Nexus Mods links
- Build caching per platform/version — same version skips rebuild entirely
- New save diagnostic script (`save_diagnostic.py`) detects orphaned players and save anomalies
- Nexus Mods upload now triggers automatically when a release is published (not during build)
- Changelog tracking system introduced (this file!)
- CI/CD: 5 workflows optimized with reusable composite actions, dist caching, hardened error handling
- Guild data format fixes for pre-2026 and 2026-07 compatibility
- Container type alignment with upstream GamePass format
- Added `encoded_raw_data` and `without_custom_type` archive helpers
- Restore Map: uses `run_with_loading` overlay for Steam and XGP clear-fog

#2.0.3
- Added `append_only` option to Build All & Release workflow (append files without editing release notes)
- Unified macOS builds on `macos_build.py`
- Cleaned up old workflow files (removed dependabot, release-build, test-build-macos)
- Merged macOS signing options into test-build workflow

#2.0.2
- 🎮 **GamePass save support**: load, edit, and save Xbox Game Pass save files with binary recompression
- Added draft test release option to Build All & Test workflow
- Release notes template with version and game version info
- Simplified release tags to just `v<version>` (always draft, publish manually)
- Preserve existing dynamics in `DynamicItemSaveData` during sync
- Fixed player file validation with translatable error messages
- Combined `fix_host_save` GUID swap + XGP save-back into single loading overlay
- Replaced hover frame with inline passive loadout preview

#2.0.1
- 🎵 **Discord notifications**: new workflow sends release announcements to Discord
- Map viewer: added base reassign to guild
- Unified macOS build script (`macos_build.py`)
- Build workflows consolidated and reorganized — cleaner CI/CD
- Fixed: NickName property when renaming a nameless player
- Fixed: base_guild_lookup key format mismatch after reassign
- Fixed: worker pal group_id and guild handles now update on base reassign

#2.0.0
- 🧬 **Breeding combos tab** with pal selector dialog and result filter search
- Refactored all right-click context menus to `ScrollableContextMenu`
- Performance optimization: replaced O(n*m) scans with pre-built maps in `character_transfer` and `fix_host_save`
- Slot injector: skip orphan containers with no matching player, restrict to guild-only players
- Numeric sorting for Level, Pals, Last Seen, Guild Level across all panels
- Map tab: fixed base child coordinate sorting
- Pal editor: show total pal count in Box/DPS headers
- Added `WaitCursor` to all heavy GUI operations
- Breeding formula documentation and rarity tiebreaker fixes
- Fixed parent lookup and `IgnoreCombi` pals children lookup

#1.0.0 — 1.1.88
These are the initial releases of Palworld Save Tools. Changelog tracking started from version 2.0.0 onward. For details on earlier releases, refer to the GitHub release history or Nexus Mods page.
