# PST (PalworldSaveTools) – Session Memory

## Agent Rules
- Do NOT commit or push without explicit instruction.
- Ask before adding or removing files.
- Keep responses terse.
- Run `backup_whole_directory()` before any destructive operation.

## Project Snapshot
- **Purpose:** GUI + CLI for editing Palworld save files. GitHub `deadafdudecomputers/PalworldSaveTools`, author **Pylar**. MIT.
- **Tech:** Python ≥3.11, **uv** (workspace), pytest, PySide6, Nuitka (CI), cx_Freeze (Windows installer).
- **Active branch:** `upd/ProjRefactor`. venv at `.venv`.
- **Key Architecture:** 3‑layer pipeline (SAV↔GVAS↔JSON). GUI state lives in module globals at `palworld_aio.constants`. The `GvasFileWrapper` (dict-like adapter) wraps the decoded save; all managers mutate it in place.
- **Testing:** `pytest` (fast ~0.6s), `pytest -m slow` (~40s roundtrip), `pytest -m ""` (all ~206). `--skip-structural` / `--no-deep-audit` / `--no-strict-paths` flags.

## Critical Gotchas
- **Triplicated reset block:** constants reset on new load is copy‑pasted in 3 places (`main.py`, `save_manager.py`, inline in `reload_current_save`) — adding a global requires editing all three.
- **CLI ≠ GUI decoding:** GUI uses `SKP_PALWORLD_CUSTOM_PROPERTIES` which overrides 6 paths with no-ops (MapObject positions, foliage, spawners) for speed — CLI uses the full table. Foliage/spawner edits require CLI.
- **Compression selection:** world‑class saves → PLZ (double‑zlib, type=50); others → PLM (Oodle, type=49). Checked via `'Pal.PalworldSaveGame'` in class name (note lowercase `w` — UE often PascalCase).
- **Two save locations:** `constants.loaded_level_json` (Level.sav, flushed on File→Save) AND per‑player .sav files (written immediately, not deferred).
- **Selection highlight:** must call `widget.set_selected(False)` before rebuild.
- **Booth lock:** controlled by `is_private_lock` byte (not `private_lock_player_uid` — that GUID is always non-zero).
- **Guild `_u8_flag`:** only read when `_has_v1_marker` is present (pre‑V1 format has no flag bytes between player entries).
- **i18n default:** `init_language()` defaults to `zh_CN` (Chinese), not English, if `config.json` is missing.
- **Structural audit skips:** `--skip-structural` to bypass file‑pairing / import‑graph / resource‑path checks on every test run.

## 9 Tabs (QStackedWidget order)
0=Tools, 1=BaseInventory, 2=PlayerInventory, 3=PalEditor, 4=Players, 5=Guilds, 6=Bases, 7=Map, 8=Exclusions.

## 13 Managers
`save_manager.py` (load/save/reload, QObject singleton), `player_manager.py`, `guild_manager.py`, `inventory_manager.py` (per‑player), `base_inventory_manager.py` (guild/base, thread‑safe, 2s debounce), `base_manager.py` (blueprint export/import), `dynamic_item_manager.py`, `standardized_container.py` (low‑level slots), `container_ownership.py`, `data_manager.py` (queries + structural deletes), `func_manager.py` (catch‑all cleanup, ~50 fns, 2657 lines), `zone_manager.py` (exclusion zones), `backup_manager.py` (.pstbase/.pst7 export).

## Skills (load on demand)
- `pst-codebase` – repo layout & entry points.
- `pst-save-pipeline` – save/round‑trip logic.
- `pst-pal-editor` – pal stats & editing.
- `pst-ui-tabs` – UI widgets and Qt styling.
- `pst-gui-architecture` – app structure.
- `pst-game-data` – JSON schemas & i18n.
- `pst-build-ci` – build system.
- `pst-stat-formula` – stat calculations.
- `pst-binary-schemas` – binary format details.
- `pst-cli-tools` – CLI tools & XGP pipeline.
- `pst-opencode-config` – opencode config, plugins, snapshot gotchas.
