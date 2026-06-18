#!/usr/bin/env python3
from __future__ import annotations
import sys
import os

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC_DIR = os.path.join(PROJECT_DIR, 'src')

try:
    import palsav
except ImportError:
    pass

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from path_setup import setup as _setup_paths
_setup_paths()

errors = []
modules_to_test = [
    ('path_setup', ['setup', 'get_src_dir', 'get_project_dir']),
    ('common', ['APP_NAME', 'APP_VERSION', 'get_base_directory', 'ICON_PATH']),
    ('i18n', ['t', 'init_language', 'set_language', 'get_language']),
    ('palobject', ['toUUID', 'MappingCacheObject', 'SKP_PALWORLD_CUSTOM_PROPERTIES']),
    ('loading_manager', ['run_with_loading', 'show_information', 'show_warning', 'show_critical']),
    ('import_libs', ['NerdBtn', 'backup_whole_directory', 'center_window']),
    ('qt_imports', ['QApplication', 'QWidget', 'QMainWindow']),
    ('nerd_btn', ['NerdBtn']),
    ('palworld_aio.constants', ['get_src_path']),
    ('palworld_coord', ['sav_to_map']),
    ('palworld_xgp_import.container_types', ['ContainerIndex', 'Container', 'FILETIME', 'ContainerFileList']),
    ('palworld_xgp_import.gamepass_manager', ['find_container_paths', 'read_container_index', 'convert_to_steam']),
    ('palsav.archive', ['UUID', 'FArchiveReader', 'FArchiveWriter']),
    ('palsav.paltypes', ['PALWORLD_CUSTOM_PROPERTIES', 'PALWORLD_TYPE_HINTS']),
    ('palsav.gvas', ['GvasFile']),
    ('palsav.json_tools', ['load', 'dump']),
]

for module_name, attrs in modules_to_test:
    try:
        mod = __import__(module_name, fromlist=attrs)
        for attr in attrs:
            if not hasattr(mod, attr):
                errors.append(f'{module_name} missing {attr}')
        print(f'  OK  {module_name}')
    except Exception as e:
        errors.append(f'{module_name}: {e}')
        print(f'FAIL  {module_name}: {e}')

if errors:
    print(f'\n{len(errors)} error(s):')
    for e in errors:
        print(f'  - {e}')
    sys.exit(1)
else:
    print(f'\nAll {len(modules_to_test)} modules imported successfully')
    sys.exit(0)
