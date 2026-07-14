import os
import sys
import re
import ssl
import json
from palsav import json_tools
import subprocess
import tempfile
import shutil
import time
import atexit
import urllib.request
from pathlib import Path
from typing import Optional, Callable, Dict, Tuple
from palworld_aio import constants
GIT_REPO_URL = 'https://github.com/deafdudecomputers/PalworldSaveTools.git'
STABLE_BRANCH = 'main'
STABLE_VERSION_URL = 'https://api.github.com/repos/deafdudecomputers/PalworldSaveTools/releases/latest'
RELEASES_PAGE_URL = 'https://github.com/deafdudecomputers/PalworldSaveTools/releases/latest'
CHANGELOG_URL = 'https://raw.githubusercontent.com/deafdudecomputers/PalworldSaveTools/main/CHANGELOG.md'

def _platform_asset_suffix():
    if sys.platform == 'win32':
        return 'win.exe'
    elif sys.platform == 'darwin':
        return 'macos.dmg'
    else:
        return 'linux.AppImage'
def get_update_settings() -> Dict:
    from resource_resolver import get_user_config_dir
    from common import get_src_directory, is_standalone
    config_path = os.path.join(get_user_config_dir(), 'config.json')
    if not os.path.exists(config_path):
        config_path = os.path.join(get_src_directory(), 'data', 'configs', 'config.json')
    standalone = is_standalone()
    if standalone:
        defaults = {'auto_update': True, 'check_updates': True}
    else:
        defaults = {'git_pull': True, 'check_updates': True}
    try:
        config = json_tools.load(config_path)
        defaults.update({k: config.get(k, v) for k, v in defaults.items()})
    except:
        pass
    return defaults
def save_update_settings(settings: Dict):
    from resource_resolver import get_user_config_dir
    config_path = os.path.join(get_user_config_dir(), 'config.json')
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    standalone = False
    try:
        from common import is_standalone
        standalone = is_standalone()
    except:
        pass
    config = {}
    try:
        config = json_tools.load(config_path)
    except:
        pass
    if standalone:
        for key in ['auto_update', 'check_updates']:
            if key in settings:
                config[key] = settings[key]
    else:
        for key in ['git_pull', 'check_updates']:
            if key in settings:
                config[key] = settings[key]
    json_tools.dump(config, config_path)
class SourceUpdater:
    @staticmethod
    def get_project_root() -> Path:
        try:
            result = subprocess.run(['git', 'rev-parse', '--show-toplevel'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return Path(result.stdout.strip())
        except:
            pass
        return Path(__file__).resolve().parent.parent.parent
    @staticmethod
    def get_current_branch() -> str:
        try:
            result = subprocess.run(['git', 'branch', '--show-current'], capture_output=True, text=True, timeout=10, cwd=SourceUpdater.get_project_root())
            if result.returncode == 0:
                branch = result.stdout.strip()
                return branch if branch else 'main'
        except:
            pass
        return 'main'
    @staticmethod
    def has_uncommitted_changes() -> bool:
        try:
            result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True, timeout=10, cwd=SourceUpdater.get_project_root())
            return bool(result.stdout.strip())
        except:
            return False
    @staticmethod
    def git_pull(branch: str=None, progress_callback: Callable=None) -> Tuple[bool, str]:
        if not branch:
            branch = SourceUpdater.get_current_branch()
        if progress_callback:
            progress_callback('Pulling updates...', 30)
        try:
            result = subprocess.run(['git', 'pull', 'origin', branch], capture_output=True, text=True, timeout=120, cwd=SourceUpdater.get_project_root())
            if result.returncode != 0:
                return (False, result.stderr or 'Git pull failed')
            if progress_callback:
                progress_callback('Update complete!', 100)
            return (True, 'Successfully updated')
        except Exception as e:
            return (False, str(e))
    @staticmethod
    def fetch_remote(branch: str=None) -> bool:
        try:
            cmd = ['git', 'fetch', 'origin']
            if branch:
                cmd.append(branch)
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60, cwd=SourceUpdater.get_project_root())
            return result.returncode == 0
        except:
            return False
    @staticmethod
    def get_local_commit(branch: str=None) -> Optional[str]:
        if not branch:
            branch = SourceUpdater.get_current_branch()
        try:
            result = subprocess.run(['git', 'rev-parse', branch], capture_output=True, text=True, timeout=10, cwd=SourceUpdater.get_project_root())
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        return None
    @staticmethod
    def get_remote_commit(branch: str) -> Optional[str]:
        try:
            result = subprocess.run(['git', 'rev-parse', f'origin/{branch}'], capture_output=True, text=True, timeout=10, cwd=SourceUpdater.get_project_root())
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        return None
    @staticmethod
    def check_for_updates(branch: str=None) -> Dict:
        if not branch:
            branch = SourceUpdater.get_current_branch()
        SourceUpdater.fetch_remote(branch)
        local_commit = SourceUpdater.get_local_commit(branch)
        remote_commit = SourceUpdater.get_remote_commit(branch)
        has_update = False
        if local_commit and remote_commit:
            has_update = local_commit != remote_commit
        return {'branch': branch, 'local_commit': local_commit, 'remote_commit': remote_commit, 'update_available': has_update}
