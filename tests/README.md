# Test Infrastructure

## Architecture

All tests use a **dynamic import system** that decouples test files from source layout. When you restructure the project, you update **one file** — zero test files change.

### Core files

| File | Purpose |
|------|---------|
| `test_registry.py` | Central `MODULE_MAP` — maps logical module names to filesystem paths |
| `dynamic_importer.py` | `import_from(path, name)` — routes imports through the registry |
| `conftest.py` | `pytest_sessionstart` hook — dynamic `sys.path` setup, namespace protection, fixtures |

### How tests import

Instead of:
```python
from palsav.archive import FArchiveReader
from common import APP_NAME
```

Every test does:
```python
from tests.dynamic_importer import import_from

FArchiveReader = import_from('palsav.archive', 'FArchiveReader')
APP_NAME = import_from('common', 'APP_NAME')
```

The `import_from()` call looks up the root module (`palsav`, `common`, etc.) in `MODULE_MAP`, injects the correct `sys.path` entry, and uses `importlib` to resolve the import dynamically.

---

## Restructuring

When you move source files, update `tests/test_registry.py`:

```python
# Before: common.py lives at src/common.py
'common': {'import_as': 'common', 'parent': 'src'},

# After: common.py moves to src/core/common.py
'common': {'import_as': 'core.common', 'parent': 'src'},
```

The `import_as` field is the actual Python import path. The `parent` field is the directory added to `sys.path` before importing. Tests never change.

### Installed packages

`palsav` and `palooz` are marked `{'installed': True}` — they use normal Python import (no `sys.path` manipulation).

### Adding a new module

1. Create the module somewhere under `src/`
2. Add an entry to `MODULE_MAP` in `test_registry.py`
3. Use `import_from('your_module', ...)` in tests

---

## Running tests

### Command line

```bash
pytest                       # fast suite (182 tests, ~0.3s)
pytest -m slow               # only save file tests
pytest -m ""                 # everything including slow (202 tests, ~45s)
pytest tests/unit/core_logic # specific area
```

### Interactive runner

```bash
python scripts/scrs/test_interactively.py          # menu mode
python scripts/scrs/test_interactively.py --quick   # fast suite, no menu
python scripts/scrs/test_interactively.py --all     # everything
```

---

## Slow tests

Save file tests (`tests/integration/test_palworld_save.py`) are marked `@pytest.mark.slow`. They decompress and roundtrip a 3.2MB Palworld V1 beta save — takes ~40s.

They are **excluded by default** via `addopts = -m "not slow"` in `pytest.ini`.

---

## Resource integrity tests

`tests/integration/test_resource_integrity.py` validates the resource restructuring (11 tests, ~0.1s):

| Test class | What it checks |
|------------|----------------|
| `TestResourceMapConsistency` | All `RESOURCE_MAP` entries point to existing files; canonical keys (`assets/`, `certs/`) map to themselves; no duplicate targets for canonical keys |
| `TestAssetInventoryIntegrity` | All critical branding/icons/maps/fonts exist; detects orphaned files in `resources/` that aren't in `RESOURCE_MAP` |
| `TestCaseSensitivity` | Filesystem casing matches `RESOURCE_MAP` entries — catches case-mismatch bugs across platforms |
| `TestResourcePathResolution` | `resource_path()` returns correct absolute paths for game_data, maps, icons, certs, and fonts |

These always run (not marked slow).

---

## Test layout

```
tests/
├── conftest.py                          # dynamic path setup, fixtures
├── test_registry.py                     # MODULE_MAP manifest
├── dynamic_importer.py                  # import_from() helper
├── save_test/                           # real Palworld save files (V1 beta)
│   ├── Level.sav
│   ├── LocalData.sav
│   └── Players/
├── integration/
│   ├── test_imports.py                  # import validation for all modules
│   ├── test_palworld_save.py           # save file decompress/parse/roundtrip (slow)
│   └── test_resource_integrity.py      # resource map/asset/filesystem validation
└── unit/
    ├── core_logic/                      # common, coords, version, paths, i18n, assets
    ├── palsav_core/                     # archive, gvas, json_tools
    ├── palworld_aio_tests/             # constants, utils
    └── scripts/                         # theme violation scanner
```

---

## Fixtures

| Fixture | Returns | Description |
|---------|---------|-------------|
| `project_dir` | `Path` | Project root |
| `src_dir` | `Path` | `project_dir / 'src'` |
| `resolve_source_target` | `Path or None` | Auto-finds source file matching current test (strips `test_` prefix, searches registry) |
| `sample_sav_path` | `Path` | Empty temp `.sav` file |
| `mock_gvas_data` | `dict` | Minimal GVAS-style dict |
| `helpers` | `Helpers` | `make_sav_path()` helper |
