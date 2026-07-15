from __future__ import annotations
import os
import sys
import pytest
from tests.dynamic_importer import import_from

_common = import_from('common')
APP_NAME = _common.APP_NAME
APP_VERSION = _common.APP_VERSION
TESTING_VER = _common.TESTING_VER
GAME_VERSION = _common.GAME_VERSION
get_base_directory = _common.get_base_directory
get_src_directory = _common.get_src_directory
get_resources_directory = _common.get_resources_directory
ICON_PATH = _common.ICON_PATH
get_backup_directory = _common.get_backup_directory
BACKUP_BASE_DIR = _common.BACKUP_BASE_DIR
BACKUP_DIRS = _common.BACKUP_DIRS
is_frozen = _common.is_frozen
get_python_executable = _common.get_python_executable
get_versions = _common.get_versions
get_display_version = _common.get_display_version
get_current_version = _common.get_current_version


def test_app_name():
    assert APP_NAME == 'PalworldSaveTools'
    assert isinstance(APP_NAME, str)


def test_version_constants():
    assert isinstance(APP_VERSION, str) and APP_VERSION.count('.') == 2
    assert isinstance(TESTING_VER, str) and TESTING_VER.count('.') == 2
    assert isinstance(GAME_VERSION, str)


def test_get_base_directory(project_dir):
    result = get_base_directory()
    assert isinstance(result, str)
    assert os.path.isabs(result)
    assert result == str(project_dir)


def test_get_src_directory(src_dir):
    result = get_src_directory()
    assert result == str(src_dir)


def test_get_resources_directory(project_dir):
    result = get_resources_directory()
    assert result == os.path.join(str(project_dir), 'resources')


def test_ICON_PATH():
    assert ICON_PATH.endswith('icon.ico')
    assert os.path.isabs(ICON_PATH)


def test_get_backup_directory():
    result = get_backup_directory('test_tool')
    assert result == os.path.join(BACKUP_BASE_DIR, 'test_tool')
    assert os.path.isabs(result)


def test_BACKUP_DIRS():
    assert isinstance(BACKUP_DIRS, dict)
    assert 'all_in_one_tools' in BACKUP_DIRS


def test_is_frozen():
    result = is_frozen()
    assert result is False


def test_get_python_executable():
    result = get_python_executable()
    assert result == sys.executable


def test_get_versions():
    v, g = get_versions()
    assert v == APP_VERSION
    assert g == GAME_VERSION


def test_get_display_version():
    result = get_display_version()
    assert isinstance(result, str)
    assert len(result) > 0
    app_tuple = tuple(int(x) for x in APP_VERSION.split('.'))
    testing_tuple = tuple(int(x) for x in TESTING_VER.split('.'))
    if testing_tuple > app_tuple:
        assert result == f'{TESTING_VER} (testing)'
    else:
        assert result == APP_VERSION


def test_get_current_version():
    result = get_current_version()
    assert isinstance(result, str)
    assert '.' in result


def test_get_python_executable_matches_sys():
    assert get_python_executable() == sys.executable