class StandaloneUpdater:
    def __init__(self):
        self.install_dir = Path(sys.executable).parent
        self.temp_dir = Path(tempfile.mkdtemp(prefix='pst_update_'))
        self.downloaded_file = None
        self.downloaded_name = None
        atexit.register(self.cleanup)
    def check_version(self) -> Dict:
        try:
            context = ssl._create_unverified_context()
            req = urllib.request.Request(
                STABLE_VERSION_URL,
                headers={
                    'User-Agent': 'PalworldSaveTools/2.0',
                    'Accept': 'application/vnd.github.v3+json',
                },
            )
            with urllib.request.urlopen(req, timeout=10, context=context) as r:
                data = json.loads(r.read().decode('utf-8'))
            tag = data.get('tag_name', '') or ''
            latest = tag.lstrip('v') or None
            suffix = _platform_asset_suffix()
            asset_name = None
            for a in data.get('assets', []):
                name = a.get('name', '')
                if name.endswith(suffix):
                    asset_name = name
                    break
            try:
                from common import get_versions
                local, _ = get_versions()
            except:
                local = '0.0.0'
            if not latest:
                return {'local': local, 'latest': None, 'update_available': False}
            local_tuple = tuple((int(x) for x in local.split('.')))
            latest_tuple = tuple((int(x) for x in latest.split('.')))
            return {'local': local, 'latest': latest, 'update_available': latest_tuple > local_tuple, 'asset_name': asset_name}
        except Exception as e:
            return {'local': None, 'latest': None, 'update_available': False, 'error': str(e)}
    def download(self, version: str, progress_callback: Callable=None, cancel_check: Callable=None) -> Optional[Path]:
        suffix = _platform_asset_suffix()
        asset_name = f'PalworldSaveTools-V{version}-{suffix}'
        url = f'https://github.com/deafdudecomputers/PalworldSaveTools/releases/download/v{version}/{asset_name}'
        exe_path = self.temp_dir / asset_name
        try:
            context = ssl._create_unverified_context()
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=30, context=context) as r:
                total_size = int(r.headers.get('Content-Length', 0))
                downloaded = 0
                chunk_size = 8192
                with open(exe_path, 'wb') as f:
                    while True:
                        if cancel_check and cancel_check():
                            return None
                        chunk = r.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback and total_size > 0:
                            pct = int(downloaded / total_size * 100)
                            progress_callback(f'Downloading... {downloaded / (1024 * 1024):.1f} MB', pct)
            self.downloaded_file = exe_path
            self.downloaded_name = asset_name
            return exe_path
        except Exception as e:
            if progress_callback:
                progress_callback(f'Download failed: {e}', 0)
            return None
    def cleanup(self):
        try:
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir, ignore_errors=True)
        except:
            pass
    def apply_and_restart(self) -> bool:
        if not self.downloaded_file or not self.downloaded_file.exists():
            return False
        try:
            current_exe = Path(sys.executable)
            new_exe = self.downloaded_file
            helper_code = f'''import os, sys, time, shutil, subprocess
PARENT_PID = {os.getpid()}
CURRENT = r"{current_exe}"
NEW = r"{new_exe}"
INSTALL_DIR = r"{self.install_dir}"
def wait():
    while True:
        try:
            os.kill(PARENT_PID, 0)
            time.sleep(0.5)
        except:
            break
def replace():
    bak = str(CURRENT) + ".bak"
    try:
        if os.path.exists(bak):
            os.remove(bak)
    except:
        pass
    try:
        os.rename(str(CURRENT), bak)
    except:
        pass
    try:
        shutil.copy2(NEW, str(CURRENT))
        os.chmod(str(CURRENT), 0o755)
    except Exception as e:
        os.rename(bak, str(CURRENT))
        return False
    return True
def launch():
    if os.path.exists(str(CURRENT)):
        subprocess.Popen([str(CURRENT)], cwd=INSTALL_DIR)
if __name__ == '__main__':
    wait()
    time.sleep(1)
    if replace():
        launch()
'''
            helper_path = self.temp_dir / 'update_helper.py'
            with open(helper_path, 'w', encoding='utf-8') as f:
                f.write(helper_code)
            if os.name == 'nt':
                creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
                si = subprocess.STARTUPINFO()
                si.dwFlags = subprocess.STARTF_USESHOWWINDOW
                si.wShowWindow = subprocess.SW_HIDE
            else:
                creationflags = 0
                si = None
            subprocess.Popen([sys.executable, str(helper_path)], creationflags=creationflags, startupinfo=si, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception as e:
            print(f'Failed to spawn update helper: {e}')
            return False
def check_for_updates(branch: str=None) -> Dict:
    try:
        from common import is_standalone
        if is_standalone():
            updater = StandaloneUpdater()
            return updater.check_version()
        else:
            return SourceUpdater.check_for_updates(branch)
    except:
        updater = StandaloneUpdater()
        return updater.check_version()
def get_version_from_remote(branch: str=None) -> Optional[str]:
    try:
        context = ssl._create_unverified_context()
        req = urllib.request.Request(
            STABLE_VERSION_URL,
            headers={
                'User-Agent': 'PalworldSaveTools/2.0',
                'Accept': 'application/vnd.github.v3+json',
            },
        )
        with urllib.request.urlopen(req, timeout=10, context=context) as r:
            data = json.loads(r.read().decode('utf-8'))
        tag = data.get('tag_name', '') or ''
        return tag.lstrip('v') or None
    except:
        return None