from __future__ import annotations
import pytest
from tests.dynamic_importer import import_from

_common = import_from('common')
APP_NAME = _common.APP_NAME
get_base_directory = _common.get_base_directory
ICON_PATH = _common.ICON_PATH
get_versions = _common.get_versions

sav_to_map = import_from('palworld_coord', 'sav_to_map')
map_to_sav = import_from('palworld_coord', 'map_to_sav')

_i18n = import_from('i18n')
t = _i18n.t
init_language = _i18n.init_language
set_language = _i18n.set_language
get_language = _i18n.get_language
load_resources = _i18n.load_resources

_qt = import_from('qt_imports')
QApplication = _qt.QApplication
QWidget = _qt.QWidget
QMainWindow = _qt.QMainWindow

_path_setup = import_from('path_setup')
setup = _path_setup.setup
get_src_dir = _path_setup.get_src_dir
get_project_dir = _path_setup.get_project_dir

_palobject = import_from('palobject')
toUUID = _palobject.toUUID
MappingCacheObject = _palobject.MappingCacheObject
SKP_PALWORLD_CUSTOM_PROPERTIES = _palobject.SKP_PALWORLD_CUSTOM_PROPERTIES

_loading_manager = import_from('loading_manager')
run_with_loading = _loading_manager.run_with_loading
show_information = _loading_manager.show_information
show_warning = _loading_manager.show_warning
show_critical = _loading_manager.show_critical

_import_libs = import_from('import_libs')
NerdBtn = _import_libs.NerdBtn
backup_whole_directory = _import_libs.backup_whole_directory
center_window = _import_libs.center_window

NerdBtn = import_from('nerd_btn', 'NerdBtn')

get_src_path = import_from('palworld_aio.constants', 'get_src_path')
get_base_path = import_from('palworld_aio.constants', 'get_base_path')

_palsav_archive = import_from('palsav.archive')
UUID = _palsav_archive.UUID
FArchiveReader = _palsav_archive.FArchiveReader
FArchiveWriter = _palsav_archive.FArchiveWriter

_palsav_paltypes = import_from('palsav.paltypes')
PALWORLD_CUSTOM_PROPERTIES = _palsav_paltypes.PALWORLD_CUSTOM_PROPERTIES
PALWORLD_TYPE_HINTS = _palsav_paltypes.PALWORLD_TYPE_HINTS

GvasFile = import_from('palsav.gvas', 'GvasFile')

_palsav_json_tools = import_from('palsav.json_tools')
json_load = _palsav_json_tools.load
json_dump = _palsav_json_tools.dump

_palsav_palsav = import_from('palsav.core')
decompress_sav_to_gvas = _palsav_palsav.decompress_sav_to_gvas
compress_gvas_to_sav = _palsav_palsav.compress_gvas_to_sav

setup_logging = import_from('palsav', 'setup_logging')

sav_to_map_by_z = import_from('palworld_coord', 'sav_to_map_by_z')

_xgp_ct = import_from('palworld_xgp_import.container_types')
ContainerIndex = _xgp_ct.ContainerIndex
Container = _xgp_ct.Container
FILETIME = _xgp_ct.FILETIME
ContainerFileList = _xgp_ct.ContainerFileList

_xgp_gm = import_from('palworld_xgp_import.gamepass_manager')
find_container_paths = _xgp_gm.find_container_paths
read_container_index = _xgp_gm.read_container_index
convert_to_steam = _xgp_gm.convert_to_steam
convert_to_gamepass_from_steam = _xgp_gm.convert_to_gamepass_from_steam


def test_common_imports():
    assert APP_NAME == 'PalworldSaveTools'
    assert isinstance(get_base_directory(), str)


def test_palworld_coord_imports():
    assert callable(sav_to_map)


def test_i18n_imports():
    assert callable(t)


def test_qt_imports():
    assert QApplication is not None


def test_path_setup_imports():
    assert callable(setup)


def test_palobject_imports():
    assert callable(toUUID)


def test_loading_manager_imports():
    assert callable(run_with_loading)


def test_import_libs_imports():
    assert callable(backup_whole_directory)


def test_nerd_btn_imports():
    assert NerdBtn is not None


def test_palworld_aio_constants_imports():
    assert callable(get_src_path)


def test_palsav_archive_imports():
    assert UUID is not None


def test_palsav_paltypes_imports():
    assert isinstance(PALWORLD_TYPE_HINTS, dict)


def test_palsav_gvas_imports():
    assert GvasFile is not None


def test_palsav_json_tools_imports():
    assert callable(json_load)


def test_palsav_palsav_imports():
    assert callable(decompress_sav_to_gvas)


def test_palsav_setup_logging_import():
    assert callable(setup_logging)


def test_common_get_versions():
    v = get_versions()
    assert len(v) == 2


def test_palworld_coord_sav_to_map_by_z():
    result = sav_to_map_by_z(0, 0, z=0)
    assert len(result) == 2


def test_i18n_load_resources():
    assert callable(load_resources)


def test_path_setup_setup_adds_src():
    import sys
    src_before = str(get_src_dir()) in sys.path
    if not src_before:
        setup()
    assert str(get_src_dir()) in sys.path


def test_xgp_container_types_imports():
    assert ContainerIndex is not None
    assert Container is not None
    assert FILETIME is not None
    assert ContainerFileList is not None
    assert callable(ContainerIndex.from_stream)


def test_xgp_gamepass_manager_imports():
    assert callable(find_container_paths)
    assert callable(read_container_index)
    assert callable(convert_to_steam)
    assert callable(convert_to_gamepass_from_steam)
