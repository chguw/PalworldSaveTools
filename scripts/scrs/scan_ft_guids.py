import sys, os, json, mmap, shutil, subprocess
from pathlib import Path
_SCRIPT_DIR = Path(__file__).resolve().parent
_PROJECT_DIR = _SCRIPT_DIR.parent.parent
_VENV_DIR = _PROJECT_DIR / '.venv'
_SRC_DIR = _PROJECT_DIR / 'src'
def _venv_python():
    return _VENV_DIR / 'Scripts' / 'python.exe' if os.name == 'nt' else _VENV_DIR / 'bin' / 'python'
def _ensure_venv():
    vpy = _venv_python()
    if vpy.exists():
        return True
    print('Creating virtual environment...')
    if _VENV_DIR.exists():
        shutil.rmtree(_VENV_DIR, ignore_errors=True)
    if subprocess.run(['uv', 'venv', str(_VENV_DIR)]).returncode != 0:
        print('Failed to create venv')
        return False
    print('Installing dependencies...')
    if subprocess.run(['uv', 'sync'], cwd=str(_PROJECT_DIR)).returncode != 0:
        print('Failed to install dependencies')
        if _VENV_DIR.exists():
            shutil.rmtree(_VENV_DIR, ignore_errors=True)
        return False
    uv_lock = _PROJECT_DIR / 'uv.lock'
    if uv_lock.exists():
        uv_lock.unlink()
    print('Environment ready')
    return True
def _load_save_tools():
    sys.path.insert(0, str(_SRC_DIR))
    global decompress_sav_to_gvas, GvasFile, PALWORLD_TYPE_HINTS, SKP_PALWORLD_CUSTOM_PROPERTIES
    from palsav.core import decompress_sav_to_gvas
    from palsav.gvas import GvasFile
    from palsav.paltypes import PALWORLD_TYPE_HINTS
    import palobject
    SKP_PALWORLD_CUSTOM_PROPERTIES = palobject.SKP_PALWORLD_CUSTOM_PROPERTIES
def sav_to_gvasfile(path):
    if 'decompress_sav_to_gvas' not in globals():
        _load_save_tools()
    file_size = os.path.getsize(path)
    if file_size > 100 * 1024 * 1024:
        with open(path, 'rb') as f:
            with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                raw_gvas, _ = decompress_sav_to_gvas(mm.read())
    else:
        with open(path, 'rb') as f:
            data = f.read()
        raw_gvas, _ = decompress_sav_to_gvas(data)
    return GvasFile.read(raw_gvas, PALWORLD_TYPE_HINTS, SKP_PALWORLD_CUSTOM_PROPERTIES, allow_nan=True)
def get_record_data(gvas):
    props = gvas.properties if hasattr(gvas, 'properties') else gvas.get('properties', {})
    save_data = props.get('SaveData', {}).get('value', {})
    if not save_data:
        return None
    return save_data.get('RecordData', {}).get('value', {})
def extract_map_keys(record_data, key):
    prop = record_data.get(key, {})
    if not prop:
        return set()
    return {e['key'] for e in prop.get('value', []) if e.get('value', False)}
def extract_world_map_flags(record_data):
    prop = record_data.get('UnlockedWorldMapFlags', {})
    if not prop:
        return {}
    return {e['key']: e.get('value', False) for e in prop.get('value', [])}
def scan_saves(players_dir):
    per_player_ft = []
    area_keys = set()
    world_flags = {}
    area_barrier = set()
    scanned = 0
    for fname in sorted(os.listdir(players_dir)):
        if not fname.endswith('.sav') or '_dps' in fname:
            continue
        path = os.path.join(players_dir, fname)
        try:
            gvas = sav_to_gvasfile(path)
            record = get_record_data(gvas)
            if record is None:
                continue
            scanned += 1
            per_player_ft.append(extract_map_keys(record, 'FastTravelPointUnlockFlag'))
            area_keys |= extract_map_keys(record, 'FindAreaFlagMap')
            wf = extract_world_map_flags(record)
            for k, v in wf.items():
                if v:
                    world_flags[k] = True
            area_barrier |= extract_map_keys(record, 'AreaBarrierUnlockFlags')
        except Exception as e:
            print(f'  Skipping {fname}: {e}')
    return (scanned, per_player_ft, area_keys, world_flags, area_barrier)
