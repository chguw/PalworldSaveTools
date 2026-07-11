from __future__ import annotations
import os
import pytest
from tests.dynamic_importer import import_from

constants = import_from('palworld_aio.constants')


def test_constants_exist():
    assert constants.BG == '#0A0B0E'
    assert constants.ACCENT == '#3B8ED0'
    assert constants.TEXT == '#E6EEF6'
    assert isinstance(constants.FONT_SIZE, int)
    assert isinstance(constants.SPACE_MEDIUM, int)
    assert isinstance(constants.CORNER_RADIUS, int)


def test_urls_exist():
    assert constants.GIT_REPO_URL.startswith('https://')
    assert constants.GITHUB_RAW_URL.startswith('https://')
    assert constants.STABLE_BRANCH == 'main'


def test_get_base_path():
    result = constants.get_base_path()
    assert isinstance(result, str)
    assert os.path.isabs(result)


def test_get_src_path():
    result = constants.get_src_path()
    assert isinstance(result, str)
    assert 'src' in result


def test_get_icon_path():
    result = constants.get_icon_path()
    assert result.endswith('icon.ico')
    assert os.path.isabs(result)


def test_ICON_PATH_const():
    assert constants.ICON_PATH.endswith('icon.ico')


def test_exclusion_files():
    assert 'deletion_exclusions' in constants.EXCLUSIONS_FILE
    assert 'zone_exclusions' in constants.ZONE_EXCLUSIONS_FILE


def test_module_exports():
    assert hasattr(constants, 'get_base_path')
    assert hasattr(constants, 'get_src_path')
    assert hasattr(constants, 'get_icon_path')
    assert hasattr(constants, 'get_container_lookup')
    assert hasattr(constants, 'invalidate_container_lookup')


def test_container_lookup_empty_when_no_data():
    constants.loaded_level_json = None
    result = constants.get_container_lookup()
    assert result == {}
