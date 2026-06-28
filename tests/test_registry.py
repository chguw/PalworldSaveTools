from __future__ import annotations

from pathlib import Path

def _find_project_root() -> Path:
    p = Path(__file__).resolve()
    for parent in [p] + list(p.parents):
        if (parent / 'pyproject.toml').exists():
            return parent
    return p.parent.parent.parent / 'pst_dev'

PROJECT_ROOT = _find_project_root()
TESTS_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / 'src'
SCRIPTS_DIR = PROJECT_ROOT / 'scripts'
RESOURCES_DIR = PROJECT_ROOT / 'resources'
SAVE_TEST_DIR = TESTS_ROOT / 'save_test'

MODULE_MAP: dict[str, dict] = {
    'common':                {'import_as': 'common',                'parent': 'src'},
    'path_setup':            {'import_as': 'path_setup',            'parent': 'src'},
    'resource_resolver':     {'import_as': 'resource_resolver',     'parent': 'src'},
    'qt_imports':            {'import_as': 'qt_imports',            'parent': 'src'},
    'palobject':             {'import_as': 'palobject',             'parent': 'src'},
    'loading_manager':       {'import_as': 'loading_manager',       'parent': 'src'},
    'import_libs':           {'import_as': 'import_libs',           'parent': 'src'},
    'nerd_btn':              {'import_as': 'nerd_btn',              'parent': 'src'},
    'bootup':                {'import_as': 'bootup',                'parent': 'src'},

    'palworld_aio':          {'import_as': 'palworld_aio',          'parent': 'src'},
    'palworld_toolsets':     {'import_as': 'palworld_toolsets',     'parent': 'src'},
    'palworld_coord':        {'import_as': 'palworld_coord',        'parent': 'src'},
    'i18n':                  {'import_as': 'i18n',                  'parent': 'src'},
    'palworld_xgp_import':   {'import_as': 'palworld_xgp_import',  'parent': 'src'},

    'palsav':                {'installed': True},
    'palooz':                {'installed': True},

    'check_theme_violations': {'import_as': 'check_theme_violations', 'parent': 'scripts/scrs'},
    'validate_imports':       {'import_as': 'validate_imports',       'parent': 'scripts/scrs'},
    'clean_code':             {'import_as': 'clean_code',             'parent': 'scripts/scrs'},
    'auto_update':            {'import_as': 'auto_update',            'parent': 'scripts/scrs'},
    'build_cx':               {'import_as': 'build_cx',               'parent': 'scripts/scrs'},
}

_PARENT_CACHE: dict[str, Path] = {}


def _resolve_parent(alias: str) -> Path:
    if alias not in _PARENT_CACHE:
        _PARENT_CACHE[alias] = PROJECT_ROOT / alias
    return _PARENT_CACHE[alias]


def get_all_parent_dirs() -> list[Path]:
    dirs: list[Path] = []
    seen: set[str] = set()
    for entry in MODULE_MAP.values():
        if entry.get('installed'):
            continue
        parent_alias = entry.get('parent')
        if parent_alias and parent_alias not in seen:
            seen.add(parent_alias)
            resolved = _resolve_parent(parent_alias)
            if resolved.is_dir():
                dirs.append(resolved)
    return dirs


def get_entry(logical_root: str) -> dict | None:
    return MODULE_MAP.get(logical_root)


_SOURCE_INDEX: dict[str, Path] | None = None


def _build_source_index() -> dict[str, Path]:
    index: dict[str, Path] = {}
    for parent_dir in get_all_parent_dirs():
        for py_file in parent_dir.rglob('*.py'):
            stem = py_file.stem
            if stem.startswith('_') and stem != '__init__':
                continue
            if stem not in index:
                index[stem] = py_file
    return index


def find_source_for_test(test_stem: str) -> Path | None:
    global _SOURCE_INDEX
    if _SOURCE_INDEX is None:
        _SOURCE_INDEX = _build_source_index()
    if not test_stem.startswith('test_'):
        return None
    base = test_stem[5:]
    return _SOURCE_INDEX.get(base)