def main():
    vpy = _venv_python()
    if not vpy.exists() or os.path.abspath(sys.executable) != os.path.abspath(str(vpy)):
        if not _ensure_venv():
            sys.exit(1)
        os.execv(str(vpy), [str(vpy), __file__] + sys.argv[1:])
    saves_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), '..', '..', 'TestSaves', 'PylarUpdated', 'Players')
    output = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(__file__), '..', '..', 'resources', 'game_data', 'reference_unlock_data.json')
    if os.path.isfile(saves_dir):
        print(f'Scanning single file: {saves_dir}')
        gvas = sav_to_gvasfile(saves_dir)
        record = get_record_data(gvas)
        if record is None:
            print('No RecordData found')
            sys.exit(1)
        scanned = 1
        per_player_ft = [extract_map_keys(record, 'FastTravelPointUnlockFlag')]
        area_keys = extract_map_keys(record, 'FindAreaFlagMap')
        wf = extract_world_map_flags(record)
        world_flags = {k: True for k, v in wf.items() if v}
        area_barrier = extract_map_keys(record, 'AreaBarrierUnlockFlags')
    elif os.path.isdir(saves_dir):
        print(f'Scanning: {saves_dir}')
        scanned, per_player_ft, area_keys, world_flags, area_barrier = scan_saves(saves_dir)
    else:
        print(f'Not found: {saves_dir}')
        sys.exit(1)
    print(f'Scanned {scanned} player save(s)')
    ft_guids = set.union(*per_player_ft) if per_player_ft else set()
    ref_path = os.path.join(os.path.dirname(__file__), '..', '..', 'resources', 'game_data', 'reference_unlock_data.json')
    if os.path.exists(ref_path):
        try:
            old_ref = json.load(open(ref_path, 'r'))
            old_ft = set(old_ref.get('FastTravelPointUnlockFlag_guids', []))
            before = len(ft_guids)
            ft_guids |= old_ft
            if len(ft_guids) > before:
                print(f'  Added {len(ft_guids) - before} FT GUIDs from existing reference')
            old_area_keys = set(old_ref.get('FindAreaFlagMap_keys', []))
            before = len(area_keys)
            area_keys |= old_area_keys
            if len(area_keys) > before:
                print(f'  Added {len(area_keys) - before} area keys from existing reference')
            old_world_flags = old_ref.get('UnlockedWorldMapFlags', {})
            for k, v in old_world_flags.items():
                if v:
                    world_flags.setdefault(k, True)
            old_barrier = set(old_ref.get('AreaBarrierUnlockFlags_guids', []))
            before = len(area_barrier)
            area_barrier |= old_barrier
            if len(area_barrier) > before:
                print(f'  Added {len(area_barrier) - before} barrier GUIDs from existing reference')
        except Exception:
            pass
    result = {'FastTravelPointUnlockFlag_guids': sorted(ft_guids), 'FindAreaFlagMap_keys': sorted(area_keys), 'UnlockedWorldMapFlags': world_flags or {'MainMap': True, 'Tree': True}, 'AreaBarrierUnlockFlags_guids': sorted(area_barrier)}
    with open(output, 'w') as f:
        json.dump(result, f, indent=2)
    print(f'Written: {output}')
    print(f'  FT points: {len(ft_guids)}')
    print(f'  Area flags: {len(area_keys)}')
    print(f'  World map flags: {len(world_flags)}')
    print(f'  Area barriers: {len(area_barrier)}')
if __name__ == '__main__':
    main()