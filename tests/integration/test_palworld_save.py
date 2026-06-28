from __future__ import annotations

import pytest
from pathlib import Path
from tests.dynamic_importer import import_from
from tests.test_registry import SAVE_TEST_DIR

pytestmark = pytest.mark.slow

decompress_sav_to_gvas = import_from('palsav.core', 'decompress_sav_to_gvas')
compress_gvas_to_sav = import_from('palsav.core', 'compress_gvas_to_sav')
GvasFile = import_from('palsav.gvas', 'GvasFile')
PALWORLD_TYPE_HINTS = import_from('palsav.paltypes', 'PALWORLD_TYPE_HINTS')
PALWORLD_CUSTOM_PROPERTIES = import_from('palsav.paltypes', 'PALWORLD_CUSTOM_PROPERTIES')


def _load_sav(path: Path):
    data = path.read_bytes()
    gv_bytes, save_type = decompress_sav_to_gvas(data)
    gvas = GvasFile.read(
        gv_bytes,
        type_hints=PALWORLD_TYPE_HINTS,
        custom_properties=PALWORLD_CUSTOM_PROPERTIES,
    )
    return gvas, save_type


@pytest.fixture
def level_sav():
    return SAVE_TEST_DIR / 'Level.sav'


@pytest.fixture
def local_data_sav():
    return SAVE_TEST_DIR / 'LocalData.sav'


@pytest.fixture
def player_sav():
    return SAVE_TEST_DIR / 'Players' / '00000000000000000000000000000001.sav'


@pytest.fixture
def player_dps_sav():
    return SAVE_TEST_DIR / 'Players' / '00000000000000000000000000000001_dps.sav'


class TestLevelSav:
    def test_file_exists(self, level_sav):
        assert level_sav.is_file()
        assert level_sav.stat().st_size > 0

    def test_decompress(self, level_sav):
        data = level_sav.read_bytes()
        gv_bytes, save_type = decompress_sav_to_gvas(data)
        assert len(gv_bytes) > 0
        assert isinstance(save_type, int)
        assert len(gv_bytes) > len(data)

    def test_parse(self, level_sav):
        gvas, _ = _load_sav(level_sav)
        assert gvas.header.save_game_class_name == '/Script/Pal.PalWorldSaveGame'
        assert 'worldSaveData' in gvas.properties
        assert 'Version' in gvas.properties
        assert 'Timestamp' in gvas.properties

    def test_world_save_data_has_characters(self, level_sav):
        gvas, _ = _load_sav(level_sav)
        wsd = gvas.properties['worldSaveData']
        wsd_val = wsd.get('value', wsd)
        if isinstance(wsd_val, dict):
            chars = wsd_val.get('CharacterSaveParameterMap', {}).get('value', [])
            assert isinstance(chars, list)
            assert len(chars) > 0

    def test_world_save_data_has_groups(self, level_sav):
        gvas, _ = _load_sav(level_sav)
        wsd = gvas.properties['worldSaveData']
        wsd_val = wsd.get('value', wsd)
        if isinstance(wsd_val, dict):
            groups = wsd_val.get('GroupSaveDataMap', {}).get('value', [])
            assert isinstance(groups, list)

    def test_dump_roundtrip(self, level_sav):
        gvas, _ = _load_sav(level_sav)
        dumped = gvas.dump()
        assert 'header' in dumped
        assert 'properties' in dumped
        assert 'trailer' in dumped

        gvas2 = GvasFile.load(dumped)
        assert gvas2.header.save_game_class_name == gvas.header.save_game_class_name
        assert set(gvas2.properties.keys()) == set(gvas.properties.keys())

    def test_full_roundtrip(self, level_sav):
        data = level_sav.read_bytes()
        gv_bytes, save_type = decompress_sav_to_gvas(data)
        gvas = GvasFile.read(gv_bytes, type_hints=PALWORLD_TYPE_HINTS, custom_properties=PALWORLD_CUSTOM_PROPERTIES)
        written = gvas.write(custom_properties=PALWORLD_CUSTOM_PROPERTIES)
        assert len(written) == len(gv_bytes)

        compressed = compress_gvas_to_sav(written, save_type)
        assert len(compressed) == len(data)

    def test_trailer_is_bytes(self, level_sav):
        gvas, _ = _load_sav(level_sav)
        assert isinstance(gvas.trailer, bytes)


class TestLocalDataSav:
    def test_file_exists(self, local_data_sav):
        assert local_data_sav.is_file()

    def test_decompress_and_parse(self, local_data_sav):
        gvas, _ = _load_sav(local_data_sav)
        assert gvas.header.save_game_class_name == '/Script/Pal.PalLocalWorldSaveGame'
        assert 'SaveData' in gvas.properties

    def test_dump_roundtrip(self, local_data_sav):
        gvas, _ = _load_sav(local_data_sav)
        dumped = gvas.dump()
        gvas2 = GvasFile.load(dumped)
        assert set(gvas2.properties.keys()) == set(gvas.properties.keys())


class TestPlayerSav:
    def test_file_exists(self, player_sav):
        assert player_sav.is_file()

    def test_decompress_and_parse(self, player_sav):
        gvas, _ = _load_sav(player_sav)
        assert gvas.header.save_game_class_name == '/Script/Pal.PalWorldPlayerSaveGame'
        assert 'SaveData' in gvas.properties
        assert 'Version' in gvas.properties

    def test_dump_roundtrip(self, player_sav):
        gvas, _ = _load_sav(player_sav)
        dumped = gvas.dump()
        gvas2 = GvasFile.load(dumped)
        assert set(gvas2.properties.keys()) == set(gvas.properties.keys())


class TestPlayerDpsSav:
    def test_file_exists(self, player_dps_sav):
        assert player_dps_sav.is_file()

    def test_decompress_and_parse(self, player_dps_sav):
        gvas, _ = _load_sav(player_dps_sav)
        assert gvas.header is not None
        assert isinstance(gvas.properties, dict)

    def test_dump_roundtrip(self, player_dps_sav):
        gvas, _ = _load_sav(player_dps_sav)
        dumped = gvas.dump()
        gvas2 = GvasFile.load(dumped)
        assert set(gvas2.properties.keys()) == set(gvas.properties.keys())


class TestRegistryIntegration:
    def test_save_test_dir_exists(self):
        assert SAVE_TEST_DIR.is_dir()

    def test_save_test_dir_has_level(self):
        assert (SAVE_TEST_DIR / 'Level.sav').is_file()

    def test_save_test_dir_has_players(self):
        players = SAVE_TEST_DIR / 'Players'
        assert players.is_dir()
        sav_files = list(players.glob('*.sav'))
        assert len(sav_files) > 0
