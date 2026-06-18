---
name: pst-gui-architecture
description: The palworld_aio GUI app architecture — startup lifecycle, MainWindow structure, the constants.py shared-state hub (global state pattern), the 13 managers (SaveManager through ZoneManager), data flow from load to save, and communication patterns. Load when working on app structure, managers, state, or wiring.
---

# PST GUI Architecture — palworld_aio

## App lifecycle (main.py)
Entry: `run_aio()` (main.py:106). Module-level bootstrap (4-75) resolves binary root, patches sys.path (palworld_coord, palsav, palworld_xgp_import, resources, palworld_aio), and if frozen sets multiprocessing exe + mocks stdin/stdout/stderr.

`run_aio()` has 3 branches:
1. **CLI/headless** (main.py:112-251): if argv[1] is a Level.sav path. Resets constants, backs up, sav_to_gvas_wrapper, builds caches. `-logs` generates scan logs; `-fix` runs 7 cleanup fns then wrapper_to_sav. **No GUI.**
2. **Loading popup test** (--test-loading-popup): shows LoadingPopup 5s.
3. **GUI mode** (264-274): init_language('en_US') → QApplication → excepthook→show_error_screen → Fusion style → MainWindow() → center_window → show → app.exec().

## MainWindow (ui/main_window.py:220)
`QMainWindow`, **frameless** (Qt.FramelessWindowHint), min 1448×800. Custom title-drag (mousePressEvent:747).

`__init__` order (221-252): set is_dark_mode/_is_refreshing/user_settings/lang_map → load_exclusions → _load_user_settings (CONFIG_DIR/user.cfg) → _setup_ui → _load_theme (ThemeManager.apply_global) → sidebar.set_active('tools') [DEFAULT TAB] → _setup_menus → _setup_connections → QTimer async update check → unlock_self_folder (Win) → StatusBarStream redirects stdout/stderr → setup_logging.

**UI composition** (_setup_ui:253-314): HeaderWidget (top) + QHBoxLayout body = SidebarWidget (left, 48px) + QSplitter[ QStackedWidget (center, 9 pages) | ResultsWidget (right dashboard, collapsible) ]. QStatusBar hidden (status sink only).

**9 stacked pages** (index → tab → setup):
0=Tools(ToolsTab), 1=BaseInventory(BaseInventoryTab), 2=PlayerInventory(PlayerInventoryTab), 3=PalEditor(PalEditorTab), 4=Players(inline SearchPanel+bulk), 5=Guilds(inline, 2 SearchPanels in splitter), 6=Bases(inline SearchPanel), 7=Map(MapTab), 8=Exclusions(inline, 3 SearchPanels).

**Signal wiring** (_setup_connections:554-556): ONLY `save_manager.load_finished→_on_load_finished` and `save_manager.save_finished→_on_save_finished`. Everything else is direct calls.

**refresh_all() (685-702)**: reentrancy-guarded (_is_refreshing) fan-out → re-pulls from constants/save_manager into every panel. F5 triggers it (keyPressEvent:2106).

**Action flow**: menu items → (label, handler) → QAction.triggered → handler → runs work via run_with_loading → refresh_all(). Context menus build ScrollableContextMenu/QMenu with _create_action.

## GLOBAL STATE HUB — constants.py (THE central pattern)
`constants.py` is a module of globals — every manager/tab does `from palworld_aio import constants` and reads/writes attributes directly. **No encapsulation, no classes.** This is how data flows between managers.

**Loaded save data:**
- `loaded_level_json` (50) — **THE** GvasFileWrapper holding decoded Level.sav. Single mutable source of truth. Its `['properties']['worldSaveData']['value']` (="wsd") is what everything edits.
- `current_save_path` (49) — path to save FOLDER (Level.sav + Players/).
- `original_loaded_level_json` (51) — snapshot for comparison/reset.
- `backup_save_path` (52).

**Guild/player caches:**
- `srcGuildMapping` (53) — MappingCacheObject (has .GroupSaveDataMap, .BaseCampMapping, ._worldSaveData).
- `base_guild_lookup` (55) — {base_id_str: {GuildName, GuildID}}.
- `player_levels` (54), `PLAYER_PAL_COUNTS` (58), `PLAYER_DETAILS_CACHE` (59), `PLAYER_REMAPS` (60), `selected_source_player` (64).

**Container lookups:** `container_lookup` (56) — lazy memoized {container_id_lower: container_dict}. `get_container_lookup()` (69-84) builds on demand; `invalidate_container_lookup()` (85-87) resets. **The cross-cutting invalidation call** — invoked by load, deletes, mutations, bulk ops.

**DPS/deletion state:** `files_to_delete` (57, set), `exclusions` (61, {players/guilds/bases} persisted to EXCLUSIONS_FILE), `death_bag_protected_instance_ids` (62), `death_bag_protected_container_ids` (63), `dps_executor` (65), `dps_futures` (66), `dps_tasks` (67).

**Static config** (4-48): theme colors (BG/GLASS/ACCENT/TEXT/etc), fonts (FONT_FAMILY), URLs (GITHUB_RAW_URL, GIT_REPO_URL, *_VERSION_URL), paths (ICON_PATH, EXCLUSIONS_FILE), path helpers (get_base_path/get_src_path/get_icon_path).

**CRITICAL GOTCHA — the reset block is triplicated**: on new load, ALL globals reset to defaults. This block is copy-pasted in 3 places: main.py:132-151, save_manager.py:52-71, and inline in reload_current_save. **Adding a new global requires editing all three.**

