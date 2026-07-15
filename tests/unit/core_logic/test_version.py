from __future__ import annotations
import pytest
from tests.dynamic_importer import import_from

_common = import_from('common')
APP_NAME = _common.APP_NAME
APP_VERSION = _common.APP_VERSION
get_versions = _common.get_versions
get_display_version = _common.get_display_version
is_frozen = _common.is_frozen
get_current_version = _common.get_current_version
is_standalone = _common.is_standalone
get_python_executable = _common.get_python_executable
get_backup_directory = _common.get_backup_directory
BACKUP_DIRS = _common.BACKUP_DIRS


def test_app_name():
    assert APP_NAME == 'PalworldSaveTools'
    assert isinstance(APP_NAME, str)


def test_version_format():
    parts = APP_VERSION.split('.')
    assert len(parts) == 2 or len(parts) == 3
    for p in parts:
        assert p.isdigit()


def test_get_versions_returns_tuple():
    result = get_versions()
    assert isinstance(result, tuple)
    assert len(result) == 2


def test_display_version_is_string():
    result = get_display_version()
    assert isinstance(result, str)
    assert len(result) > 0


def test_is_frozen_returns_bool():
    result = is_frozen()
    assert isinstance(result, bool)


def test_get_current_version_matches():
    result = get_current_version()
    assert isinstance(result, str)
    assert '.' in result


def test_is_standalone_returns_bool():
    result = is_standalone()
    assert isinstance(result, bool)


def test_get_python_executable_matches():
    import sys
    assert get_python_executable() == sys.executable


def test_get_backup_directory_is_absolute():
    import os
    result = get_backup_directory('test')
    assert os.path.isabs(result)


def test_BACKUP_DIRS_has_expected_keys():
    expected = {'all_in_one_tools', 'slot_injector', 'character_transfer', 'fix_host_save', 'restore_map'}
    assert set(BACKUP_DIRS.keys()) == expected
