import os, sys, subprocess, configparser
from palsav import json_tools
from resource_resolver import get_base_dir, get_src_dir, get_resources_dir, resource_path
APP_NAME = 'PalworldSaveTools'
APP_VERSION = '2.0.7'
TESTING_VER = '2.0.7'
GAME_VERSION = '1.0.0'
def get_base_directory():
    return get_base_dir()
def get_src_directory():
    return get_src_dir()
def get_resources_directory():
    return get_resources_dir()
ICON_PATH = resource_path(get_base_dir(), 'icon.ico')
BACKUP_BASE_DIR = os.path.join(get_base_dir(), 'Backups')
def get_backup_directory(tool_name):
    return os.path.join(BACKUP_BASE_DIR, tool_name)
BACKUP_DIRS = {'all_in_one_tools': 'AllinOneTools', 'slot_injector': 'Slot Injector', 'character_transfer': 'Character Transfer', 'fix_host_save': 'Fix Host Save', 'restore_map': 'Restore Map'}
def is_frozen():
    return getattr(sys, 'frozen', False)
def get_python_executable():
    if is_frozen():
        return sys.executable
    else:
        return sys.executable
def get_versions():
    return (APP_VERSION, GAME_VERSION)
def get_display_version():
    try:
        app_tuple = tuple(int(x) for x in APP_VERSION.split('.'))
        testing_tuple = tuple(int(x) for x in TESTING_VER.split('.'))
        if testing_tuple > app_tuple:
            return f'{TESTING_VER} (testing)'
    except:
        pass
    return APP_VERSION
def is_standalone():
    if is_frozen():
        return True
    from boot_paths import CONFIG_DIR
    cfg_path = os.path.join(str(CONFIG_DIR), 'runtime.cfg')
    try:
        cfg = configparser.ConfigParser()
        cfg.read(cfg_path)
        return cfg.getboolean('build', 'standalone', fallback=False)
    except:
        return False
def get_current_version():
    return APP_VERSION
def get_update_settings():
    from boot_paths import CONFIG_DIR
    cfg_path = os.path.join(str(CONFIG_DIR), 'config.json')
    if is_standalone():
        defaults = {'auto_update': True, 'check_updates': True}
    else:
        defaults = {'git_pull': True, 'check_updates': True}
    try:
        config = json_tools.load(cfg_path)
        defaults.update({k: config.get(k, v) for k, v in defaults.items()})
    except:
        pass
    return defaults
def save_update_settings(settings):
    from boot_paths import CONFIG_DIR
    cfg_path = os.path.join(str(CONFIG_DIR), 'config.json')
    config = {}
    try:
        config = json_tools.load(cfg_path)
    except:
        pass
    if is_standalone():
        for key in ['auto_update', 'check_updates']:
            if key in settings:
                config[key] = settings[key]
    else:
        for key in ['git_pull', 'check_updates']:
            if key in settings:
                config[key] = settings[key]
    json_tools.dump(config, cfg_path)
def open_file_with_default_app(file_path):
    import platform
    if not os.path.exists(file_path):
        print(f'File not found: {file_path}')
        return False
    try:
        if platform.system() == 'Windows':
            os.startfile(file_path)
        elif platform.system() == 'Darwin':
            import subprocess
            subprocess.run(['open', file_path])
        else:
            import subprocess
            subprocess.run(['xdg-open', file_path])
        return True
    except Exception as e:
        print(f'Error opening file {file_path}: {e}')
        return False
def unlock_self_folder():
    if getattr(sys, 'frozen', False):
        folder = os.path.dirname(os.path.abspath(sys.executable))
    else:
        script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        src_dir = os.path.dirname(script_dir)
        folder = os.path.dirname(src_dir)
    folder_escaped = folder.replace('\\', '\\\\').replace("'", "''")
    parent_pid = os.getpid()
    ps_command = f"""$ErrorActionPreference='SilentlyContinue'; $target='{folder_escaped}'; $pPid={parent_pid}; $currentPid=$PID; function Global-Nuke {{   try {{     $procs=Get-Process | Where-Object {{ $_.Path -like "$target*" -and $_.Id -ne $PID }};     $handleProcs=@();     try {{       $allProcs=Get-Process;       foreach($p in $allProcs){{         if($p.Id -ne $PID){{           try {{             $handles=Get-WmiObject Win32_ProcessHandle -Filter "ProcessId=$($p.Id)" 2>$null;             foreach($h in $handles){{               if($h.Handle -and $h.Handle.Name -like "$target*"){{                 $handleProcs +=$p;                 break;               }}             }}           }} catch {{ }}         }}       }}     }} catch {{ }}     $allProcsToKill=$procs + $handleProcs | Select-Object -Unique;     foreach($p in $allProcsToKill){{       try {{         Stop-Process -Id $p.Id -Force -ErrorAction Stop;       }} catch {{         try {{ taskkill /F /T /PID $p.Id /NoWindow 2>$null; }} catch {{ }}       }}     }}   }} catch {{ }} }}; $monitorCount=0; while($true){{   Start-Sleep -Milliseconds 500;   $monitorCount++;   try {{     $parent=Get-Process -Id $pPid -ErrorAction Stop;   }} catch {{     Global-Nuke;     break;   }} }}; Stop-Process -Id $currentPid -Force"""
    si = subprocess.STARTUPINFO()
    si.dwFlags = subprocess.STARTF_USESHOWWINDOW
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    si.wShowWindow = subprocess.SW_HIDE
    try:
        subprocess.Popen(['powershell', '-WindowStyle', 'Hidden', '-ExecutionPolicy', 'Bypass', '-Command', ps_command], startupinfo=si, creationflags=subprocess.CREATE_NO_WINDOW, cwd=os.path.dirname(folder))
    except Exception:
        pass