## The 13 managers

| Manager | Class/Module | File:line | Responsibility |
|---|---|---|---|
| **SaveManager** | `SaveManager(QObject)` singleton `save_manager` | managers/save_manager.py:27, inst:1019 | Load/save/reload Level.sav; build guild/player caches; scan logs. Signals: load_started/finished, save_started/finished. Methods: load_save(36), reload_current_save(122), save_changes(165), get_current_stats(800), get_players(819), get_guild_name_by_id(839), is_player_guild_leader(857). |
| **PlayerManager** | module of fns | managers/player_manager.py | Player mutations: rename_player(20), set_player_level(101)/adjust(319), unlock_viewing_cage(76), set_player_tech_points(132)/boss(154)/stats(173), add_all_effigies(230). |
| **GuildManager** | module of fns | managers/guild_manager.py | Guild restructuring: move_player_to_guild(9), rebuild_all_players_pals(157), rebuild_all_guilds(274). |
| **InventoryManager** | `ItemData`(16) `InventoryContainer`(199) `PlayerInventory`(258) | inventory/inventory_manager.py | Per-player inventory. ItemData caches items.json; PlayerInventory.load(266); add_item(449)/save(491). |
| **BaseInventoryManager** | `BaseInventoryManager` thread-safe singleton | inventory/base_inventory_manager.py:204 | Guild/base container browsing+editing; 2s debounce auto-save. get_instance(228), select_container(267), add_item(279)/remove(319)/set_count(339). |
| **BaseManager** | module of fns | managers/base_manager.py | Base blueprint export/import/clone: export_base_json(84), import_base_json(168). |
| **DynamicItemManager** | `DynamicItemManager` singleton | inventory/dynamic_item_manager.py:108 | Registry of dynamic items. create_dynamic_item(113), sync_with_save_data(181). |
| **StandardizedContainer** | `ContainerSlot`(7) `StandardizedContainer`(52) | inventory/standardized_container.py | Low-level parse/edit of one container's Slots array. _parse_slots(65), add_item(118)/remove(140), get_raw_slots(169). |
| **ContainerOwnership** | `ContainerOwnership` plain class | inventory/container_ownership.py:2 | Maps instance to container to effective owner. build(7), get_effective_owner(66). |
| **DataManager** | module of fns | managers/data_manager.py | Read queries + structural deletes. get_tick(62)/get_guilds(64)/get_bases(131); delete_guild(228)/delete_player(318)/delete_base_camp(156); load_exclusions(373). |
| **FuncManager** | module of ~50 fns (2657 lines) | managers/func_manager.py | Catch-all cleanup/repair. scan_and_protect_death_bags(17), delete_inactive_*(209/266), fix_missions(931), reset_*(990+), check_is_illegal_pal(1637), fix_illegal_pals_in_save(1857), unlock_all_*(1321/1352). |
| **ZoneManager** | module fns over `_zones` global(14) | managers/zone_manager.py | Exclusion-zone polygons/rects; point-in-zone tests. load_zones(15)/is_point_in_exclusion(121). |
| **BackupManager** | module of fns | managers/backup_manager.py | .pstbase/.pst7 compressed export/import. export_base_backup(65)/import(85). |

## Data flow (concrete trace)
**Load**: _load_save → save_manager.load_save → reset constants → backup → run_with_loading(load_task): sav_to_gvas_wrapper(p) → constants.loaded_level_json → invalidate_container_lookup → scan_and_protect_death_bags → dynamic_manager.sync → _build_player_levels → MappingCacheObject.get → srcGuildMapping → base_guild_lookup → _count_pals_found → PLAYER_PAL_COUNTS+logs → emit load_finished(True) → refresh_all.

**Edit**: tabs call managers directly. Managers mutate constants.loaded_level_json IN PLACE (by dict reference). Some also write player .sav files independently (PlayerInventory._save_player_sav, player_manager, guild_manager.move_player_to_guild).

**Save**: _save_changes → save_manager.save_changes → wrapper_to_sav(loaded_level_json, Level.sav) → serializes GvasFileWrapper.gvas_file → compress_gvas_to_sav → writes Level.sav → deletes files_to_delete UIDs → emit save_finished.

**KEY INSIGHT — mutable save data lives in TWO places:**
1. `constants.loaded_level_json` (world/Level.sav data) — mutated in place, flushed to disk only by save_changes.
2. Per-player .sav files — loaded independently, edited, written back IMMEDIATELY via gvasfile_to_sav (NOT deferred). So "Save Changes" persists only Level.sav; in-flight player edits are already on disk.

## Communication patterns
- **constants.py globals** = PRIMARY. All data flows through module globals, not parameters.
- **Direct function calls** = most manager invocations. No message bus/service locator.
- **Qt signals** = MINIMAL — only SaveManager↔MainWindow. UI widgets use signals internally.
- **Singletons**: BaseInventoryManager.get_instance(), get_dynamic_item_manager(), ItemData(), save_manager module instance.
- **Invalidation protocol**: invalidate_container_lookup() is the cross-cutting call; BaseInventoryManager.invalidate_cache(); MappingCacheObject._MappingCacheInstances.clear() on load.

**Coupling smells**: triplicated reset block; DataManager get_bases defined twice (dead code); main_window.py is a 2144-line god-class (~80 handlers); many managers write player .sav independently bypassing save_manager.