# AGENTS.md — PalworldSaveTools (PST)

## Quick start

```bash
uv run start.py                          # app entry (bootstraps venv)
source .venv/bin/activate                # activate venv directly
```

## Commands

```bash
cd tests && pytest                       # fast suite (~0.6s, excludes slow)
cd tests && pytest -m slow               # 40s save-file roundtrip
cd tests && pytest -m ""                 # everything (~206 tests)
cd tests && pytest --skip-structural     # bypass all file-pairing/import/resource audits
cd tests && pytest --no-deep-audit --no-strict-paths # skip import graph + AST resource-path checks
```

## Architecture

- **3-layer save pipeline**: SAV ↔ GVAS ↔ JSON via `palsav` engine (`src/palsav/`)
- **Global state**: `palworld_aio.constants` module globals; `GvasFileWrapper` wraps decoded save
- **All managers mutate in place** on `constants.loaded_level_json`
- **palsav is an installed workspace pkg** (`uv workspace`, editable). Do NOT import from `src/` directly
- **10 flat files** in `src/` (boot, path, qt, i18n, etc.) + 6 packages

## Critical gotchas

- **Triplicated reset block**: constants reset on load is copy-pasted in `main.py` + `save_manager.py` + `reload_current_save`. Adding a global = edit all three.
- **CLI ≠ GUI decoding**: GUI uses `SKP_PALWORLD_CUSTOM_PROPERTIES` (6 no-op paths for speed). Full foliage/spawner edits require CLI.
- **Compression**: world saves → PLZ (double-zlib, type=50); others → PLM (Oodle, type=49). Checked via `'Pal.PalworldSaveGame'` (note lowercase `w`).
- **Two save locations**: `constants.loaded_level_json` (Level.sav, deferred write) + per-player .sav files (written immediately).
- **i18n default**: `init_language()` falls back to `zh_CN`, not English.
- **Re-export hub**: `import_libs.py` star-imports everything from palsav into namespace.

## Dynamic test imports (MUST follow)

Tests never hardcode import paths. On module move, update **only** `tests/test_registry.py`:

```python
# test_registry.py
MODULE_MAP = {
    'common':     {'import_as': 'common',     'parent': 'src'},
    'bootup':     {'import_as': 'bootup',     'parent': 'src'},
    'palsav':     {'installed': True},    # workspace package
    'palooz':     {'installed': True},
    ...
}
```

Tests import via:
```python
from tests.dynamic_importer import import_from
X = import_from('common', 'APP_NAME')
```

## Build

| Target | Command | Output |
|---|---|---|
| Release binary | `uv run python build/nuitka/build_nuitka.py --onefile` | `dist/` |
| Windows installer | `uv run python build/cx_freeze/build_cx.py` | `PST_standalone/` |

CI (5 workflows) builds Nuitka binaries; **pytest does NOT run in CI**.

## OpenCode config (`.opencode/`)

- `instructions` (auto-loaded): `AGENTS.md` + `memory.md`
- Skills in `.opencode/skills/<name>/SKILL.md` — load via `skill({ name: "pst-*" })`
- Plugins in `.opencode/plugins/` — auto-discovered, no config entry needed
- Config is `.jsonc` (JSON with Comments); merges across global/project dirs

## Source layout

```
src/
  palsav/               # SERIALIZATION ENGINE (workspace pkg)
  palworld_aio/         # GUI app (managers/, editor/, ui/)
  palworld_toolsets/    # CLI tools (9)
  palworld_xgp_import/  # Xbox Game Pass import pipeline
  palworld_coord/       # Coordinate transforms
  bootup.py             # Entry after start.py (splash + dep check)
  boot_paths.py         # Path constants
  import_libs.py        # Star-import re-export hub
```

## Repo exclusions

`.venv/`, `dist/`, `build/`, `Backups/`, `*.sav`, `*.savc`, `*.7z`, `uv.lock` — all gitignored.
