---
name: pst-codebase
description: PalworldSaveTools (PST) architecture map — repo layout, entry chain, the palsav SAV<->GVAS<->JSON pipeline, the palworld_aio GUI structure, game data locations, and the custom pytest dynamic-import registry. Load FIRST whenever working anywhere in this repo so you orient on real structure, not guesses.
---

# PalworldSaveTools (PST) — Codebase Map

**Maintain this as the source of truth.** When the layout changes, patch this skill. Project: PalworldSaveTools v2.0.0, GitHub `deadafdudecomputers/PalworldSaveTools`, author **Pylar**. MIT. PySide6 desktop GUI + CLI save tools for Palworld.

Active branch (cyrix's dev): `upd/ProjRefactor`. Python >=3.11. Package mgr: **uv** (workspace). venv at `.venv`.

## Entry chain
1. `start.py` (repo root) — creates/ensures uv venv at `.venv`, deletes stale `uv.lock`, then runs `src/bootup.py` with the venv python.
2. `src/bootup.py` — splash screen + dependency/version checks; launches the GUI. **GUI deps are optional**: set env `PST_NO_GUI=1` (or any truthy value) to skip PySide6 import — essential for headless/test/CI runs. `PST_DEBUG=1` enables verbose bootup logging.
3. `src/palworld_aio/main.py` — the actual PySide6 "All-in-One" app + `ui/main_window.py`.

Bootup path constants live in `src/boot_paths.py`: `ROOT_DIR`, `CONFIG_DIR`, `RESOURCES_DIR`, `GUI_DIR`.

## Source layout (`src/`)
```
src/
  palsav/            # SERIALIZATION ENGINE (workspace pkg "palsav-flex")
    palsav/
      core.py            # decompress_sav_to_gvas / compress_gvas_to_sav
      gvas.py            # GvasFile.read/load/write/dump  (UE GVAS container)
      archive.py         # FArchiveReader / FArchiveWriter (UE binary archive)
      paltypes.py        # PALWORLD_CUSTOM_PROPERTIES, PALWORLD_TYPE_HINTS
      json_tools.py      # orjson-backed dump/load
      _cityhash.py       # city hash for save integrity
      compressor/        # oozlib (Oodle, default) + zlib backends, enums
      rawdata/           # PER-ENTITY raw decoders (character, group, base_camp,
                         #   map_data, map_model, item_container, work*, etc.)
      commands/          # auto_update, backup, convert, diag, resave_test,
                         #   roundtrip_validation  (CLI subcommands)
      cli.py             # `palsav` CLI entry  (SAV<->JSON)
  palworld_aio/      # THE GUI APP ("All-in-One Tools") — RESTRUCTURED into sub-packages
    main.py             # app entry  ->  ui/main_window.py
    constants.py        # global state hub (50+ importers, STAYS at root)
    utils.py            # shared helpers (STAYS at root, external importers)
    updater.py          # update checking
    managers/           # ★ business logic (operates on constants.loaded_level_json)
      save_manager, player_manager, guild_manager, base_manager,
      data_manager, func_manager, zone_manager, backup_manager
    inventory/          # ★ inventory + container subsystem
      inventory_manager, base_inventory_manager, standardized_container,
      dynamic_item_manager, dynamic_item, container_ownership
    editor/             # ★ pal + world editing engine
      edit_pals (5454 LOC), dialogs, worldoption_editor
    map/                # map generation
      map_generator
    ui/                 # views (sub-organized)
      main_window.py    # QMainWindow god-class (2144 lines)
      tabs/             # tools_tab, base_inventory_tab, inventory_tab, pal_editor_tab, map_tab, container_ids_tab
      dialogs/          # container_selector_dialog, player_item_dialog, player_pal_dialog, player_technology_dialog, skill_picker, tab_guide_dialog
      chrome/           # header_widget, sidebar_widget, results_widget, styled_combo, styles (ThemeManager), menus
      map_view/         # map_view (MapGraphicsView), map_markers, map_items, map_effects
    widgets/            # reusable Qt widgets (unchanged): search_panel, stats_panel, menu_popup, scrollable_context_menu, hover overlays, collapsible_splitter, loading_popup, tree_widgets
  palworld_toolsets/    # CLI tools: fix_host_save, game_pass_save_fix,
                        #   character_transfer, convert_generic, convertids,
                        #   modify_save, restore_map, slot_injector, xgp_save_extract
  palworld_xgp_import/  # Xbox Game Pass save import (gamepass_manager, container_types)
  palworld_coord/       # coordinate transforms
  (top-level) bootup.py, boot_paths.py, common.py, palobject.py,
            qt_imports.py, resource_resolver.py, path_setup.py,
            loading_manager.py, import_libs.py, i18n/__init__.py, nerd_btn.py
```

## The palsav pipeline (the heart of the project)
`SAV bytes  <->  GVAS (UE struct)  <->  Python dict/JSON`
- **SAV->JSON**: `decompress_sav_to_gvas(raw)` -> `GvasFile.read(gvas, PALWORLD_TYPE_HINTS, PALWORLD_CUSTOM_PROPERTIES)` -> `.dump()` -> `json_tools.dump`.
- **JSON->SAV**: `json_tools.load` -> `GvasFile.load(data)` -> `.write(PALWORLD_CUSTOM_PROPERTIES)` -> `compress_gvas_to_sav(gvas_bytes, compression_level)`.
- `PALWORLD_CUSTOM_PROPERTIES` maps property type names -> (read_fn, write_fn) decoders. The `rawdata/` modules implement the per-entity decode/encode for each Palworld property type (CharacterSaveParameterMap, GroupSaveDataMap, MapObjectSaveData, ItemContainerSaveData, work collections, base camps, map models, etc.).
- Default compression is **Oodle** (`compressor/oozlib.py`, via pyoozle). zlib is the fallback (`--library zlib`).
- `orjson` for speed; GC is disabled during parsing then re-enabled.

## Resources & data
- `resources/game_data/*.json` — static game reference: `characters` (pal data + passives), `items`, `skills`, `boss_mapping`, `pal_exp_table`, `friendship`, `relic_data`, `reference_unlock_data`, `uidata`, `world`, `world_map_areas`.
- `resources/i18n/*.json` — 8 langs (en_US, zh_CN, de_DE, es_ES, fr_FR, ru_RU, ja_JP, ko_KR); `resources/i18n/config.json` is the lang registry. i18n loader at `src/i18n/__init__.py`.
- `src/data/configs/*.json` — app presets: `base_inventory_loadouts`, `equipment_loadouts`, `inventory_loadouts`, `passive_loadouts`, `zone_exclusions`, plus `config.json`.
- `resources/tab_guide/` — in-app help. `resources/readme/` — localized READMEs.

## Testing (cyrix's preferred route)
**Custom dynamic-import registry** — tests NEVER hardcode import paths:
- `tests/test_registry.py` -> `MODULE_MAP` maps logical name -> `{import_as, parent}` (or `{installed: True}` for installed pkgs like palsav).
- Tests do: `from tests.dynamic_importer import import_from` then `X = import_from('palsav.archive', 'FArchiveReader')`.
- `tests/conftest.py` -> `pytest_sessionstart` injects parent dirs into sys.path.
- **To move a source module: update only MODULE_MAP. Zero test files change.** This is the restructure-safe design of this repo — respect it.

Commands (run from repo root, venv active):
- `pytest` — fast suite (~186 tests, ~0.6s; excludes `@pytest.mark.slow`).
- `pytest -m slow` — only the save-file roundtrip (~40s, decompresses/recompresses a 3.2MB V1 beta save in `tests/save_test/`).
- `pytest -m ""` — everything (~206 tests).
- `python scripts/scrs/test_interactively.py` — menu runner (`--quick` / `--all`).

**Structural audit** auto-runs at session start via conftest (`tests/harness/`: `file_pairer`, `graph_validator`, `resource_auditor`, `structural_cache`). It gates the suite: file pairing + import graph + resource path integrity + **relative-import resolution check** (catches broken `from .X`/`from ..X` that lazy/in-function code hides from runtime tests). Flags:
- `--skip-structural` — skip ALL structural checks.
- `--no-deep-audit` — skip file pairing + import graph (keep resource audit).
- `--no-strict-paths` — skip the deep AST resource-path audit.
- `--dump-structural` — print full report without aborting.

Test layout: `tests/unit/{core_logic,palsav_core,palworld_aio_tests,scripts}`, `tests/integration/{test_imports,test_palworld_save,test_resource_integrity}`.

## Repo composition (measured)
~2900 tracked files, but 2467 are in `resources/game_data` (mostly 2470 .webp icons — pals/npcs/items/passives/structures/technologies/elements/ui). Real source: 213 files in src/, 35 tests, 31 scripts. Total Python LOC ~50,643. Heaviest files: edit_pals.py (5454), func_manager.py (2657), base_inventory_tab.py (2606), update_game_data.py (2362), inventory_tab.py (2203), main_window.py (2144), map_tab.py (1916). palsav engine (archive.py 809) is dwarfed by the GUI layer.

## Structural audit findings (known issues)
1. **STALE .gitattributes**: references `src/palsav/pyooz/` (deleted in 1e3eff6, renamed to palooz). The 15 SIMDe .h headers now under palooz are NOT marked linguist-vendored → GitHub C++ language stats inflated. Fix: update path to `src/palsav/palooz/ooz/dep/ooz/simde/**`.
2. **Icon storage split 3 ways**: `resources/assets/icons` (16, app icons), `resources/game_data/icons` (2456, game entity icons), `src/data/icon/` (2 .ico — paladius/xenolord, look misplaced/orphaned).
3. **src/ top-level flat namespace**: 10 loose .py files (boot_paths, bootup, common, import_libs, loading_manager, nerd_btn, palobject, path_setup, qt_imports, resource_resolver) mixing boot/Qt/app concerns. import_libs.py is a star-import re-export hub (namespace pollution risk).
4. **.gitignore `lib/` is global**: could shadow a future legit lib dir. palsav/palsav/lib/ (compiled palooz .so, platform-specific) is gitignored — on-disk build output in the source tree.
5. **9 .cmd wrappers** in scripts/ duplicate the uv-venv bootstrap logic each (Windows launcher pattern).

## Gotchas
- The repo has a `dist/` and `build/` dir full of Nuitka/cx_Freeze build artifacts and a `.venv` — **always exclude these** when scanning files (`find` without filters drowns in noise). Scan only real source: exclude `.git`, `.venv`, `dist`, `build`, `__pycache__`, `*.egg-info`, `.pytest_cache`.
- There is no `AGENTS.md`/`CLAUDE.md`/`.cursorrules` yet — repo conventions live in README + tests/README.md + this skill.
- `palsav` (the engine) and `palooz` are installed packages; everything else under `src/` is path-imported.
- Save format versioning: tests target V1 beta saves. Mind format changes across Palworld updates (see `commands/auto_update.py`, `commands/diag.py`).

## How to grow this knowledge
Build focused per-section skills as we actually work there, e.g. `pst-save-pipeline` (deep palsav internals), `pst-pal-editor` (pal_editor_tab + edit_pals + characters.json schema), `pst-game-data-json` (the resources/game_data schemas), `pst-map-tab`, `pst-inventory`. Patch THIS skill's layout map whenever a module moves or a new package appears.