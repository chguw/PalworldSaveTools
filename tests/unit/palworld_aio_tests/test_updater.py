from __future__ import annotations
import json
import os
import sys
import tempfile
from pathlib import Path
import pytest
from tests.dynamic_importer import import_from

_updater = import_from('palworld_aio.updater')
_platform_asset_suffix = _updater._platform_asset_suffix
StandaloneUpdater = _updater.StandaloneUpdater
get_update_settings = _updater.get_update_settings
save_update_settings = _updater.save_update_settings


def test_platform_asset_suffix_win(monkeypatch):
    monkeypatch.setattr(sys, 'platform', 'win32')
    assert _platform_asset_suffix() == 'win.exe'


def test_platform_asset_suffix_macos(monkeypatch):
    monkeypatch.setattr(sys, 'platform', 'darwin')
    assert _platform_asset_suffix() == 'macos.dmg'


def test_platform_asset_suffix_linux(monkeypatch):
    monkeypatch.setattr(sys, 'platform', 'linux')
    assert _platform_asset_suffix() == 'linux.AppImage'


class TestStandaloneUpdater:
    @property
    def _sample_release_data(self):
        return {
            'tag_name': 'v2.0.9',
            'assets': [
                {'name': 'PalworldSaveTools-V2.0.9-win.exe'},
                {'name': 'PalworldSaveTools-V2.0.9-linux.AppImage'},
                {'name': 'PalworldSaveTools-V2.0.9-macos.dmg'},
            ],
        }

    def _mock_urlopen(self, monkeypatch, data: dict):
        import urllib.request
        body = json.dumps(data).encode()
        class FakeResponse:
            headers = {'Content-Length': str(len(body))}
            def read(self, *a, **kw):
                return body
            def __enter__(self):
                return self
            def __exit__(self, *a):
                pass
        monkeypatch.setattr(urllib.request, 'urlopen', lambda *a, **kw: FakeResponse())

    def test_check_version_finds_asset(self, monkeypatch):
        self._mock_urlopen(monkeypatch, self._sample_release_data)
        monkeypatch.setattr(sys, 'platform', 'win32')
        monkeypatch.setattr(sys, 'executable', __file__)
        updater = StandaloneUpdater()
        result = updater.check_version()
        assert result['latest'] == '2.0.9'
        assert result['asset_name'] == 'PalworldSaveTools-V2.0.9-win.exe'

    def test_check_version_macos_asset(self, monkeypatch):
        self._mock_urlopen(monkeypatch, self._sample_release_data)
        monkeypatch.setattr(sys, 'platform', 'darwin')
        monkeypatch.setattr(sys, 'executable', __file__)
        updater = StandaloneUpdater()
        result = updater.check_version()
        assert result['asset_name'] == 'PalworldSaveTools-V2.0.9-macos.dmg'

    def test_check_version_no_update(self, monkeypatch):
        from common import APP_VERSION
        data = dict(self._sample_release_data)
        data['tag_name'] = f'v{APP_VERSION}'
        self._mock_urlopen(monkeypatch, data)
        monkeypatch.setattr(sys, 'platform', 'win32')
        monkeypatch.setattr(sys, 'executable', __file__)
        updater = StandaloneUpdater()
        result = updater.check_version()
        assert result['update_available'] is False

    def test_check_version_http_failure(self, monkeypatch):
        import urllib.request, urllib.error
        def _fail(*a, **kw):
            raise urllib.error.URLError('fail')
        monkeypatch.setattr(urllib.request, 'urlopen', _fail)
        monkeypatch.setattr(sys, 'executable', __file__)
        updater = StandaloneUpdater()
        result = updater.check_version()
        assert result['error'] is not None

    def test_download_writes_file(self, monkeypatch, tmp_path):
        monkeypatch.setattr(sys, 'platform', 'win32')
        monkeypatch.setattr(tempfile, 'mkdtemp', lambda **kw: str(tmp_path))
        import urllib.request
        _read_count = [0]
        class FakeStream:
            def __enter__(self):
                return self
            def __exit__(self, *a):
                pass
            def read(self, n):
                _read_count[0] += 1
                if _read_count[0] > 1:
                    return b''
                return b'exe-data'
            @property
            def headers(self):
                return {'Content-Length': '8'}
        monkeypatch.setattr(urllib.request, 'urlopen', lambda *a, **kw: FakeStream())
        updater = StandaloneUpdater()
        result = updater.download('2.0.9')
        assert result is not None
        assert result.exists()
        assert result.read_bytes() == b'exe-data'
        assert result.name == 'PalworldSaveTools-V2.0.9-win.exe'

    def test_download_cancel(self, monkeypatch, tmp_path):
        monkeypatch.setattr(sys, 'platform', 'win32')
        monkeypatch.setattr(tempfile, 'mkdtemp', lambda **kw: str(tmp_path))
        import urllib.request
        _read_count = [0]
        class FakeStream:
            def __enter__(self):
                return self
            def __exit__(self, *a):
                pass
            def read(self, n):
                _read_count[0] += 1
                if _read_count[0] > 3:
                    return b''
                return b'x'
            @property
            def headers(self):
                return {'Content-Length': '100'}
        monkeypatch.setattr(urllib.request, 'urlopen', lambda *a, **kw: FakeStream())
        updater = StandaloneUpdater()
        result = updater.download('2.0.9', cancel_check=lambda: True)
        assert result is None

    def test_apply_and_restart_creates_helper(self, monkeypatch, tmp_path):
        monkeypatch.setattr(sys, 'argv', [str(tmp_path / 'pst.exe')])
        monkeypatch.setattr(tempfile, 'mkdtemp', lambda **kw: str(tmp_path / 'temp'))
        (tmp_path / 'temp').mkdir(exist_ok=True)
        new_exe = tmp_path / 'temp' / 'PalworldSaveTools-V2.0.9-win.exe'
        new_exe.write_bytes(b'new-exe')
        import subprocess
        calls = []
        monkeypatch.setattr(subprocess, 'Popen', lambda *a, **kw: (calls.append(a[0]), type('P', (), {'poll': lambda s: 0, 'wait': lambda s: 0})())[1])
        updater = StandaloneUpdater()
        updater.downloaded_file = new_exe
        result = updater.apply_and_restart()
        assert result is True
        assert len(calls) == 1
        helper = Path(calls[0][1])
        assert helper.name == 'update_helper.py'


def test_get_update_settings_fallback(monkeypatch):
    from resource_resolver import get_user_config_dir
    user_cfg = Path(get_user_config_dir()) / 'config.json'
    if user_cfg.exists():
        user_cfg.unlink()
    settings = get_update_settings()
    assert isinstance(settings, dict)
    assert 'check_updates' in settings


def test_save_update_settings_roundtrip(monkeypatch):
    from resource_resolver import get_user_config_dir
    cfg_dir = Path(get_user_config_dir())
    cfg_dir.mkdir(parents=True, exist_ok=True)
    cfg_path = cfg_dir / 'config.json'
    if cfg_path.exists():
        cfg_path.unlink()
    save_update_settings({'check_updates': False, 'auto_update': False})
    assert cfg_path.exists()
    result = get_update_settings()
    assert result.get('check_updates') is False
