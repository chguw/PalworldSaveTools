import os
import sys
import json
import re
import shutil
import subprocess
from pathlib import Path
import io
import itertools
import threading
import time
VENV_DIR = Path(__file__).resolve().parent.parent.parent / '.venv'
def _venv_python():
    if os.name == 'nt':
        return VENV_DIR / 'Scripts' / 'python.exe'
    return VENV_DIR / 'bin' / 'python'
def _ensure_venv():
    vpy = _venv_python()
    if vpy.exists():
        return True
    print('Creating virtual environment...')
    if VENV_DIR.exists():
        shutil.rmtree(VENV_DIR, ignore_errors=True)
    result = subprocess.run(['uv', 'venv', str(VENV_DIR)])
    if result.returncode != 0:
        print('Failed to create venv')
        return False
    print('Installing dependencies...')
    result = subprocess.run(['uv', 'sync'], cwd=str(Path(__file__).resolve().parent.parent.parent))
    uv_lock = Path(__file__).resolve().parent.parent.parent / 'uv.lock'
    if uv_lock.exists():
        uv_lock.unlink()
    if result.returncode == 0:
        print('Environment ready')
        return True
    print('Failed to install dependencies')
    if VENV_DIR.exists():
        shutil.rmtree(VENV_DIR, ignore_errors=True)
    return False
def _spinner(label):
    spinner_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    stop_event = threading.Event()
    out = sys.__stdout__
    try:
        out.encoding
    except AttributeError:
        pass
    def _spin():
        for c in itertools.cycle(spinner_chars):
            if stop_event.is_set():
                break
            try:
                out.write(f'\r  {c} {label}')
                out.flush()
            except UnicodeEncodeError:
                out.write(f'\r  . {label}')
                out.flush()
            time.sleep(0.08)
        try:
            out.write('\r')
            out.flush()
        except UnicodeEncodeError:
            pass
    t = threading.Thread(target=_spin, daemon=True)
    t.start()
    return stop_event
BASE_DIR = Path(__file__).resolve().parent.parent.parent
RESOURCES_DIR = BASE_DIR / 'resources' / 'game_data'
ICONS_DIR = RESOURCES_DIR / 'icons'
EXPORTS_DIR = BASE_DIR / 'Exports' / 'Pal' / 'Content' / 'Pal' / 'DataTable'
EXPORT_TEXTURES_DIR = BASE_DIR / 'Exports' / 'Pal' / 'Content' / 'Pal' / 'Texture'
EXPORT_L10N_DIR = BASE_DIR / 'Exports' / 'Pal' / 'Content' / 'L10N' / 'en' / 'Pal' / 'DataTable' / 'Text'
EXPORT_TEXTURES_DIR_FAST = BASE_DIR / 'Exports' / 'Pal' / 'Content' / 'Pal' / 'Texture'
OTHER_ICON_DIR = BASE_DIR / 'Exports' / 'Pal' / 'Content' / 'Others'
_ELEMENT_DEFS = [{'name': 'Normal', 'display': 'Neutral', 'index': 0, 'color': '#9CA3AF'}, {'name': 'Fire', 'display': 'Fire', 'index': 1, 'color': '#EF4444'}, {'name': 'Water', 'display': 'Water', 'index': 2, 'color': '#3B82F6'}, {'name': 'Electricity', 'display': 'Electric', 'index': 3, 'color': '#FBBF24'}, {'name': 'Leaf', 'display': 'Grass', 'index': 4, 'color': '#4ADE80'}, {'name': 'Dark', 'display': 'Dark', 'index': 5, 'color': '#6B21A8'}, {'name': 'Dragon', 'display': 'Dragon', 'index': 6, 'color': '#818CF8'}, {'name': 'Earth', 'display': 'Earth', 'index': 7, 'color': '#A78BFA'}, {'name': 'Ice', 'display': 'Ice', 'index': 8, 'color': '#67E8F9'}]
def _build_icon_lookup():
    icon_name_to_path = {}
    for search_dir in [str(EXPORT_TEXTURES_DIR_FAST), str(OTHER_ICON_DIR)]:
        if os.path.exists(search_dir):
            for root, dirs, files in os.walk(search_dir):
                for f in files:
                    stem = os.path.splitext(f)[0].lower()
                    icon_name_to_path[stem] = os.path.join(root, f)
    return icon_name_to_path
icon_name_to_path = {}
def ensure_dir(directory: Path):
    directory.mkdir(parents=True, exist_ok=True)
def load_export_json(rel_path: str) -> dict | list | None:
    path = EXPORTS_DIR / rel_path
    if not path.exists():
        print(f'  WARNING: Export file not found: {rel_path}')
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f'  ERROR loading {rel_path}: {e}')
        return None
def load_l10n_table(filename: str) -> dict[str, str]:
    path = EXPORT_L10N_DIR / filename
    if not path.exists():
        print(f'  WARNING: L10N file not found: {filename}')
        return {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f'  ERROR loading L10N {filename}: {e}')
        return {}
    result = {}
    all_rows = {}
    if isinstance(data, list):
        for table in data:
            if isinstance(table, dict):
                rows = table.get('Rows', {})
                if rows:
                    all_rows.update(rows)
    elif isinstance(data, dict):
        rows = data.get('Rows', {})
        if rows:
            all_rows.update(rows)
    for key, row in all_rows.items():
        if isinstance(row, dict):
            text_data = row.get('TextData', row)
            source = text_data.get('SourceString', '')
            if source:
                result[key] = source
    return result
_LEGACY_FALLBACK = {'paldata.json': 'characters.json', 'npcdata.json': 'characters.json', 'passivedata.json': 'skills.json', 'skilldata.json': 'skills.json', 'elementdata.json': 'skills.json', 'structuredata.json': 'world.json', 'technologydata.json': 'world.json', 'labresearchdata.json': 'world.json', 'itemdata.json': 'items.json', 'items_dynamic.json': 'items.json', 'palpassivedata.json': 'skills.json'}
def load_resource_json(filename: str) -> dict:
    path = RESOURCES_DIR / filename
    if path.exists():
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    fb = _LEGACY_FALLBACK.get(filename)
    if fb:
        fb_path = RESOURCES_DIR / fb
        if fb_path.exists():
            try:
                with open(fb_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
    return {}
def save_resource_json(filename: str, data: dict | list):
    path = RESOURCES_DIR / filename
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f'  Saved: {filename} ({(len(data.get(list(data.keys())[0]) if isinstance(data, dict) and data else data) if isinstance(data, list) else len(data))} entries)')
def get_rows(data: list | dict) -> dict:
    if isinstance(data, dict):
        return data.get('Rows', {})
    rows = {}
    for table in data:
        if isinstance(table, dict):
            r = table.get('Rows', {})
            if r:
                rows.update(r)
            props = table.get('Properties', {})
            parent_tables = props.get('ParentTables', [])
            for parent in parent_tables:
                if isinstance(parent, dict):
                    obj_name = parent.get('ObjectName', '')
                    obj_path = parent.get('ObjectPath', '')
                    if obj_name:
                        m = re.search("'([^']+)'", obj_name)
                        if m:
                            parent_name = m.group(1)
                            pass
    return rows
def extract_icon_path(asset_path: str) -> str:
    if not asset_path:
        return None
    if '.' in asset_path:
        asset_path = asset_path[:asset_path.rindex('.')]
    filename = os.path.basename(asset_path)
    return filename
def find_icon_file(export_texture_path: str, icon_subdir: str) -> str | None:
    if not export_texture_path:
        return None
    clean_path = export_texture_path
    if '.' in clean_path:
        clean_path = clean_path[:clean_path.rindex('.')]
    filename = os.path.basename(clean_path)
    extensions_to_try = ['.webp', '.png', '.PNG', '.jpg', '.tga']
    search_patterns = [filename, filename.replace('_icon_normal', '_icon'), filename.replace('_icon_normal', '')]
    for ext in extensions_to_try:
        for pattern in search_patterns:
            search_dirs = []
            if icon_subdir == 'pals':
                search_dirs = [EXPORT_TEXTURES_DIR / 'PalIcon' / 'Normal', EXPORT_TEXTURES_DIR / 'PalIcon' / 'NPC']
            elif icon_subdir == 'items':
                search_dirs = [EXPORT_TEXTURES_DIR / 'Item', EXPORT_TEXTURES_DIR / 'UI' / 'InGame', EXPORT_TEXTURES_DIR / 'UI' / 'Common']
            elif icon_subdir == 'structures':
                search_dirs = [EXPORT_TEXTURES_DIR / 'BuildObject' / 'Icon', EXPORT_TEXTURES_DIR / 'BuildObject' / 'PNG']
            elif icon_subdir == 'technologies':
                search_dirs = [EXPORT_TEXTURES_DIR / 'UI' / 'Common']
            elif icon_subdir == 'passives':
                search_dirs = [EXPORT_TEXTURES_DIR / 'UI' / 'Common', EXPORT_TEXTURES_DIR / 'StatusParameterIcon']
            elif icon_subdir == 'elements':
                search_dirs = [EXPORT_TEXTURES_DIR / 'UI' / 'Common', EXPORT_TEXTURES_DIR / 'UI' / 'InGame']
            for search_dir in search_dirs:
                if search_dir.exists():
                    for found_file in search_dir.rglob(f'{pattern}{ext}'):
                        return f'/icons/{icon_subdir}/{found_file.name}'
    return None
def copy_icon_to_resources(export_path: Path, target_subdir: str) -> str | None:
    if not export_path.exists():
        return None
    target_dir = ICONS_DIR / target_subdir
    ensure_dir(target_dir)
    target_file = target_dir / export_path.name
    if not target_file.exists() or export_path.stat().st_mtime > target_file.stat().st_mtime:
        try:
            shutil.copy2(str(export_path), str(target_file))
        except Exception as e:
            print(f'    ERROR copying {export_path.name}: {e}')
            return None
    return f'/icons/{target_subdir}/{export_path.name}'
_ITEM_NAME_CACHE = {}
_STRUCT_NAME_CACHE = {}
_PAL_NAME_CACHE = {}
_SKILL_NAME_CACHE = {}
def _ensure_name_caches():
    if not _ITEM_NAME_CACHE:
        try:
            item_data = load_resource_json('items.json')
            for i in item_data.get('items', []):
                if isinstance(i, dict) and 'asset' in i and ('name' in i):
                    _ITEM_NAME_CACHE[i['asset'].lower()] = i['name']
        except Exception:
            pass
    if not _STRUCT_NAME_CACHE:
        try:
            struct_data = load_resource_json('world.json')
            for s in struct_data.get('structures', []):
                if isinstance(s, dict) and 'asset' in s and ('name' in s):
                    _STRUCT_NAME_CACHE[s['asset'].lower()] = s['name']
        except Exception:
            pass
    if not _PAL_NAME_CACHE:
        try:
            pal_data = load_resource_json('characters.json')
            for p in pal_data.get('pals', []):
                if isinstance(p, dict) and 'asset' in p and ('name' in p):
                    _PAL_NAME_CACHE[p['asset'].lower()] = p['name']
        except Exception:
            pass
    if not _SKILL_NAME_CACHE:
        try:
            skill_data = load_resource_json('skills.json')
            for s in skill_data.get('skills', []):
                if isinstance(s, dict) and 'asset' in s and ('name' in s):
                    _SKILL_NAME_CACHE[s['asset'].lower()] = s['name']
        except Exception:
            pass
def resolve_rich_text(text: str) -> str:
    import re
    _ensure_name_caches()
    _RARITY_MAP = {'RARITY_COMMON': 'Common', 'RARITY_UNCOMMON': 'Uncommon', 'RARITY_RARE': 'Rare', 'RARITY_EPIC': 'Epic', 'RARITY_LEGENDARY': 'Legendary'}
    def _replace(m):
        tag_type = m.group(1).lower()
        asset_id = m.group(2).lower()
        if tag_type == 'itemname':
            name = _ITEM_NAME_CACHE.get(asset_id, '')
        elif tag_type == 'mapobjectname' or tag_type == 'mapobjectname':
            name = _STRUCT_NAME_CACHE.get(asset_id, '')
        elif tag_type == 'charactername':
            name = _PAL_NAME_CACHE.get(asset_id, '')
        elif tag_type == 'activeskillname':
            name = _SKILL_NAME_CACHE.get(asset_id, '')
        else:
            name = ''
        if name and '<' not in name:
            return name
        return asset_id
    def _replace_rarity(m):
        return _RARITY_MAP.get(m.group(1), m.group(1))
    def _ui_common_readable(m):
        id_val = m.group(1)
        parts = id_val.split('_')
        tail = parts[-1] if parts else id_val
        tail = tail[0].upper() + tail[1:].lower() if tail else ''
        return tail
    text = re.sub('<(itemName|mapObjectName|characterName|activeSkillName)\\s+id=\\|([^|]+)\\|[^>]*/>', _replace, text, flags=re.I)
    text = re.sub('<uiCommon\\s+id=\\|(RARITY_\\w+)\\|[^/>]*/>', _replace_rarity, text, flags=re.I)
    text = re.sub('<uiCommon\\s+id=\\|([^|]+)\\|[^/>]*/>', _ui_common_readable, text, flags=re.I)
    text = re.sub('<Status_Up>([^<]*)</>', '\\1 ', text)
    text = re.sub('<Status_Keyword>([^<]*)</>', '\\1 ', text)
    text = re.sub('</>', '', text)
    text = re.sub('<[^>]+>', '', text).strip()
    text = re.sub('\\s+([\\)\\]\\}\\.\\,\\;\\:\\!\\?])', '\\1', text)
    return text
def find_and_copy_icon(search_name: str, target_subdir: str, export_subdirs: list[Path]=None) -> str | None:
    if not search_name:
        return None
    name_lower = search_name.lower()
    target_dir = ICONS_DIR / target_subdir
    ensure_dir(target_dir)
    search_terms = [name_lower]
    no_zero = re.sub('_0+(\\d)', '_\\1', name_lower)
    if no_zero != name_lower:
        search_terms.append(no_zero)
    seen = set()
    unique_terms = []
    for t in search_terms:
        if t not in seen:
            seen.add(t)
            unique_terms.append(t)
    for term in unique_terms:
        full_path = icon_name_to_path.get(term)
        if full_path:
            target_file = target_dir / os.path.basename(full_path)
            if not target_file.exists():
                shutil.copy2(full_path, str(target_file))
            return f'/icons/{target_subdir}/{os.path.basename(full_path)}'
    for term in unique_terms:
        with_ti = f't_itemicon_{term}'
        full_path = icon_name_to_path.get(with_ti)
        if full_path:
            target_file = target_dir / os.path.basename(full_path)
            if not target_file.exists():
                shutil.copy2(full_path, str(target_file))
            return f'/icons/{target_subdir}/{os.path.basename(full_path)}'
    for term in unique_terms:
        with_t = f't_{term}'
        full_path = icon_name_to_path.get(with_t)
        if full_path:
            target_file = target_dir / os.path.basename(full_path)
            if not target_file.exists():
                shutil.copy2(full_path, str(target_file))
            return f'/icons/{target_subdir}/{os.path.basename(full_path)}'
    for term in unique_terms:
        with_ibo = f't_icon_buildobject_{term}'
        full_path = icon_name_to_path.get(with_ibo)
        if full_path:
            target_file = target_dir / os.path.basename(full_path)
            if not target_file.exists():
                shutil.copy2(full_path, str(target_file))
            return f'/icons/{target_subdir}/{os.path.basename(full_path)}'
    for term in unique_terms:
        with_ic = f't_icon_{term}'
        full_path = icon_name_to_path.get(with_ic)
        if full_path:
            target_file = target_dir / os.path.basename(full_path)
            if not target_file.exists():
                shutil.copy2(full_path, str(target_file))
            return f'/icons/{target_subdir}/{os.path.basename(full_path)}'
    if not name_lower.startswith('t_itemicon_'):
        tier_stripped = re.sub('_\\d+$', '', name_lower)
        if tier_stripped != name_lower:
            for try_term in [tier_stripped, f't_itemicon_{tier_stripped}', f't_{tier_stripped}']:
                full_path = icon_name_to_path.get(try_term)
                if full_path:
                    target_file = target_dir / os.path.basename(full_path)
                    if not target_file.exists():
                        shutil.copy2(full_path, str(target_file))
                    return f'/icons/{target_subdir}/{os.path.basename(full_path)}'
    best_match = None
    best_match_len = 0
    for term in unique_terms:
        for cache_key, full_path in icon_name_to_path.items():
            if term in cache_key and len(cache_key) > best_match_len:
                best_match = full_path
                best_match_len = len(cache_key)
    if best_match:
        target_file = target_dir / os.path.basename(best_match)
        if not target_file.exists():
            shutil.copy2(best_match, str(target_file))
        return f'/icons/{target_subdir}/{os.path.basename(best_match)}'
    return None
def update_pal_data():
    print('\n=== Updating Pal Data ===')
    export_data = load_export_json('Character/DT_PalCharacterIconDataTable.json')
    export_data_common = load_export_json('Character/DT_PalCharacterIconDataTable_Common.json')
    monster_param = load_export_json('Character/DT_PalMonsterParameter.json')
    monster_param_common = load_export_json('Character/DT_PalMonsterParameter_Common.json')
    pal_name_l10n = load_l10n_table('DT_PalNameText_Common.json')
    name_prefix_l10n = load_l10n_table('DT_NamePrefixText_Common.json')
    icon_rows = {}
    for data in [export_data, export_data_common]:
        if data:
            if isinstance(data, list):
                for table in data:
                    if isinstance(table, dict):
                        rows = table.get('Rows', {})
                        if rows:
                            icon_rows.update(rows)
            elif isinstance(data, dict):
                rows = data.get('Rows', {})
                if rows:
                    icon_rows.update(rows)
    monster_rows = {}
    for data in [monster_param, monster_param_common]:
        if data:
            if isinstance(data, list):
                for table in data:
                    if isinstance(table, dict):
                        rows = table.get('Rows', {})
                        if rows:
                            monster_rows.update(rows)
            elif isinstance(data, dict):
                rows = data.get('Rows', {})
                if rows:
                    monster_rows.update(rows)
    if not icon_rows and (not monster_rows):
        print('  No pal rows found in exports. Skipping.')
        return
    _pal_name_l10n_lower = {}
    for k, v in pal_name_l10n.items():
        _pal_name_l10n_lower[k.lower()] = v
    def _lookup_l10n(key: str) -> str | None:
        val = pal_name_l10n.get(key)
        if val:
            return val
        val = _pal_name_l10n_lower.get(key.lower())
        return val
    def _is_valid_name(name: str) -> bool:
        if not name:
            return False
        return name.lower() not in ('en_text', 'none', 'unidentified pal')
    def _get_pal_name(name_key: str) -> str | None:
        n = _lookup_l10n(name_key)
        return n if n and _is_valid_name(n) else None
    PREFIX_MAP = {'BOSS_': 'Boss', 'POLICE_': 'Police', 'PREDATOR_': 'Predator', 'GYM_': 'Gym', 'RAID_': 'Raid', 'SUMMON_': 'Summon'}
    def _get_base_l10n_name(raw_id: str) -> str | None:
        direct = _get_pal_name(f'PAL_NAME_{raw_id}')
        if direct:
            return direct
        for prefix_str in PREFIX_MAP:
            if raw_id.startswith(prefix_str):
                inner = raw_id[len(prefix_str):]
                inner_name = _get_pal_name(f'PAL_NAME_{inner}')
                if inner_name:
                    return inner_name
        return None
    def _append_prefix_label(base: str, pal_id: str) -> str:
        for pfx_key, pfx_label in PREFIX_MAP.items():
            if pal_id.startswith(pfx_key) and pfx_label not in base:
                return f'{base} ({pfx_label})'
        return base
    def _clean_pal_id(raw: str) -> str:
        name = raw
        for pfx in PREFIX_MAP:
            if name.startswith(pfx):
                name = name[len(pfx):]
                break
        name = name.replace('_', ' ').strip()
        import re
        name = re.sub('(?<=[a-z])(?=[A-Z])', ' ', name)
        return name if name else raw
    def resolve_pal_name(pal_id: str, monster_row: dict=None) -> str:
        if monster_row and isinstance(monster_row, dict):
            name_text_id = monster_row.get('OverrideNameTextID', '')
            base_name = _get_pal_name(name_text_id) if name_text_id else None
            if base_name:
                return _append_prefix_label(base_name, pal_id)
        base_name = _get_base_l10n_name(pal_id)
        if base_name:
            return _append_prefix_label(base_name, pal_id)
        fallback = _clean_pal_id(pal_id)
        return _append_prefix_label(fallback, pal_id)
    updated_pals = []
    pal_icon_subdirs = [EXPORT_TEXTURES_DIR / 'PalIcon' / 'Normal', EXPORT_TEXTURES_DIR / 'PalIcon' / 'NPC', EXPORT_TEXTURES_DIR / 'PalIcon' / 'SKin']
    processed_ids = set()
    for pal_id, row_data in sorted(icon_rows.items()):
        pal_id_lower = pal_id.lower()
        processed_ids.add(pal_id_lower)
        icon_data = row_data.get('Icon', {})
        icon_path = icon_data.get('AssetPathName', '') if isinstance(icon_data, dict) else ''
        if icon_path:
            icon_filename = icon_path.split('/')[-1].split('.')[0] if '.' in icon_path else icon_path.split('/')[-1]
            copied_icon = find_and_copy_icon(icon_filename, 'pals', pal_icon_subdirs)
        else:
            copied_icon = None
        monster_row = monster_rows.get(pal_id, None)
        display_name = resolve_pal_name(pal_id, monster_row)
        final_icon = copied_icon or f'/icons/pals/{pal_id}_icon_normal.webp'
        if not copied_icon:
            t_prefixed = f'/icons/pals/T_{pal_id}_icon_normal.webp'
            t_file = RESOURCES_DIR / t_prefixed.lstrip('/')
            if t_file.exists():
                final_icon = t_prefixed
            else:
                t_png = f'/icons/pals/T_{pal_id}_icon_normal.png'
                if (RESOURCES_DIR / t_png.lstrip('/')).exists():
                    final_icon = t_png
        pal_entry = {'name': display_name, 'asset': pal_id, 'icon': final_icon, 'elements': _build_element_icons(monster_row)}
        if monster_row and isinstance(monster_row, dict):
            el1 = monster_row.get('ElementType1', '')
            el2 = monster_row.get('ElementType2', '')
            if isinstance(el1, str) and el1.startswith('EPalElementType::'):
                el1 = el1.replace('EPalElementType::', '')
            if isinstance(el2, str) and el2.startswith('EPalElementType::'):
                el2 = el2.replace('EPalElementType::', '')
            ws_fields = ['EmitFlame', 'Watering', 'Seeding', 'GenerateElectricity', 'Handcraft', 'Collection', 'Deforest', 'Mining', 'OilExtraction', 'ProductMedicine', 'Cool', 'Transport', 'MonsterFarm']
            work_suit = {}
            for w in ws_fields:
                key = f'WorkSuitability_{w}'
                val = monster_row.get(key, 0)
                if isinstance(val, dict):
                    val = val.get('value', 0)
                work_suit[w] = int(val) if val else 0
            pal_entry['stats'] = {'hp': monster_row.get('Hp', 100), 'melee_attack': monster_row.get('MeleeAttack', 100), 'shot_attack': monster_row.get('ShotAttack', 100), 'defense': monster_row.get('Defense', 100), 'support': monster_row.get('Support', 100), 'craft_speed': monster_row.get('CraftSpeed', 100), 'max_full_stomach': monster_row.get('MaxFullStomach', 300), 'food_amount': monster_row.get('FoodAmount', 5), 'element_type1': el1, 'element_type2': el2, 'zukan_index': monster_row.get('ZukanIndex', 0), 'rarity': monster_row.get('Rarity', 0), 'size': monster_row.get('Size', 'EPalSizeType::XS') if isinstance(monster_row.get('Size', ''), str) else 'EPalSizeType::XS', 'run_speed': monster_row.get('RunSpeed', 400), 'ride_sprint_speed': monster_row.get('RideSprintSpeed', 700)}
            pal_entry['scaling'] = {'hp': monster_row.get('Hp', 100), 'attack': monster_row.get('MeleeAttack', 100), 'defense': monster_row.get('Defense', 100)}
            pal_entry['friendship_hp'] = monster_row.get('Friendship_HP', 0)
            pal_entry['friendship_shotattack'] = monster_row.get('Friendship_ShotAttack', 0)
            pal_entry['friendship_defense'] = monster_row.get('Friendship_Defense', 0)
            pal_entry['work_suitabilities'] = work_suit
        updated_pals.append(pal_entry)
    for pal_id in sorted(monster_rows.keys()):
        pal_id_lower = pal_id.lower()
        if pal_id_lower in processed_ids:
            continue
        processed_ids.add(pal_id_lower)
        monster_row = monster_rows[pal_id_lower] if pal_id_lower in monster_rows else monster_rows.get(pal_id, {})
        base_pal_id = pal_id
        if pal_id.startswith('BOSS_'):
            base_pal_id = pal_id[5:]
        elif pal_id.startswith('POLICE_'):
            base_pal_id = pal_id[7:]
        base_icon = None
        if base_pal_id != pal_id and base_pal_id in icon_rows:
            base_icon_data = icon_rows[base_pal_id].get('Icon', {})
            if isinstance(base_icon_data, dict):
                base_icon_path = base_icon_data.get('AssetPathName', '')
                if base_icon_path:
                    fn = base_icon_path.split('/')[-1].split('.')[0] if '.' in base_icon_path else base_icon_path.split('/')[-1]
                    base_icon = find_and_copy_icon(fn, 'pals', pal_icon_subdirs)
        icon_path = None
        if not base_icon:
            for fname in (f'T_{pal_id}_icon_normal', f'T_{pal_id}_icon', f'T_{pal_id}', f'T_{base_pal_id}_icon_normal', f'T_{base_pal_id}'):
                for ext in ['.webp', '.png', '.PNG']:
                    for subdir in pal_icon_subdirs:
                        if subdir.exists():
                            matches = list(subdir.rglob(f'{fname}{ext}'))
                            if matches:
                                copied = copy_icon_to_resources(matches[0], 'pals')
                                if copied:
                                    icon_path = copied
                                    break
                    if icon_path:
                        break
        display_name = resolve_pal_name(pal_id, monster_row)
        final_icon = icon_path or base_icon or f'/icons/pals/{pal_id}_icon_normal.webp'
        if not icon_path and not base_icon:
            t_prefixed = f'/icons/pals/T_{pal_id}_icon_normal.webp'
            t_file = RESOURCES_DIR / t_prefixed.lstrip('/')
            if t_file.exists():
                final_icon = t_prefixed
        pal_entry = {'name': display_name, 'asset': pal_id, 'icon': final_icon, 'elements': _build_element_icons(monster_row)}
        if monster_row and isinstance(monster_row, dict):
            el1 = monster_row.get('ElementType1', '')
            el2 = monster_row.get('ElementType2', '')
            if isinstance(el1, str) and el1.startswith('EPalElementType::'):
                el1 = el1.replace('EPalElementType::', '')
            if isinstance(el2, str) and el2.startswith('EPalElementType::'):
                el2 = el2.replace('EPalElementType::', '')
            ws_fields = ['EmitFlame', 'Watering', 'Seeding', 'GenerateElectricity', 'Handcraft', 'Collection', 'Deforest', 'Mining', 'OilExtraction', 'ProductMedicine', 'Cool', 'Transport', 'MonsterFarm']
            work_suit = {}
            for w in ws_fields:
                key = f'WorkSuitability_{w}'
                val = monster_row.get(key, 0)
                if isinstance(val, dict):
                    val = val.get('value', 0)
                work_suit[w] = int(val) if val else 0
            pal_entry['stats'] = {'hp': monster_row.get('Hp', 100), 'melee_attack': monster_row.get('MeleeAttack', 100), 'shot_attack': monster_row.get('ShotAttack', 100), 'defense': monster_row.get('Defense', 100), 'support': monster_row.get('Support', 100), 'craft_speed': monster_row.get('CraftSpeed', 100), 'max_full_stomach': monster_row.get('MaxFullStomach', 300), 'food_amount': monster_row.get('FoodAmount', 5), 'element_type1': el1, 'element_type2': el2, 'zukan_index': monster_row.get('ZukanIndex', 0), 'rarity': monster_row.get('Rarity', 0), 'size': monster_row.get('Size', 'EPalSizeType::XS') if isinstance(monster_row.get('Size', ''), str) else 'EPalSizeType::XS', 'run_speed': monster_row.get('RunSpeed', 400), 'ride_sprint_speed': monster_row.get('RideSprintSpeed', 700)}
            pal_entry['scaling'] = {'hp': monster_row.get('Hp', 100), 'attack': monster_row.get('MeleeAttack', 100), 'defense': monster_row.get('Defense', 100)}
            pal_entry['friendship_hp'] = monster_row.get('Friendship_HP', 0)
            pal_entry['friendship_shotattack'] = monster_row.get('Friendship_ShotAttack', 0)
            pal_entry['friendship_defense'] = monster_row.get('Friendship_Defense', 0)
            pal_entry['work_suitabilities'] = work_suit
        updated_pals.append(pal_entry)
        if display_name != pal_id:
            print(f"  Added new variant from MonsterParameter: {pal_id} -> '{display_name}'")
        else:
            print(f'  Added new variant from MonsterParameter: {pal_id}')
    result = {'pals': updated_pals}
    save_resource_json('paldata.json', result)
    print(f'  Total pals: {len(updated_pals)}')
def update_npc_data():
    print('\n=== Updating NPC Data ===')
    npc_icon_data = load_export_json('Character/DT_PalBossNPCIcon.json')
    npc_name_l10n = load_l10n_table('DT_HumanNameText_Common.json')
    _npc_l10n_lower = {k.lower(): v for k, v in npc_name_l10n.items()}
    def _resolve_npc_name(npc_id: str) -> str:
        key = f'NAME_{npc_id}'
        val = npc_name_l10n.get(key)
        if val and val.lower() not in ('en_text', 'none', ''):
            return val
        val = _npc_l10n_lower.get(key.lower())
        if val and val.lower() not in ('en_text', 'none', ''):
            return val
        return None
    all_rows = {}
    for data in [npc_icon_data]:
        if data:
            if isinstance(data, list):
                for table in data:
                    if isinstance(table, dict):
                        rows = table.get('Rows', {})
                        if rows:
                            all_rows.update(rows)
            elif isinstance(data, dict):
                rows = data.get('Rows', {})
                if rows:
                    all_rows.update(rows)
    if not all_rows:
        print('  No NPC rows found. Skipping.')
        return
    npc_icon_subdirs = [EXPORT_TEXTURES_DIR / 'PalIcon' / 'NPC', EXPORT_TEXTURES_DIR / 'PalIcon' / 'Normal']
    updated_npcs = []
    for npc_id, row_data in sorted(all_rows.items()):
        npc_id_lower = npc_id.lower()
        icon_data = row_data.get('Icon', {})
        icon_path = icon_data.get('AssetPathName', '') if isinstance(icon_data, dict) else ''
        copied_icon = None
        if icon_path:
            icon_filename = icon_path.split('/')[-1].split('.')[0] if '.' in icon_path else icon_path.split('/')[-1]
            copied_icon = find_and_copy_icon(icon_filename, 'npcs', npc_icon_subdirs)
        l10n_name = _resolve_npc_name(npc_id)
        npc_entry = {'name': l10n_name or npc_id, 'asset': npc_id, 'icon': copied_icon or f'/icons/npcs/{npc_id}_icon_normal.webp'}
        updated_npcs.append(npc_entry)
    result = {'npcs': updated_npcs}
    save_resource_json('npcdata.json', result)
def update_item_data():
    print('\n=== Updating Item Data ===')
    item_table = load_export_json('Item/DT_ItemDataTable.json')
    item_table_common = load_export_json('Item/DT_ItemDataTable_Common.json')
    icon_table = load_export_json('Item/DT_ItemIconDataTable.json')
    icon_table_common = load_export_json('Item/DT_ItemIconDataTable_Common.json')
    item_name_l10n = load_l10n_table('DT_ItemNameText_Common.json')
    item_desc_l10n = load_l10n_table('DT_ItemDescriptionText_Common.json')
    all_item_rows = {}
    for data in [item_table, item_table_common]:
        if data:
            if isinstance(data, list):
                for table in data:
                    if isinstance(table, dict):
                        rows = table.get('Rows', {})
                        if rows:
                            all_item_rows.update(rows)
            elif isinstance(data, dict):
                rows = data.get('Rows', {})
                if rows:
                    all_item_rows.update(rows)
    all_icon_rows = {}
    for data in [icon_table, icon_table_common]:
        if data:
            if isinstance(data, list):
                for table in data:
                    if isinstance(table, dict):
                        rows = table.get('Rows', {})
                        if rows:
                            all_icon_rows.update(rows)
            elif isinstance(data, dict):
                rows = data.get('Rows', {})
                if rows:
                    all_icon_rows.update(rows)
    if not all_item_rows:
        print('  No item rows found. Skipping.')
        return
    all_item_ids = set(all_item_rows.keys())
    item_icon_subdirs = [EXPORT_TEXTURES_DIR / 'Item', EXPORT_TEXTURES_DIR / 'Item' / 'Weapon', EXPORT_TEXTURES_DIR / 'UI' / 'InGame', EXPORT_TEXTURES_DIR / 'UI' / 'Main_Menu', EXPORT_TEXTURES_DIR / 'UI' / 'Common', EXPORT_TEXTURES_DIR.parent.parent / 'Others' / 'InventoryItemIcon' / 'Texture']
    def _is_valid_l10n_name(name: str) -> bool:
        if not name:
            return False
        return name.strip() not in ('', '-', 'en_text', 'en Text', 'None', 'none', 'ex Text')
    def resolve_item_name(item_id: str, item_row: dict) -> str:
        override = ''
        if isinstance(item_row, dict):
            override = item_row.get('OverrideName', '')
        if override and override != 'None' and (override in item_name_l10n):
            val = item_name_l10n[override]
            if _is_valid_l10n_name(val):
                return val
        standard_key = f'ITEM_NAME_{item_id}'
        if standard_key in item_name_l10n:
            val = item_name_l10n[standard_key]
            if _is_valid_l10n_name(val):
                return val
        if item_id in item_name_l10n:
            val = item_name_l10n[item_id]
            if _is_valid_l10n_name(val):
                return val
        return item_id
    def resolve_item_desc(item_id: str, item_row: dict) -> str:
        override = ''
        if isinstance(item_row, dict):
            override = item_row.get('OverrideDescription', '')
        if override and override != 'None' and (override in item_desc_l10n):
            val = item_desc_l10n[override]
            if val and val.strip().lower() not in ('', 'en_text', 'en text', 'none'):
                return val
        standard_key = f'ITEM_DESC_{item_id}'
        if standard_key in item_desc_l10n:
            val = item_desc_l10n[standard_key]
            if val and val.strip().lower() not in ('', 'en_text', 'en text', 'none'):
                return val
        return ''
    updated_items = []
    for item_id in sorted(all_item_ids):
        item_id_lower = item_id.lower()
        item_row = all_item_rows.get(item_id, {})
        item_name = resolve_item_name(item_id, item_row)
        item_name = resolve_rich_text(item_name)
        item_desc = resolve_item_desc(item_id, item_row)
        item_desc = resolve_rich_text(item_desc) if item_desc else ''
        icon_name_field = ''
        if isinstance(item_row, dict):
            icon_name_field = item_row.get('IconName', '')
        if not icon_name_field or icon_name_field == 'None':
            icon_name_field = ''
        icon_row = all_icon_rows.get(item_id, {})
        icon_path = ''
        if isinstance(icon_row, dict):
            icon_data = icon_row.get('Icon', {})
            if isinstance(icon_data, dict):
                icon_path = icon_data.get('AssetPathName', '')
        copied_icon = None
        if icon_path:
            icon_filename = icon_path.split('/')[-1].split('.')[0] if '.' in icon_path else icon_path.split('/')[-1]
            copied_icon = find_and_copy_icon(icon_filename, 'items', item_icon_subdirs)
        if not copied_icon and icon_name_field and (icon_name_field != item_id):
            icon_name_row = all_icon_rows.get(icon_name_field, {})
            if isinstance(icon_name_row, dict):
                icon_data = icon_name_row.get('Icon', {})
                if isinstance(icon_data, dict):
                    icon_path2 = icon_data.get('AssetPathName', '')
                    if icon_path2:
                        icon_filename2 = icon_path2.split('/')[-1].split('.')[0] if '.' in icon_path2 else icon_path2.split('/')[-1]
                        copied_icon = find_and_copy_icon(icon_filename2, 'items', item_icon_subdirs)
                        if copied_icon:
                            print(f"    Found icon for {item_id} via IconName '{icon_name_field}'")
        if not copied_icon and icon_name_field:
            for try_name in [icon_name_field, item_name.replace(' ', '')]:
                for alt_fn in [f'T_itemicon_{try_name}', f'T_{try_name}', try_name]:
                    for ext in ['.webp', '.png']:
                        found = find_and_copy_icon(alt_fn, 'items', item_icon_subdirs)
                        if found:
                            copied_icon = found
                            break
                    if copied_icon:
                        break
            if copied_icon:
                print(f'    Found icon for {item_id} via IconName fallback: {copied_icon}')
        if not copied_icon:
            for try_name in [item_id, item_name.replace(' ', '')]:
                for alt_fn in [f'T_itemicon_{try_name}', f'T_{try_name}', try_name]:
                    for ext in ['.webp', '.png']:
                        found = find_and_copy_icon(alt_fn, 'items', item_icon_subdirs)
                        if found:
                            copied_icon = found
                            break
                    if copied_icon:
                        break
            if copied_icon:
                print(f'    Found icon for {item_id} via alt search: {copied_icon}')
        final_icon = copied_icon or f'/icons/items/{item_id}.webp'
        if not final_icon.startswith('/icons/'):
            final_icon = f'/icons/items/{item_id}.webp'
        rarity = 0
        type_a = ''
        type_b = ''
        sort_id = 0
        if isinstance(item_row, dict):
            rarity_val = item_row.get('Rarity', 0)
            if isinstance(rarity_val, dict):
                rarity_val = rarity_val.get('value', 0)
            rarity = int(rarity_val) if rarity_val else 0
            type_a = item_row.get('TypeA', '')
            type_b = item_row.get('TypeB', '')
            sort_id_val = item_row.get('SortId', 0)
            if isinstance(sort_id_val, dict):
                sort_id_val = sort_id_val.get('value', 0)
            sort_id = int(sort_id_val) if sort_id_val else 0
        item_entry = {'name': item_name, 'asset': item_id, 'icon': final_icon, 'rarity': rarity, 'type_a': type_a, 'type_b': type_b, 'description': item_desc, 'sort_id': sort_id}
        updated_items.append(item_entry)
    try:
        pal_data = load_resource_json('paldata.json')
        pal_char_ids = set()
        for p in pal_data.get('pals', []):
            if isinstance(p, dict) and 'asset' in p:
                pal_char_ids.add(p['asset'].lower())
        filtered = []
        removed = 0
        for item in updated_items:
            asset_lower = item.get('asset', '').lower()
            name = item.get('name', '')
            if name == item.get('asset', '') and asset_lower in pal_char_ids:
                removed += 1
                continue
            filtered.append(item)
        if removed:
            print(f'  Removed {removed} pal-summon entries from item data')
        updated_items = filtered
    except Exception:
        pass
    result = {'items': updated_items}
    save_resource_json('itemdata.json', result)
    print(f'  Total items: {len(updated_items)}')
def load_single_table(data) -> dict:
    rows = {}
    if data:
        if isinstance(data, list):
            for table in data:
                if isinstance(table, dict):
                    r = table.get('Rows', {})
                    if r:
                        rows.update(r)
        elif isinstance(data, dict):
            r = data.get('Rows', {})
            if r:
                rows.update(r)
    return rows
def update_structure_data():
    print('\n=== Updating Structure Data ===')
    master_data = load_export_json('MapObject/DT_MapObjectMasterDataTable.json')
    master_common = load_export_json('MapObject/DT_MapObjectMasterDataTable_Common.json')
    master_enemy = load_export_json('MapObject/DT_MapObjectMasterDataTable_EnemyCamp.json')
    build_data = load_export_json('MapObject/Building/DT_BuildObjectDataTable.json')
    build_data_common = load_export_json('MapObject/Building/DT_BuildObjectDataTable_Common.json')
    icon_table = load_export_json('MapObject/Building/DT_BuildObjectIconDataTable.json')
    icon_table_common = load_export_json('MapObject/Building/DT_BuildObjectIconDataTable_Common.json')
    struct_name_l10n = load_l10n_table('DT_MapObjectNameText_Common.json')
    master_rows = {}
    for d in [master_data, master_common, master_enemy]:
        master_rows.update(load_single_table(d))
    build_rows = {}
    for d in [build_data, build_data_common]:
        build_rows.update(load_single_table(d))
    icon_rows = {}
    for d in [icon_table, icon_table_common]:
        icon_rows.update(load_single_table(d))
    if not master_rows:
        print('  No map object rows found. Skipping.')
        return
    all_struct_ids = set(master_rows.keys())
    for r in build_rows.values():
        if isinstance(r, dict) and r.get('MapObjectId', '') not in ('None', ''):
            all_struct_ids.add(r['MapObjectId'])
    all_struct_ids.update(icon_rows.keys())
    structure_icon_subdirs = [EXPORT_TEXTURES_DIR / 'BuildObject' / 'Icon', EXPORT_TEXTURES_DIR / 'BuildObject' / 'PNG', EXPORT_TEXTURES_DIR / 'MapObject']
    def resolve_struct_name(struct_id: str) -> str:
        key = f'MAPOBJECT_NAME_{struct_id}'
        name = struct_name_l10n.get(key, '')
        if name and name.lower() not in ('en_text', 'none', '-', ''):
            return name
        return struct_id
    updated_structures = []
    for struct_id in sorted(all_struct_ids):
        struct_id_lower = struct_id.lower()
        display_name = resolve_struct_name(struct_id)
        copied_icon = None
        icon_row = icon_rows.get(struct_id, {})
        if icon_row:
            soft_icon = icon_row.get('SoftIcon', {})
            if isinstance(soft_icon, dict):
                icon_path = soft_icon.get('AssetPathName', '')
                if icon_path and icon_path != 'None':
                    icon_filename = icon_path.split('/')[-1].split('.')[0] if '.' in icon_path else icon_path.split('/')[-1]
                    copied_icon = find_and_copy_icon(icon_filename, 'structures', structure_icon_subdirs)
        final_icon = copied_icon or f'/icons/structures/{struct_id}.webp'
        struct_entry = {'name': display_name, 'asset': struct_id, 'icon': final_icon}
        updated_structures.append(struct_entry)
    result = {'structures': updated_structures}
    save_resource_json('structuredata.json', result)
    print(f'  Total structures: {len(updated_structures)}')
_EFFECT_LABEL_MAP = {'ShotAttack': 'Attack', 'MeleeAttack': 'Melee Attack', 'Defense': 'Defense', 'MaxHP': 'Max HP', 'CraftSpeed': 'Work Speed', 'MoveSpeed': 'Movement Speed', 'MoveSpeed_Grass': 'Grass Movement Speed', 'MoveSpeed_Ground': 'Ground Movement Speed', 'MoveSpeed_Snow': 'Snow Movement Speed', 'MoveSpeed_Water': 'Water Movement Speed', 'SwimSpeed': 'Swim Speed', 'AttackSpeedUp': 'Attack Speed', 'ReloadSpeedUp': 'Reload Speed', 'AutoHPRegeneRate': 'HP Regeneration', 'Regene_HP': 'HP Regeneration', 'Regene_HP_Rate': 'HP Regeneration Rate', 'LifeSteal': 'Life Steal', 'Support': 'Support', 'Logging': 'Logging', 'Mining': 'Mining', 'CollectItem': 'Item Collection', 'CollectItemDrop': 'Item Drop', 'CollectItemDrop_NaturalObject': 'Natural Item Drop', 'BreedSpeed': 'Breeding Speed', 'MeatCutAddItemDrop': 'Meat Drop', 'CaptureLevel': 'Capture Power', 'MaxInventoryWeight': 'Max Inventory Weight', 'ItemWeightReduction': 'Item Weight Reduction', 'BulletAccuracy': 'Bullet Accuracy', 'BulletSpeed': 'Bullet Speed', 'Recoil': 'Recoil', 'Homing': 'Homing', 'Explosive': 'Explosion', 'ExplosionResist': 'Explosion Resistance', 'FallDamageRate': 'Fall Damage', 'TemperatureResist_Heat': 'Heat Resistance', 'TemperatureResist_Cold': 'Cold Resistance', 'ShieldDamageCutRate': 'Shield Damage Reduction', 'TemperatureInvalid_Heat': 'Heat Immunity', 'TemperatureInvalid_Cold': 'Cold Immunity', 'InvalidToxicGas': 'Toxic Gas Immunity', 'Nocturnal': 'Nocturnal', 'Mute': 'Mute', 'NonKilling': 'Non-Killing', 'KnockbackInvalid': 'Knockback Immunity', 'KnockbackInvalid_ForPassiveSkill': 'Knockback Immunity', 'LeanBackInvalid_ForPassiveSkill': 'Flinch Immunity', 'LowGravity': 'Low Gravity', 'EnemySightDetectionRate': 'Stealth', 'EquipmentDurabilityRate': 'Equipment Durability', 'DefeatEnemy_ActiveSkillCoolTime_Decrease': 'Active Skill Cooldown Reduction on Defeat', 'Sanity_Decrease': 'Sanity Drain', 'FullStomatch_Decrease': 'Fullness Drain', 'FarmCropGrowupSpeed': 'Crop Growth Speed', 'FarmCropHarvestNumRate': 'Crop Harvest Amount', 'Fishing_SuccessAmountUp': 'Fishing Success Amount', 'Fishing_StartProgressAdd': 'Fishing Progress', 'Fishing_FailedAmountDown': 'Fishing Failed Amount Reduction', 'Fishing_ItemAddDrop': 'Fishing Extra Drop', 'Fishing_EnemyAddDrop': 'Fishing Enemy Extra Drop', 'Fishing_GoodTalentPalProbability': 'Fishing Good Pal Probability', 'Fishing_SearchProbabilityRateInNight': 'Fishing Night Search Probability', 'FishingSalvage_ItemDrop': 'Fishing Salvage Drop', 'ShopBuyPrice_Money_Increase': 'Shop Buy Price', 'ShopSellPrice_Money_Increase': 'Shop Sell Price', 'AttackRateHPThreshold': 'Attack (Low HP)', 'DefenseRateHPThreshold': 'Defense (Low HP)', 'RecoverHPOnHPThreshold': 'HP Recovery (Low HP)', 'DefeatEnemy_StackBuff': 'Stack Buff on Defeat', 'BulletHit_StackBuff': 'Stack Buff on Hit', 'SelfDeathAddItemDrop': 'Extra Drop on Death', 'GainItemDrop': 'Extra Item Drop', 'BreedSpeed_InBaseCamp': 'Breeding Speed (Base Camp)', 'DamageUpToNonBattleEnemy': 'Damage to Non-Battle Enemies', 'DamageUpPartnerSkillAttack': 'Partner Skill Damage', 'DamageUp_LastBullet': 'Last Bullet Damage', 'DamageRateByEquippedWeapon': 'Equipped Weapon Damage', 'BuildingDamageReduction': 'Building Damage Reduction', 'PlayerSP_DecreaseRate': 'SP Consumption', 'PlayerShield_RecoverStartTimeRate': 'Shield Recovery Delay', 'LifeDrainPower_AttackUp': 'Life Drain Attack', 'BodyPartsWeakDamage': 'Weak Point Damage', 'PlayerLowHealthBlast': 'Low Health Explosion', 'Player_ArrowExplosion': 'Arrow Explosion', 'SlipDamageRate_Burn': 'Burn Slip Damage', 'SlipDamageRate_Poison': 'Poison Slip Damage', 'PlayerInflictEffect_MeleeHitBarrier': 'Melee Hit Barrier', 'PlayerInflictEffect_WeakPointHit_DamageUp': 'Weak Point Damage Up', 'PlayerInflictEffect_AttackBurning_ApplyExplosion': 'Burning Attack Explosion', 'PlayerInflictEffect_AttackBurning_ApplyFireVortex': 'Burning Attack Fire Vortex', 'PlayerInflictEffect_AttackElectrified_ApplySpark': 'Electrified Attack Spark', 'PlayerInflictEffect_AttackIvyCling_ApplyExplosion': 'Ivy Cling Attack Explosion', 'PlayerInflictEffect_AttackMuddy_ApplyAttackDown': 'Muddy Attack Down', 'PlayerInflictEffect_AttackPoisoned_ApplyAttackDown': 'Poison Attack Down', 'PlayerInflictEffect_AttackWet_ApplyFreeze': 'Wet Attack Freeze', 'PlayerElementStepAttack_Fire': 'Fire Step Attack', 'PlayerElementStepAttack_Leaf': 'Grass Step Attack', 'PlayerElementStepAttack_Water': 'Water Step Attack', 'WorldTreeDecayImmunity': 'World Tree Decay Immunity', 'ForYakushimaDefenceRate': 'Yakushima Defense', 'DamageUpIfEquipped_YakushimaMagicWeapon': 'Yakushima Magic Weapon Damage', 'DamageUpIfEquipped_YakushimaMeleeWeapon': 'Yakushima Melee Weapon Damage', 'DamageUpIfEquipped_YakushimaRangedWeapon': 'Yakushima Ranged Weapon Damage', 'DamageUpIfEquipped_YakushimaSummonWeapon': 'Yakushima Summon Weapon Damage', 'PalExp_Increase': 'Pal EXP Gain', 'PalSP_Increase': 'Pal SP', 'PalEggHatchingSpeed': 'Egg Hatching Speed', 'EggAlphaConversion': 'Egg Alpha Conversion', 'EggObtainExtraEgg': 'Extra Egg Obtain', 'FriendshipPoint_Increase': 'Friendship Gain', 'ItemCorruptionSpeedRate': 'Item Corruption Speed', 'ClimbMoveSpeedRate': 'Climb Speed', 'RideJumpCount_Increase': 'Ride Jump Count', 'JumpCount_Increase': 'Jump Count', 'JumpPower_Increase': 'Jump Power', 'LavaDamageInvalid': 'Lava Damage Immunity', 'CaptureLevel_SneakBonus': 'Sneak Capture Bonus', 'CaptureLevelUpIfTarget_Freeze': 'Capture Power vs Frozen', 'CaptureLevelUpIfTarget_IvyCling': 'Capture Power vs Ivy Cling', 'Regene_Stomatch_Hungriest': 'Fullness Regeneration', 'Defuser_ExplosiveSpore': 'Explosive Spore Defense', 'SphereRecovery': 'Sphere Recovery', 'NightOwl': 'Night Owl', 'ActiveSkillCoolTime_Decrease': 'Active Skill Cooldown', 'PartnerSkillCoolTime_Decrease': 'Partner Skill Cooldown', 'AvoidDurationUp_EquipSkill': 'Equip Skill Avoid Duration', 'AvoidDurationUp_PartnerSkill': 'Partner Skill Avoid Duration', 'Wind_Change_Negative': 'Negative Wind Change'}
_WORK_TYPE_MAP = {'EmitFlame': 'Kindling', 'Watering': 'Watering', 'Seeding': 'Planting', 'GenerateElectricity': 'Generating Electricity', 'Handcraft': 'Handiwork', 'Collection': 'Gathering', 'Deforest': 'Lumbering', 'Mining': 'Mining', 'Transport': 'Transporting', 'MonsterFarm': 'Ranching', 'ProductMedicine': 'Medicine Production', 'OilExtraction': 'Oil Extraction', 'Cool': 'Cooling'}
_ELEMENT_MAP = {'Fire': 'Fire', 'Water': 'Water', 'Leaf': 'Grass', 'Electricity': 'Electric', 'Ice': 'Ice', 'Earth': 'Ground', 'Dark': 'Dark', 'Dragon': 'Dragon', 'Normal': 'Neutral'}
_ADDITIONAL_MAP = {'Burn': 'Burn', 'Poison': 'Poison', 'Freeze': 'Freeze', 'Electrical': 'Electrified', 'IvyCling': 'Ivy Cling', 'Muddy': 'Muddy', 'Darkness': 'Darkness', 'Stun': 'Stun', 'Wetness': 'Wet'}
def _format_effect_value(v):
    if isinstance(v, float):
        if v == int(v):
            return str(int(v))
        return f'{v:g}'
    return str(v)
def _generate_passive_desc(passive_id, etype1, eval1, etype2, eval2, etype3, eval3):
    parts = []
    for etype, evalue in [(etype1, eval1), (etype2, eval2), (etype3, eval3)]:
        if evalue == 0:
            continue
        label = _resolve_effect_label(etype)
        if label is None:
            continue
        sign = '+' if evalue > 0 else ''
        parts.append(f'{label} {sign}{_format_effect_value(evalue)}%')
    if parts:
        return '\r\n'.join(parts)
    return ''
def _resolve_effect_label(etype):
    if not etype or etype == 'EPalPassiveSkillEffectType::no':
        return None
    name = etype.replace('EPalPassiveSkillEffectType::', '')
    if name in _EFFECT_LABEL_MAP:
        return _EFFECT_LABEL_MAP[name]
    m = re.match('ElementBoost_(\\w+)', name)
    if m:
        elem = _ELEMENT_MAP.get(m.group(1), m.group(1))
        return f'{elem} attack damage'
    m = re.match('ElementBoostWeakness_(\\w+)', name)
    if m:
        elem = _ELEMENT_MAP.get(m.group(1), m.group(1))
        return f'{elem} attack damage (weakness)'
    m = re.match('ElementResist_(\\w+)', name)
    if m:
        elem = _ELEMENT_MAP.get(m.group(1), m.group(1))
        return f'{elem} damage resistance'
    m = re.match('Element(\\w+)', name)
    if m and m.group(1) in _ELEMENT_MAP:
        elem = _ELEMENT_MAP[m.group(1)]
        return f'{elem} type'
    m = re.match('WorkSuitabilityAddRank_(\\w+)', name)
    if m:
        work = _WORK_TYPE_MAP.get(m.group(1), m.group(1))
        return f'{work}'
    m = re.match('ResistAdditionalEffect_(\\w+)', name)
    if m:
        eff = _ADDITIONAL_MAP.get(m.group(1), m.group(1))
        return f'{eff} resistance'
    m = re.match('AdditionalEffect_(\\w+)', name)
    if m:
        eff = _ADDITIONAL_MAP.get(m.group(1), m.group(1))
        return f'Inflict {eff}'
    m = re.match('AttackRateIfAttacker_(\\w+)', name)
    if m:
        eff = _ADDITIONAL_MAP.get(m.group(1), m.group(1))
        return f'Attack vs {eff}'
    m = re.match('DamageRateIfDefender_(\\w+)', name)
    if m:
        eff = _ADDITIONAL_MAP.get(m.group(1), m.group(1))
        return f'Damage vs {eff}'
    m = re.match('ElementAddItemDrop_(\\w+)', name)
    if m:
        elem = _ELEMENT_MAP.get(m.group(1), m.group(1))
        return f'{elem} item drop'
    if name == 'CurveType':
        return None
    display = name.replace('_', ' ')
    return display
def update_passive_data():
    print('\n=== Updating Passive Data ===')
    passive_main = load_export_json('PassiveSkill/DT_PassiveSkill_Main.json')
    passive_main_common = load_export_json('PassiveSkill/DT_PassiveSkill_Main_Common.json')
    raw_skill_l10n = load_l10n_table('DT_SkillNameText_Common.json')
    raw_skill_desc = load_l10n_table('DT_SkillDescText_Common.json')
    passive_name_l10n = {}
    passive_desc_l10n = {}
    _invalid_l10n = {'', 'en_text', 'en text', 'en', '-', 'none', 'ex text'}
    for uid_key, display_name in raw_skill_l10n.items():
        if uid_key.startswith('PASSIVE_'):
            passive_asset = uid_key[len('PASSIVE_'):]
            if display_name and display_name.strip().lower() not in _invalid_l10n:
                passive_name_l10n[passive_asset] = display_name
    for uid_key, desc_text in raw_skill_desc.items():
        if uid_key.startswith('PASSIVE_'):
            passive_asset = uid_key[len('PASSIVE_'):]
            if desc_text and desc_text.strip().lower() not in _invalid_l10n:
                passive_desc_l10n[passive_asset] = desc_text
    all_rows = {}
    for data in [passive_main, passive_main_common]:
        if data:
            if isinstance(data, list):
                for table in data:
                    if isinstance(table, dict):
                        rows = table.get('Rows', {})
                        if rows:
                            all_rows.update(rows)
            elif isinstance(data, dict):
                rows = data.get('Rows', {})
                if rows:
                    all_rows.update(rows)
    if not all_rows:
        print('  No passive rows found. Skipping.')
        return
    passive_icon_subdirs = [EXPORT_TEXTURES_DIR / 'UI' / 'Common', EXPORT_TEXTURES_DIR / 'StatusParameterIcon', EXPORT_TEXTURES_DIR / 'UI' / 'Main_Menu']
    updated_passives = []
    for passive_id, row_data in sorted(all_rows.items()):
        passive_id_lower = passive_id.lower()
        rank = 1
        if isinstance(row_data, dict):
            rank_data = row_data.get('Rank', row_data.get('PassiveRank', {}))
            if isinstance(rank_data, dict):
                rank = rank_data.get('value', rank)
            else:
                rank = rank_data or rank
        icon_data = row_data.get('Icon', {})
        icon_path = icon_data.get('AssetPathName', '') if isinstance(icon_data, dict) else ''
        copied_icon = None
        if icon_path:
            icon_filename = icon_path.split('/')[-1].split('.')[0] if '.' in icon_path else icon_path.split('/')[-1]
            copied_icon = find_and_copy_icon(icon_filename, 'passives', passive_icon_subdirs)
        if not copied_icon:
            if isinstance(rank, int) and rank < 0:
                arrow_idx = 0
            else:
                arrow_idx = min(max(abs(rank) if isinstance(rank, int) else 1, 0), 5)
            arrow_name = f'T_icon_skillstatus_rank_arrow_{arrow_idx:02d}'
            copied_icon = find_and_copy_icon(arrow_name, 'passives', passive_icon_subdirs)
        l10n_name = passive_name_l10n.get(passive_id, None)
        display_name = l10n_name or passive_id
        desc_id = row_data.get('OverrideDescMsgID', '') if isinstance(row_data, dict) else ''
        if desc_id in ('None', 'none', ''):
            desc_id = ''
        desc_text = raw_skill_desc.get(desc_id, '') if desc_id else ''
        if not desc_text and desc_id:
            desc_text = raw_skill_desc.get(passive_id, '')
        if desc_text:
            _UI_COMMON_MAP = {'COMMON_STATUS_HP': 'HP', 'COMMON_STATUS_RANGE_ATTACK': 'Attack', 'COMMON_WORK_SUITABILITY_MonsterFarm': 'Ranching', 'COMMON_WORK_SUITABILITY_PALDEX': 'work suitability'}
            for uid, label in _UI_COMMON_MAP.items():
                desc_text = desc_text.replace(f'<uiCommon id=|{uid}|/>', label)
            clean = re.sub('<[^>]+>', '', desc_text).strip()
            if clean and (not clean.startswith("'s")):
                desc_text = clean
            else:
                desc_text = ''
        et1 = row_data.get('EffectType1', '') if isinstance(row_data, dict) else ''
        et2 = row_data.get('EffectType2', '') if isinstance(row_data, dict) else ''
        et3 = row_data.get('EffectType3', '') if isinstance(row_data, dict) else ''
        ev1 = row_data.get('EffectValue1', 0) if isinstance(row_data, dict) else 0
        ev2 = row_data.get('EffectValue2', 0) if isinstance(row_data, dict) else 0
        ev3 = row_data.get('EffectValue3', 0) if isinstance(row_data, dict) else 0
        ev4 = row_data.get('EffectValue4', 0) if isinstance(row_data, dict) else 0
        if not desc_text:
            desc_text = _generate_passive_desc(passive_id, et1, ev1, et2, ev2, et3, ev3)
        add_pal = bool(row_data.get('AddPal', False)) if isinstance(row_data, dict) else False
        add_rare_pal = bool(row_data.get('AddRarePal', False)) if isinstance(row_data, dict) else False
        add_world_tree_pal = bool(row_data.get('AddWorldTreePal', False)) if isinstance(row_data, dict) else False
        add_mutation_pal = bool(row_data.get('AddMutationPal', False)) if isinstance(row_data, dict) else False
        add_armor = bool(row_data.get('AddArmor', False)) if isinstance(row_data, dict) else False
        add_accessory = bool(row_data.get('AddAccessory', False)) if isinstance(row_data, dict) else False
        add_weapon = bool(row_data.get('AddShotWeapon', False) or row_data.get('AddMeleeWeapon', False)) if isinstance(row_data, dict) else False
        invoke_always = bool(row_data.get('InvokeAlways', False)) if isinstance(row_data, dict) else False
        category = row_data.get('Category', '') if isinstance(row_data, dict) else ''
        passive_entry = {'name': display_name, 'asset': passive_id, 'rank': rank, 'icon': copied_icon or '/icons/passives/T_icon_skillstatus_rank_arrow_04.png', 'description': desc_text, 'effect1': ev1, 'effect2': ev2, 'effect3': ev3, 'effect4': ev4, 'efftype1': et1, 'efftype2': et2, 'efftype3': et3, 'add_pal': add_pal, 'add_rare_pal': add_rare_pal, 'add_world_tree_pal': add_world_tree_pal, 'add_mutation_pal': add_mutation_pal, 'add_armor': add_armor, 'add_accessory': add_accessory, 'add_weapon': add_weapon, 'invoke_always': invoke_always, 'category': category}
        updated_passives.append(passive_entry)
    result = {'passives': updated_passives}
    save_resource_json('passivedata.json', result)
    print(f'  Total passives: {len(updated_passives)}')
def update_technology_data():
    print('\n=== Updating Technology Data ===')
    tech_data = load_export_json('Technology/DT_TechnologyRecipeUnlock.json')
    tech_data_common = load_export_json('Technology/DT_TechnologyRecipeUnlock_Common.json')
    item_data = load_resource_json('itemdata.json')
    item_name_map = {}
    item_icon_map = {}
    for i in item_data.get('items', []):
        if isinstance(i, dict) and 'asset' in i and ('name' in i):
            item_name_map[i['asset'].lower()] = i['name']
            if 'icon' in i:
                item_icon_map[i['asset'].lower()] = i['icon']
    struct_data = load_resource_json('structuredata.json')
    struct_name_map = {}
    struct_icon_map = {}
    for s in struct_data.get('structures', []):
        if isinstance(s, dict) and 'asset' in s and ('name' in s):
            struct_name_map[s['asset'].lower()] = s['name']
            if 'icon' in s:
                struct_icon_map[s['asset'].lower()] = s['icon']
    tech_l10n = load_l10n_table('DT_TechnologyNameText_Common.json')
    tech_desc_l10n = load_l10n_table('DT_TechnologyDescText_Common.json')
    all_rows = {}
    for data in [tech_data, tech_data_common]:
        if data:
            if isinstance(data, list):
                for table in data:
                    if isinstance(table, dict):
                        rows = table.get('Rows', {})
                        if rows:
                            all_rows.update(rows)
            elif isinstance(data, dict):
                rows = data.get('Rows', {})
                if rows:
                    all_rows.update(rows)
    if not all_rows:
        print('  No technology rows found. Skipping.')
        return
    def _resolve_rich_text(text: str) -> str:
        return resolve_rich_text(text)
    tech_icon_subdirs = [EXPORT_TEXTURES_DIR / 'UI' / 'Common', EXPORT_TEXTURES_DIR / 'UI' / 'InGame', EXPORT_TEXTURES_DIR / 'StatusParameterIcon']
    updated_techs = []
    for tech_id, row_data in sorted(all_rows.items()):
        if not isinstance(row_data, dict):
            continue
        recipe_name = row_data.get('Name', '')
        icon_name = row_data.get('IconName', '')
        tier = row_data.get('Tier', 0)
        tech_type = row_data.get('IsBossTechnology', False)
        display_name = tech_id
        if recipe_name and recipe_name != 'None':
            l10n_name = tech_l10n.get(recipe_name, '')
            if l10n_name and l10n_name.strip().lower() not in ('', 'en_text', 'en', '-', 'none', 'ex text'):
                display_name = _resolve_rich_text(l10n_name)
        copied_icon = None
        unlock_items = row_data.get('UnlockItemRecipes', [])
        unlock_builds = row_data.get('UnlockBuildObjects', [])
        for item_id in unlock_items:
            item_icon = item_icon_map.get(item_id.lower(), '')
            if item_icon:
                item_filename = item_icon.rsplit('/', 1)[-1] if '/' in item_icon else item_icon
                src_path = ICONS_DIR / 'items' / item_filename
                if src_path.exists():
                    import shutil
                    target_dir = ICONS_DIR / 'technologies'
                    target_file = target_dir / item_filename
                    if not target_file.exists():
                        shutil.copy2(str(src_path), str(target_file))
                    copied_icon = f'/icons/technologies/{item_filename}'
                    break
        if not copied_icon:
            for struct_id in unlock_builds:
                struct_icon = struct_icon_map.get(struct_id.lower(), '')
                if struct_icon:
                    struct_filename = struct_icon.rsplit('/', 1)[-1] if '/' in struct_icon else struct_icon
                    src_path = ICONS_DIR / 'structures' / struct_filename
                    if src_path.exists():
                        import shutil
                        target_dir = ICONS_DIR / 'technologies'
                        target_file = target_dir / struct_filename
                        if not target_file.exists():
                            shutil.copy2(str(src_path), str(target_file))
                        copied_icon = f'/icons/technologies/{struct_filename}'
                        break
        if not copied_icon and icon_name:
            for try_fn in [f'T_itemicon_{icon_name}', f'T_{icon_name}', icon_name]:
                copied_icon = find_and_copy_icon(try_fn, 'technologies', tech_icon_subdirs)
                if copied_icon:
                    break
        if recipe_name and recipe_name != 'None':
            desc_key = recipe_name.replace('NAME_', 'DESC_')
        else:
            desc_key = f'DESC_RECIPE_{tech_id}'
        desc_text = tech_desc_l10n.get(desc_key, '')
        if not desc_text or desc_text.strip().lower() in ('', 'en_text', 'en text', 'none', 'ex text'):
            desc_text = ''
        else:
            desc_text = _resolve_rich_text(desc_text)
        tech_entry = {'name': display_name, 'asset': tech_id, 'icon': copied_icon or f'/icons/technologies/{tech_id}.webp', 'type': 'boss' if tech_type else 'standard', 'description': desc_text}
        updated_techs.append(tech_entry)
    result = {'technology': updated_techs}
    save_resource_json('technologydata.json', result)
    print(f'  Total technologies: {len(updated_techs)}')
def get_all_rows_for_tables(table_names: list[str]) -> dict:
    all_rows = {}
    for table_name in table_names:
        data = load_export_json(table_name)
        if data:
            if isinstance(data, list):
                for table in data:
                    if isinstance(table, dict):
                        rows = table.get('Rows', {})
                        if rows:
                            all_rows.update(rows)
            elif isinstance(data, dict):
                rows = data.get('Rows', {})
                if rows:
                    all_rows.update(rows)
        base, ext = table_name.rsplit('.', 1) if '.' in table_name else (table_name, 'json')
        common_name = f'{base}_Common.{ext}'
        data_common = load_export_json(common_name)
        if data_common:
            if isinstance(data_common, list):
                for table in data_common:
                    if isinstance(table, dict):
                        rows = table.get('Rows', {})
                        if rows:
                            all_rows.update(rows)
            elif isinstance(data_common, dict):
                rows = data_common.get('Rows', {})
                if rows:
                    all_rows.update(rows)
    return all_rows
def _build_character_name_map():
    char_map = {}
    try:
        name_l10n = load_l10n_table('DT_PalNameText_Common.json')
        for key, name in name_l10n.items():
            if key.startswith('PAL_NAME_') and name:
                char_id = key[len('PAL_NAME_'):]
                if char_id and name.lower() not in ('en text', 'en_text', '', 'none'):
                    char_map[char_id] = name
    except Exception:
        pass
    return char_map
def update_skill_data():
    print('\n=== Updating Skill Data ===')
    all_rows = get_all_rows_for_tables(['Waza/DT_WazaDataTable.json'])
    raw_skill_l10n = load_l10n_table('DT_SkillNameText_Common.json')
    raw_skill_desc = load_l10n_table('DT_SkillDescText_Common.json')
    skill_name_l10n = {}
    for uid_key, display_name in raw_skill_l10n.items():
        if uid_key.startswith('ACTION_SKILL_'):
            skill_asset = uid_key[len('ACTION_SKILL_'):]
            skill_name_l10n[skill_asset] = display_name
    skill_desc_l10n = {}
    for uid_key, desc_text in raw_skill_desc.items():
        if uid_key.startswith('ACTION_SKILL_'):
            skill_asset = uid_key[len('ACTION_SKILL_'):]
            if desc_text and desc_text.lower() not in ('en text', 'en_text', '', 'none'):
                skill_desc_l10n[skill_asset] = desc_text
    _char_name_map = _build_character_name_map()
    for k, v in skill_desc_l10n.items():
        v = re.sub('<characterName\\s+id=\\|(\\w+)\\|\\s*/>', lambda m: _char_name_map.get(m.group(1), m.group(0)), v)
        v = re.sub('<[^>]+>', '', v).strip()
        skill_desc_l10n[k] = v
    if not all_rows:
        print('  No skill rows found. Skipping.')
        return
    skill_map = {}
    for row_key, row_data in all_rows.items():
        waza_type = ''
        element = ''
        power = 0
        cooldown = 0
        if isinstance(row_data, dict):
            waza_type = row_data.get('WazaType', '')
            element_raw = row_data.get('Element', '')
            power = row_data.get('Power', 0) or row_data.get('DisplayPower', 0) or 0
            cooldown = row_data.get('CoolTime', 0) or 0
            if isinstance(element_raw, str) and element_raw.startswith('EPalElementType::'):
                element = element_raw.replace('EPalElementType::', '')
            if isinstance(element_raw, dict):
                element = element_raw.get('value', '')
        if isinstance(row_data, dict) and row_data.get('DisabledData', False):
            continue
        if isinstance(waza_type, str) and waza_type.startswith('EPalWazaID::'):
            skill_asset = waza_type.replace('EPalWazaID::', '')
        elif isinstance(waza_type, str):
            skill_asset = waza_type
        else:
            skill_asset = row_key
        skill_lower = skill_asset.lower()
        if skill_lower in skill_map:
            continue
        skill_map[skill_lower] = {'name': skill_asset, 'asset': skill_asset, 'element': element, 'power': power if isinstance(power, (int, float)) else 0, 'cooldown': cooldown if isinstance(cooldown, (int, float)) else 0}
    updated_skills = []
    for skill_asset in sorted(skill_map.keys()):
        entry = skill_map[skill_asset]
        skill_lower = entry['asset'].lower()
        l10n_name = skill_name_l10n.get(entry['asset'], None)
        skill_entry = {'name': l10n_name or entry['name'], 'asset': entry['asset'], 'element': entry['element'], 'power': entry['power'], 'cooldown': entry['cooldown'], 'description': skill_desc_l10n.get(entry['asset'], '')}
        updated_skills.append(skill_entry)
    result = {'skills': updated_skills}
    save_resource_json('skilldata.json', result)
    print(f'  Total skills: {len(updated_skills)}')
def update_pal_exp_table():
    print('\n=== Updating Pal EXP Table ===')
    exp_data = load_export_json('Exp/DT_PalExpTable.json')
    if not exp_data:
        print('  No EXP table found. Skipping.')
        return
    all_rows = {}
    if isinstance(exp_data, list):
        for table in exp_data:
            if isinstance(table, dict):
                rows = table.get('Rows', {})
                if rows:
                    all_rows.update(rows)
    elif isinstance(exp_data, dict):
        rows = exp_data.get('Rows', {})
        if rows:
            all_rows.update(rows)
    if not all_rows:
        print('  No EXP rows found. Skipping.')
        return
    save_resource_json('pal_exp_table.json', all_rows)
    print(f'  Total EXP entries: {len(all_rows)}')
def update_friendship_data():
    print('\n=== Updating Friendship Data ===')
    friend_data = load_export_json('Friendship/DT_FriendshipRankTable.json')
    if not friend_data:
        print('  No friendship data found. Skipping.')
        return
    all_rows = {}
    if isinstance(friend_data, list):
        for table in friend_data:
            if isinstance(table, dict):
                rows = table.get('Rows', {})
                if rows:
                    all_rows.update(rows)
    elif isinstance(friend_data, dict):
        rows = friend_data.get('Rows', {})
        if rows:
            all_rows.update(rows)
    if not all_rows:
        print('  No friendship rows found. Skipping.')
        return
    save_resource_json('friendship.json', all_rows)
def update_pal_descriptions():
    print('\n=== Updating Pal Descriptions ===')
    existing = load_resource_json('paldata.json')
    if not existing or 'pals' not in existing:
        print('  No existing paldata.json found. Run update_pal_data first. Skipping.')
        return
    skill_name_l10n = load_l10n_table('DT_SkillNameText_Common.json')
    first_activated_l10n = load_l10n_table('DT_PalFirstActivatedInfoText.json')
    append_l10n = load_l10n_table('DT_PartnerSkillAppendText.json')
    partner_skill_names = {}
    for key, value in skill_name_l10n.items():
        if key.startswith('PARTNERSKILL_'):
            asset = key[len('PARTNERSKILL_'):]
            partner_skill_names[asset.lower()] = value
    pal_descriptions = {}
    for key, value in first_activated_l10n.items():
        if key.startswith('PAL_FIRST_SPAWN_DESC_'):
            asset = key[len('PAL_FIRST_SPAWN_DESC_'):]
            pal_descriptions[asset.lower()] = value
    PREFIXES = ('BOSS_', 'PREDATOR_', 'GYM_', 'RAID_', 'POLICE_', 'SUMMON_')
    def _get_base_asset(pal_id):
        pal_lower = pal_id.lower()
        for pfx in PREFIXES:
            if pal_lower.startswith(pfx.lower()):
                return pal_lower[len(pfx):]
        return pal_lower
    _append_l10n_lower = {}
    for k, v in append_l10n.items():
        _append_l10n_lower[k.lower()] = v
    def _resolve_reference_msg(match):
        msg_id = match.group(1)
        rank1_key = f'{msg_id}_Rank_1'
        text = _append_l10n_lower.get(rank1_key.lower(), '')
        if text:
            text = _cleanup_game_tags(text)
            return text
        return '{ReferenceMsgId_' + msg_id + '}'
    def _cleanup_game_tags(desc):
        if not desc:
            return desc
        def _resolve_reference_msg(match):
            msg_id = match.group(1)
            rank1_key = f'{msg_id}_Rank_1'
            text = _append_l10n_lower.get(rank1_key.lower(), '')
            if text:
                text = _cleanup_game_tags(text)
                return text
            return '{ReferenceMsgId_' + msg_id + '}'
        def _pipe_to_readable(match):
            pipe_val = match.group(1)
            parts = pipe_val.split('_')
            tail = parts[-1] if parts else pipe_val
            tail = tail[0].upper() + tail[1:].lower() if tail else ''
            return tail
        def _ui_common_readable(match):
            id_val = match.group(1)
            parts = id_val.split('_')
            tail = parts[-1] if parts else id_val
            tail = tail[0].upper() + tail[1:].lower() if tail else ''
            return tail
        desc = re.sub('\\{ReferenceMsgId_(\\w+)\\}', _resolve_reference_msg, desc)
        def _preserve_effect(m):
            return f'_PH({m.group(1)})_'
        desc = re.sub('\\{(Passive\\d+_EffectValue\\d+|ReferencePassive\\d+_EffectValue\\d+|ActiveSkillMainValueByRank|ActiveSkillOverWriteEffectTime|ReferenceMsgId_\\w+)\\}', _preserve_effect, desc)
        desc = re.sub('\\{[^}]*\\}', '?', desc)
        desc = re.sub('_PH\\(([^)]+)\\)_', '{\\1}', desc)
        desc = re.sub('<Status_Up>([^<]*)</>', '\\1 ', desc)
        desc = re.sub('<Status_Keyword>([^<]*)</>', '\\1 ', desc)
        desc = re.sub('<img\\s+id=\\|ElemIcon_([^|]+)\\|[^/>]*/>', '[ICON:ElemIcon_\\1]', desc)
        desc = re.sub('<img\\s[^/>]*/>', '', desc)
        desc = re.sub('<uiCommon\\s+id=\\|COMMON_ELEMENT_NAME_(\\w+)\\|[^/>]*/>', '[ELEM:\\1]', desc)
        desc = re.sub('<uiCommon\\s+id=\\|ADDITIONAL_EFFECT_(\\w+)\\|[^/>]*/>', '[EFFECT:\\1]', desc)
        desc = re.sub('<uiCommon\\s+id=\\|([^|]+)\\|[^/>]*/>', _ui_common_readable, desc)
        def _extract_tag_id(m):
            t = m.group(0)
            mid = re.search(r'id=\|([^|]+)\|', t)
            return mid.group(1) if mid else ''
        desc = re.sub('<(activeSkillName|characterName|itemName|mapObjectName)\\s[^/>]*/>', _extract_tag_id, desc)
        desc = re.sub('<[^>]*>', '', desc)
        desc = re.sub('\\|([A-Za-z0-9_]+)\\|', _pipe_to_readable, desc)
        desc = re.sub('\\s+', ' ', desc)
        desc = desc.strip()
        return desc
    def _work_suitability_readable(m):
        name = m.group(1)
        parts = re.findall('[A-Z][a-z]*', name)
        if parts:
            return parts[0] if len(parts) == 1 else ' '.join(parts)
        return name
    updated = 0
    for pal_entry in existing['pals']:
        if not isinstance(pal_entry, dict):
            continue
        asset = pal_entry.get('asset', '')
        if not asset:
            continue
        base_asset = _get_base_asset(asset)
        pskill_name = partner_skill_names.get(base_asset, partner_skill_names.get(asset.lower(), ''))
        pal_desc = pal_descriptions.get(base_asset, pal_descriptions.get(asset.lower(), ''))
        if pal_desc:
            pal_desc = re.sub('<img\\s+id=\\|ElemIcon_([^|]+)\\|[^/>]*/>', '[ICON:ElemIcon_\\1]', pal_desc)
            pal_desc = re.sub('<uiCommon\\s+id=\\|COMMON_ELEMENT_NAME_(\\w+)\\|[^/>]*/>', '[ELEM:\\1]', pal_desc)
            pal_desc = re.sub('<uiCommon\\s+id=\\|ADDITIONAL_EFFECT_(\\w+)\\|[^/>]*/>', '[EFFECT:\\1]', pal_desc)
            pal_desc = re.sub('<uiCommon\\s+id=\\|COMMON_WORK_SUITABILITY_(\\w+)\\|[^/>]*/>', _work_suitability_readable, pal_desc)
            pal_desc = resolve_rich_text(pal_desc)
            pal_desc = _cleanup_game_tags(pal_desc)
            pal_desc = pal_desc.replace('\r\n', '\n').replace('\r', '\n')
        pal_entry['partner_skill'] = pskill_name
        pal_entry['description'] = pal_desc
        updated += 1
    from collections import defaultdict
    name_groups = defaultdict(list)
    for pal_entry in existing['pals']:
        if not isinstance(pal_entry, dict):
            continue
        ename = pal_entry.get('name', '')
        base_name = re.sub(r'\s*\(.*?\)\s*$', '', ename).strip()
        if base_name:
            name_groups[base_name.lower()].append(pal_entry)
    inherited = 0
    for pal_entry in existing['pals']:
        if not isinstance(pal_entry, dict):
            continue
        if pal_entry.get('description', ''):
            continue
        ename = pal_entry.get('name', '')
        base_name = re.sub(r'\s*\(.*?\)\s*$', '', ename).strip()
        if not base_name:
            continue
        candidates = name_groups.get(base_name.lower(), [])
        if not candidates:
            continue
        tgt_elems = pal_entry.get('elements', {})
        best = None
        for c in candidates:
            if c is pal_entry:
                continue
            if not c.get('description', ''):
                continue
            src_elems = c.get('elements', {})
            if tgt_elems and src_elems and not (set(tgt_elems.keys()) & set(src_elems.keys())):
                continue
            best = c
            break
        if best:
            pal_entry['description'] = best['description']
            if not pal_entry.get('partner_skill', ''):
                pal_entry['partner_skill'] = best.get('partner_skill', '')
            inherited += 1
    if inherited:
        print(f'  Inherited descriptions for {inherited} pals from same-name variants')
    npc_msg = 'Humans are not Pals. Therefore, they do not possess Partner Skills.'
    npc_fixed = 0
    for pal_entry in existing['pals']:
        if not isinstance(pal_entry, dict):
            continue
        if pal_entry.get('elements', {}):
            continue
        if 'stats' in pal_entry:
            continue
        if pal_entry.get('description', '') == npc_msg:
            continue
        pal_entry['description'] = npc_msg
        pal_entry['partner_skill'] = ''
        npc_fixed += 1
    if npc_fixed:
        print(f'  Set NPC description for {npc_fixed} human entries')
    partner_skill_param = load_export_json('PassiveSkill/DT_PartnerSkillParameter.json')
    skill_data_list = partner_skill_param if isinstance(partner_skill_param, list) else [partner_skill_param]
    pal_to_partner_passives = {}
    pal_to_textref_passives = {}
    pal_to_skill_type = {}
    pal_to_main_values = {}
    pal_to_overwrite_effect = {}
    for table in skill_data_list:
        if isinstance(table, dict):
            for bp_class, params in table.get('Rows', {}).items():
                if isinstance(params, dict):
                    active_skill = params.get('ActiveSkill', {})
                    if isinstance(active_skill, dict):
                        pal_to_skill_type[bp_class.lower()] = active_skill.get('SkillName', '')
                        by_rank = active_skill.get('ActiveSkill_MainValueByRank', [])
                        values = []
                        for entry in by_rank:
                            if isinstance(entry, dict):
                                v = entry.get('value', entry.get('Value', None))
                                if v is not None:
                                    values.append(float(v))
                            elif isinstance(entry, (int, float)):
                                values.append(float(entry))
                        if values:
                            pal_to_main_values[bp_class.lower()] = values
                        overwrite_by_rank = active_skill.get('ActiveSkill_OverWriteEffectTimeByRank', [])
                        o_values = []
                        for entry in overwrite_by_rank:
                            if isinstance(entry, dict):
                                v = entry.get('value', entry.get('Value', None))
                                if v is not None:
                                    o_values.append(float(v))
                            elif isinstance(entry, (int, float)):
                                o_values.append(float(entry))
                        if o_values:
                            pal_to_overwrite_effect[bp_class.lower()] = o_values
                    passive_list = []
                    seen_bases = set()
                    for slot in params.get('PassiveSkills', []):
                        if isinstance(slot, dict):
                            for item in slot.get('SkillAndParametersArray', []):
                                if isinstance(item, dict):
                                    sn = item.get('SkillName', {})
                                    if isinstance(sn, dict):
                                        key = sn.get('Key', '')
                                        if key:
                                            base = re.sub(r'_\d+$', '', key)
                                            if base not in seen_bases:
                                                seen_bases.add(base)
                                                passive_list.append(key)
                    text_ref_passives = []
                    for ref_group in params.get('TextReferencePassiveSkills', []):
                        if isinstance(ref_group, dict):
                            for item in ref_group.get('PassiveSkillIds', []):
                                if isinstance(item, dict):
                                    key = item.get('Key', '')
                                    if key:
                                        text_ref_passives.append(key)
                    if passive_list:
                        pal_to_partner_passives[bp_class.lower()] = passive_list
                    if text_ref_passives:
                        pal_to_textref_passives[bp_class.lower()] = text_ref_passives
    monster_param = load_export_json('Character/DT_PalMonsterParameter.json')
    monster_param_common = load_export_json('Character/DT_PalMonsterParameter_Common.json')
    monster_rows = {}
    for data in [monster_param, monster_param_common]:
        if data:
            if isinstance(data, list):
                for table in data:
                    if isinstance(table, dict):
                        rows = table.get('Rows', {})
                        if rows:
                            monster_rows.update(rows)
            elif isinstance(data, dict):
                rows = data.get('Rows', {})
                if rows:
                    monster_rows.update(rows)
    for pal_entry in existing['pals']:
        if not isinstance(pal_entry, dict):
            continue
        desc = pal_entry.get('description', '')
        if not desc or ('{ReferencePassive' not in desc and '{Passive' not in desc):
            continue
        asset = pal_entry.get('asset', '').lower()
        if '{ReferencePassive' in desc:
            ref_ps = pal_to_textref_passives.get(asset, [])
            if ref_ps:
                pal_entry['passives'] = ref_ps
                continue
        partner_ps = pal_to_partner_passives.get(asset, [])
        if partner_ps:
            pal_entry['passives'] = partner_ps
            continue
        skill_type = pal_to_skill_type.get(asset, '')
        if skill_type == 'StatusUp_GiveElement':
            el1 = ''
            for mk, mv in monster_rows.items():
                if mk.lower() == asset:
                    monster_row = mv
                    break
            else:
                monster_row = None
            if monster_row and isinstance(monster_row, dict):
                raw = monster_row.get('ElementType1', '')
                if isinstance(raw, str) and raw.startswith('EPalElementType::'):
                    el1 = raw.replace('EPalElementType::', '')
            if el1:
                pal_entry['passives'] = [f'AttackUp_{el1}_PartnerSkill_{r}' for r in range(1, 6)]
                continue
        def _find_monster_row(pal_id):
            r = monster_rows.get(pal_id)
            if r:
                return r
            for mk, mv in monster_rows.items():
                if mk.lower() == pal_id.lower():
                    return mv
            return None
        monster_row = _find_monster_row(asset) or _find_monster_row(pal_entry.get('asset', ''))
        if monster_row and isinstance(monster_row, dict):
            raw_passives = []
            for i in range(1, 5):
                key = f'PassiveSkill{i}'
                val = monster_row.get(key, 'None')
                if isinstance(val, str) and val not in ('None', 'none', ''):
                    raw_passives.append(val)
            if raw_passives:
                pal_entry['passives'] = raw_passives
        if not pal_entry.get('passives'):
            base_asset = _get_base_asset(asset)
            if base_asset != asset:
                base_passives = pal_to_partner_passives.get(base_asset, [])
                if base_passives:
                    pal_entry['passives'] = base_passives
    for pal_entry in existing['pals']:
        if not isinstance(pal_entry, dict):
            continue
        desc = pal_entry.get('description', '')
        asset = pal_entry.get('asset', '').lower()
        if desc and '{ActiveSkillMainValueByRank}' in desc:
            values = pal_to_main_values.get(asset, [])
            if values:
                pal_entry['active_skill_main_value'] = values
        if desc and '{ActiveSkillOverWriteEffectTime}' in desc:
            values = pal_to_overwrite_effect.get(asset, [])
            if values:
                pal_entry['active_skill_overwrite_effect'] = values
    append_text = {}
    for k, v in _append_l10n_lower.items():
        rank_match = re.search('_Rank_\\d+', k, re.IGNORECASE)
        if rank_match:
            append_text[k] = v
    ref_data = load_resource_json('reference_unlock_data.json')
    if isinstance(ref_data, dict):
        ref_data['append_text'] = append_text
        save_resource_json('reference_unlock_data.json', ref_data)
    else:
        save_resource_json('reference_unlock_data.json', {'append_text': append_text})
    print(f'  Updated {updated} pals with descriptions and partner skills')
    save_resource_json('paldata.json', existing)
def update_items_dynamic():
    print('\n=== Updating Items PSP ===')
    item_table = load_export_json('Item/DT_ItemDataTable.json')
    item_table_common = load_export_json('Item/DT_ItemDataTable_Common.json')
    all_rows = {}
    for data in [item_table, item_table_common]:
        if data:
            if isinstance(data, list):
                for table in data:
                    if isinstance(table, dict):
                        rows = table.get('Rows', {})
                        if rows:
                            all_rows.update(rows)
            elif isinstance(data, dict):
                rows = data.get('Rows', {})
                if rows:
                    all_rows.update(rows)
    if not all_rows:
        print('  No item rows for PSP. Skipping.')
        return
    result = {}
    _type_map = {'CommonWeapon': 'weapon', 'CommonArmor': 'armor'}
    for item_id, row in all_rows.items():
        if not isinstance(row, dict):
            continue
        dyn_class = row.get('ItemDynamicClass', 'None')
        if dyn_class == 'None' or not dyn_class:
            continue
        durability = row.get('Durability', 0)
        if isinstance(durability, dict):
            durability = durability.get('value', 0)
        durability = float(durability) if durability else 0.0
        dyn_type = _type_map.get(dyn_class, 'unknown')
        result[item_id] = {'dynamic': {'type': dyn_type, 'durability': durability}}
    save_resource_json('items_dynamic.json', result)
    print(f'  Total PSP entries: {len(result)}')
def update_pal_passive_data():
    print('\n=== Updating Pal Passive Data ===')
    partner_data = load_export_json('PartnerSkill/DT_PartnerSkill.json')
    partner_l10n = load_l10n_table('DT_PartnerSkillAppendText.json')
    all_rows = {}
    if partner_data:
        if isinstance(partner_data, list):
            for table in partner_data:
                if isinstance(table, dict):
                    rows = table.get('Rows', {})
                    if rows:
                        all_rows.update(rows)
        elif isinstance(partner_data, dict):
            rows = partner_data.get('Rows', {})
            if rows:
                all_rows.update(rows)
    passive_categories = {}
    try:
        passive_main = load_export_json('PassiveSkill/DT_PassiveSkill_Main.json')
        passive_common = load_export_json('PassiveSkill/DT_PassiveSkill_Main_Common.json')
        for src in [passive_main, passive_common]:
            if src:
                if isinstance(src, list):
                    for table in src:
                        if isinstance(table, dict):
                            for k, v in table.get('Rows', {}).items():
                                if isinstance(v, dict) and v.get('Category') == 'EPalPassiveCategory::SortDisplayable':
                                    passive_categories[k.lower()] = True
                elif isinstance(src, dict):
                    for k, v in src.get('Rows', {}).items():
                        if isinstance(v, dict) and v.get('Category') == 'EPalPassiveCategory::SortDisplayable':
                            passive_categories[k.lower()] = True
    except Exception:
        pass
    updated_passives = []
    seen_assets = set()
    _invalid_names = {'', 'en_text', 'en text', 'en', '-', 'none', 'unknown skill', 'unknown skills'}
    for skill_id, row_data in sorted(all_rows.items()):
        skill_id_lower = skill_id.lower()
        if skill_id_lower in seen_assets:
            continue
        seen_assets.add(skill_id_lower)
        l10n_name = partner_l10n.get(skill_id, '') if skill_id in partner_l10n else None
        if l10n_name and l10n_name.strip().lower() not in _invalid_names:
            display_name = l10n_name
        else:
            display_name = skill_id
        passive_entry = {'name': display_name, 'asset': skill_id, 'icon': '/icons/passives/T_icon_skillstatus_rank_arrow_04.png'}
        updated_passives.append(passive_entry)
    def _clean_asset_name(asset: str) -> str:
        cleaned = asset.replace('_', ' ').strip()
        import re
        cleaned = re.sub('\\s+\\d+$', '', cleaned)
        return cleaned
    try:
        general_data = load_resource_json('passivedata.json')
        for p in general_data.get('passives', []):
            asset_lower = p.get('asset', '').lower()
            if not asset_lower or asset_lower in seen_assets:
                continue
            if asset_lower not in passive_categories:
                continue
            name = p.get('name', '')
            if name and name.strip().lower() not in _invalid_names and (name != p.get('asset', '')):
                display_name = name
            else:
                display_name = _clean_asset_name(p['asset'])
            seen_assets.add(asset_lower)
            updated_passives.append({'name': display_name, 'asset': p['asset'], 'icon': p.get('icon', '/icons/passives/T_icon_skillstatus_rank_arrow_04.png')})
    except Exception as e:
        print(f'    Warning: Could not merge passives: {e}')
    result = {'passives': updated_passives}
    save_resource_json('palpassivedata.json', result)
def update_boss_mapping():
    print('\n=== Updating Boss Mapping ===')
    wild_spawner = load_export_json('Spawner/DT_PalWildSpawner.json')
    if not wild_spawner:
        print('  No spawner data found. Skipping.')
        return
    rows = get_rows(wild_spawner)
    items_data = load_resource_json('items.json')
    boss_item_suffixes = set()
    for it in items_data.get('items', []):
        if it.get('type_b') == 'EPalItemTypeB::Essential_BossReward':
            asset = it.get('asset', '')
            if asset.startswith('BossDefeatReward_') and asset != 'TEST_BossDefeatReward':
                boss_item_suffixes.add(asset.replace('BossDefeatReward_', ''))
    mapping = {}
    for row_key, row in rows.items():
        pal_1 = row.get('Pal_1', 'None')
        if not pal_1 or pal_1 == 'None':
            continue
        suffix = pal_1
        if suffix.startswith('BOSS_'):
            suffix = suffix[5:]
        elif suffix.startswith('Boss_'):
            suffix = suffix[5:]
        if suffix not in boss_item_suffixes:
            continue
        spawner_name = row.get('SpawnerName', '')
        if not spawner_name:
            continue
        item_asset = f'BossDefeatReward_{suffix}'
        if item_asset in mapping:
            if isinstance(mapping[item_asset], list):
                mapping[item_asset].append(spawner_name)
            else:
                mapping[item_asset] = [mapping[item_asset], spawner_name]
        else:
            mapping[item_asset] = spawner_name
    output = {'boss_defeat_flag_map': mapping}
    save_resource_json('boss_mapping.json', output)
    total_keys = sum((1 for v in mapping.values() if isinstance(v, str))) + sum((len(v) if isinstance(v, list) else 0 for v in mapping.values()))
    print(f'  Total mapped boss entries: {total_keys}')
    print(f'  Unique item assets mapped: {len(mapping)}')
def update_world_map_area_data():
    print('\n=== Updating World Map Area Data ===')
    area_data = load_export_json('WorldMapAreaData/DT_WorldMapAreaData.json')
    if not area_data:
        print('  No world map area data found. Skipping.')
        return
    rows = get_rows(area_data)
    if not rows:
        print('  No area rows found. Skipping.')
        return
    area_ids = sorted(rows.keys())
    output = {'areas': area_ids}
    save_resource_json('world_map_areas.json', output)
    print(f'  Total world map areas: {len(area_ids)}')
def update_ui_icons():
    print('\n=== Updating UI Icons ===')
    target_subdir = 'ui'
    target_dir = ICONS_DIR / target_subdir
    ensure_dir(target_dir)
    main_menu_dir = EXPORT_TEXTURES_DIR / 'UI' / 'Main_Menu'
    ingame_dir = EXPORT_TEXTURES_DIR / 'UI' / 'InGame'
    ui_icons = {}
    for num in range(0, 14):
        src = ingame_dir / f'T_icon_palwork_{num:02d}.png'
        path = copy_icon_to_resources(src, target_subdir)
        if path:
            ui_icons[f'palwork_{num:02d}'] = path
        else:
            print(f'    WARNING: palwork icon not found: T_icon_palwork_{num:02d}.png')
    src90 = ingame_dir / 'T_icon_palwork_90.png'
    path90 = copy_icon_to_resources(src90, target_subdir)
    if path90:
        ui_icons['palwork_90'] = path90
    else:
        print('    WARNING: palwork icon not found: T_icon_palwork_90.png')
    src_trust = main_menu_dir / 'T_Icon_PalFriendship_Color.png'
    path_trust = copy_icon_to_resources(src_trust, target_subdir)
    if path_trust:
        ui_icons['friendship'] = path_trust
    else:
        print('    WARNING: Trust icon not found: T_Icon_PalFriendship_Color.png')
    src_gf = main_menu_dir / 'T_Icon_PanGender_Female.png'
    path_gf = copy_icon_to_resources(src_gf, target_subdir)
    if path_gf:
        ui_icons['gender_female'] = path_gf
    else:
        print('    WARNING: Gender icon not found: T_Icon_PanGender_Female.png')
    src_gm = main_menu_dir / 'T_Icon_PanGender_Male.png'
    path_gm = copy_icon_to_resources(src_gm, target_subdir)
    if path_gm:
        ui_icons['gender_male'] = path_gm
    else:
        print('    WARNING: Gender icon not found: T_Icon_PanGender_Male.png')
    src_dna = main_menu_dir / 'T_Icon_PalGlobalInport.png'
    path_dna = copy_icon_to_resources(src_dna, target_subdir)
    if path_dna:
        ui_icons['dna'] = path_dna
    else:
        print('    WARNING: DNA icon not found: T_Icon_PalGlobalInport.png')
    src_food_on = main_menu_dir / 'T_Icon_foodamount_on.png'
    path_food_on = copy_icon_to_resources(src_food_on, target_subdir)
    if path_food_on:
        ui_icons['food_on'] = path_food_on
    else:
        print('    WARNING: Food icon not found: T_Icon_foodamount_on.png')
    src_food_off = main_menu_dir / 'T_Icon_foodamount_off.png'
    path_food_off = copy_icon_to_resources(src_food_off, target_subdir)
    if path_food_off:
        ui_icons['food_off'] = path_food_off
    else:
        print('    WARNING: Food icon not found: T_Icon_foodamount_off.png')
    src_lock = main_menu_dir / 'T_icon_PalLock.png'
    path_lock = copy_icon_to_resources(src_lock, target_subdir)
    if path_lock:
        ui_icons['lock'] = path_lock
        ui_icons['lock_1'] = path_lock
    else:
        print('    WARNING: Lock icon not found: T_icon_PalLock.png')
    src_lock0 = main_menu_dir / 'T_icon_PalLock_Unlock.png'
    path_lock0 = copy_icon_to_resources(src_lock0, target_subdir)
    if path_lock0:
        ui_icons['lock_0'] = path_lock0
    else:
        print('    WARNING: Lock icon not found: T_icon_PalLock_Unlock.png')
    src_lock2 = main_menu_dir / 'T_icon_PalLock_2.png'
    path_lock2 = copy_icon_to_resources(src_lock2, target_subdir)
    if path_lock2:
        ui_icons['lock_2'] = path_lock2
    else:
        print('    WARNING: Lock icon not found: T_icon_PalLock_2.png')
    src_lock3 = main_menu_dir / 'T_icon_PalLock_3.png'
    path_lock3 = copy_icon_to_resources(src_lock3, target_subdir)
    if path_lock3:
        ui_icons['lock_3'] = path_lock3
    else:
        print('    WARNING: Lock icon not found: T_icon_PalLock_3.png')
    src_buildup = EXPORT_TEXTURES_DIR / 'UI' / 'IngameMenu' / 'T_icon_buildup.png'
    path_buildup = copy_icon_to_resources(src_buildup, target_subdir)
    if path_buildup:
        ui_icons['buildup'] = path_buildup
    else:
        print('    WARNING: Buildup icon not found: T_icon_buildup.png')
    src_talent = EXPORT_TEXTURES_DIR / 'UI' / 'IngameMenu' / 'T_itemicon_Accessory_TalentChecker.png'
    if not src_talent.exists():
        src_talent = OTHER_ICON_DIR / 'InventoryItemIcon' / 'Texture' / 'T_itemicon_Accessory_TalentChecker.png'
    path_talent = copy_icon_to_resources(src_talent, target_subdir)
    if path_talent:
        ui_icons['talent_checker'] = path_talent
    else:
        print('    WARNING: Talent checker icon not found')
    result = {'ui_icons': ui_icons}
    save_resource_json('uidata.json', result)
    print(f'  Total UI icons: {len(ui_icons)}')
def update_lab_research_data():
    print('\n=== Updating Lab Research Data ===')
    lab_data = load_export_json('Lab/DT_LabResearchDataTable.json')
    if not lab_data:
        print('  No lab data found. Skipping.')
        return
    all_rows = {}
    if isinstance(lab_data, list):
        for table in lab_data:
            if isinstance(table, dict):
                rows = table.get('Rows', {})
                if rows:
                    all_rows.update(rows)
    elif isinstance(lab_data, dict):
        rows = lab_data.get('Rows', {})
        if rows:
            all_rows.update(rows)
    if not all_rows:
        print('  No lab research rows found. Skipping.')
        return
    save_resource_json('labresearchdata.json', all_rows)
MAP_EXPORT_DIR = EXPORT_TEXTURES_DIR / 'UI' / 'Map'
RELIC_TYPE_EXPORT_PATH = 'Player/DT_PlayerStatusRankMasterDataTable.json'
RELIC_OUTPUT_FILE = 'relic_data.json'
def update_relic_data():
    print('\n=== Updating Relic Data ===')
    data = load_export_json(RELIC_TYPE_EXPORT_PATH)
    if not data:
        print('  No relic data found. Skipping.')
        return
    rows = {}
    if isinstance(data, list):
        for table in data:
            if isinstance(table, dict):
                r = table.get('Rows', {})
                if r:
                    rows.update(r)
    elif isinstance(data, dict):
        rows = data.get('Rows', {})
    if not rows:
        print('  No relic rows found. Skipping.')
        return
    per_type = {}
    for row in rows.values():
        if not isinstance(row, dict):
            continue
        rt = row.get('RelicType', '')
        need = row.get('RequiredRelicNum', 0)
        if isinstance(need, dict):
            need = need.get('value', 0)
        if rt:
            per_type.setdefault(rt, []).append(int(need) if need else 0)
    result = {}
    for relic_type, needs in sorted(per_type.items()):
        total = sum(needs)
        result[relic_type] = {'cumulative_max': total, 'max_rank': len(needs), 'per_rank': needs}
    path = RESOURCES_DIR / RELIC_OUTPUT_FILE
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f'  Saved: {RELIC_OUTPUT_FILE} ({len(result)} relic types)')
    for rt, rd in result.items():
        print(f"    {rt}: {rd['cumulative_max']} total relics, {rd['max_rank']} ranks")
def update_map_data():
    map_files = ['T_TreeMap.png', 'T_WorldMap.png']
    for fname in map_files:
        src = MAP_EXPORT_DIR / fname
        if not src.exists():
            continue
        target = BASE_DIR / 'resources' / 'assets' / 'maps' / fname
        if not target.exists() or src.stat().st_mtime > target.stat().st_mtime:
            shutil.copy2(str(src), str(target))
def _convert_map_pngs(Image):
    for fname in ['T_TreeMap.png', 'T_WorldMap.png']:
        png = BASE_DIR / 'resources' / 'assets' / 'maps' / fname
        if not png.exists():
            continue
        stem = png.stem
        webp = BASE_DIR / 'resources' / 'assets' / 'maps' / f'{stem}.webp'
        try:
            img = Image.open(str(png))
            img.save(str(webp), 'WEBP', quality=60)
            png.unlink()
            print(f'  Converted map: {fname} -> {stem}.webp')
        except Exception as e:
            print(f'  ERROR converting map {fname}: {e}')
def _build_element_icons(monster_row: dict) -> dict:
    if not monster_row or not isinstance(monster_row, dict):
        return {}
    el1 = monster_row.get('ElementType1', '')
    el2 = monster_row.get('ElementType2', '')
    if isinstance(el1, str) and el1.startswith('EPalElementType::'):
        el1 = el1.replace('EPalElementType::', '')
    if isinstance(el2, str) and el2.startswith('EPalElementType::'):
        el2 = el2.replace('EPalElementType::', '')
    elem_map = {}
    try:
        elem_data = load_resource_json('elementdata.json')
        for e in elem_data.get('elements', []):
            if isinstance(e, dict) and 'name' in e:
                elem_map[e['name'].lower()] = e
    except Exception:
        pass
    elements = {}
    for el_name in [el1, el2]:
        if not el_name or el_name == 'None':
            continue
        ed = elem_map.get(el_name.lower())
        if ed:
            icons = ed.get('icons', {})
            entry = {'name': ed.get('display', ed['name']), 'icon': icons.get('small', ''), 'icon_large': icons.get('large', ''), 'icon_passive_base': icons.get('passive_base', '')}
            elements[ed['name']] = entry
    return elements
def update_element_data():
    print('\n=== Updating Element Data ===')
    target_dir = ICONS_DIR / 'elements'
    ensure_dir(target_dir)
    main_menu_dir = EXPORT_TEXTURES_DIR / 'UI' / 'Main_Menu'
    ingame_dir = EXPORT_TEXTURES_DIR / 'UI' / 'InGame'
    for edef in _ELEMENT_DEFS:
        idx_str = f"{edef['index']:02d}"
        icon_sets = [('passive_base', main_menu_dir, f'T_prt_pal_skill_base_element_{idx_str}'), ('large', main_menu_dir, f'T_Icon_element_{idx_str}'), ('palstatus', main_menu_dir, f'T_prt_palstatus_element_{idx_str}'), ('small', ingame_dir, f'T_Icon_element_s_{idx_str}')]
        edef['icons'] = {}
        for key, src_dir, stem in icon_sets:
            found = None
            for ext in ['.png', '.PNG']:
                src = src_dir / f'{stem}{ext}'
                if src.exists():
                    found = src
                    break
            if found:
                dst = target_dir / found.name
                if not dst.exists() or found.stat().st_mtime > dst.stat().st_mtime:
                    shutil.copy2(str(found), str(dst))
                edef['icons'][key] = f'/icons/elements/{found.name}'
            else:
                edef['icons'][key] = f'/icons/elements/{stem}.png'
                print(f'    WARNING: Element icon not found: {stem}.png')
    save_resource_json('elementdata.json', {'elements': _ELEMENT_DEFS})
    print(f'  Total elements: {len(_ELEMENT_DEFS)}')
def _convert_icons(Image):
    optimized = 0
    saved_bytes = 0
    for subdir in ['pals', 'items', 'structures', 'technologies', 'passives', 'npcs', 'elements', 'ui']:
        subdir_path = ICONS_DIR / subdir
        if not subdir_path.exists():
            continue
        for f in subdir_path.iterdir():
            if f.is_file() and f.suffix.lower() == '.png':
                webp_path = f.with_suffix('.webp')
                if webp_path.exists():
                    png_size = f.stat().st_size
                    webp_size = webp_path.stat().st_size
                    if webp_size < png_size:
                        f.unlink()
                        optimized += 1
                        saved_bytes += png_size - webp_size
                    continue
                try:
                    img = Image.open(str(f))
                    img.save(str(webp_path), 'WEBP', quality=60)
                    png_size = f.stat().st_size
                    webp_size = webp_path.stat().st_size
                    f.unlink()
                    optimized += 1
                    saved_bytes += png_size - webp_size
                except Exception:
                    pass
    if optimized:
        print(f'  Optimized {optimized} icons, saved {saved_bytes / 1024:.0f} KB')
        updated_refs = 0
        def _scan_icon_refs(data):
            nonlocal updated_refs, modified
            if isinstance(data, dict):
                for key, entries in data.items():
                    if isinstance(entries, list):
                        for entry in entries:
                            if isinstance(entry, dict):
                                if 'icon' in entry:
                                    icon = entry['icon']
                                    if icon.endswith('.png'):
                                        webp_icon = icon[:-4] + '.webp'
                                        webp_path = RESOURCES_DIR / webp_icon.lstrip('/')
                                        if webp_path.exists():
                                            entry['icon'] = webp_icon
                                            modified = True
                                            updated_refs += 1
                                icns = entry.get('icons', {})
                                if isinstance(icns, dict):
                                    for ikey, ival in list(icns.items()):
                                        if isinstance(ival, str) and ival.endswith('.png'):
                                            webp_val = ival[:-4] + '.webp'
                                            webp_path = RESOURCES_DIR / webp_val.lstrip('/')
                                            if webp_path.exists():
                                                icns[ikey] = webp_val
                                                modified = True
                                                updated_refs += 1
                    elif isinstance(entries, dict):
                        for ikey, ival in entries.items():
                            if isinstance(ival, str) and ival.endswith('.png'):
                                webp_val = ival[:-4] + '.webp'
                                webp_path = RESOURCES_DIR / webp_val.lstrip('/')
                                if webp_path.exists():
                                    data[key][ikey] = webp_val
                                    modified = True
                                    updated_refs += 1
        scan_fnames = []
        for fname in _MERGED_FILES:
            scan_fnames.append(fname)
        for fname in _MERGED_FILES_WHOLE:
            if fname not in scan_fnames:
                scan_fnames.append(fname)
        scan_fnames += ['uidata.json']
        for fname in scan_fnames:
            fpath = RESOURCES_DIR / fname
            if not fpath.exists():
                continue
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except:
                continue
            modified = False
            _scan_icon_refs(data)
            if modified:
                with open(fpath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
        if updated_refs:
            print(f'  Updated {updated_refs} icon references in data files')
    else:
        print('  No icons to optimize')
_MERGED_FILES = {'characters.json': ['pals', 'npcs'], 'skills.json': ['passives', 'skills', 'elements'], 'world.json': ['structures', 'technology'], 'items.json': ['items']}
_MERGED_FILES_WHOLE = {'world.json': ['lab_research'], 'items.json': ['items_dynamic'], 'characters.json': ['friendship']}
SPECIAL_KEEP_FILES = ['pal_exp_table.json', 'uidata.json', 'friendship.json']
def _write_merged_files():
    print('\n=== Writing Merged Game Data Files ===')
    merged_group = {}
    for merged_name, keys in _MERGED_FILES.items():
        merged = {}
        for k in keys:
            merged[k] = []
        merged_group[merged_name] = merged
    for merged_name, keys in _MERGED_FILES_WHOLE.items():
        if merged_name not in merged_group:
            merged_group[merged_name] = {}
        for k in keys:
            merged_group[merged_name][k] = {}
    src_map = {'pals': 'paldata.json', 'npcs': 'npcdata.json', 'passives': 'passivedata.json', 'skills': 'skilldata.json', 'elements': 'elementdata.json', 'structures': 'structuredata.json', 'technology': 'technologydata.json', 'items': 'itemdata.json', 'lab_research': 'labresearchdata.json', 'items_dynamic': 'items_dynamic.json', 'friendship': 'friendship.json'}
    for merged_name, merged in merged_group.items():
        for key in list(merged.keys()):
            src_fname = src_map.get(key)
            if not src_fname:
                continue
            data = load_resource_json(src_fname)
            if data:
                if isinstance(data, dict):
                    val = data.get(key, data if key in ['lab_research', 'items_dynamic', 'friendship'] else {})
                else:
                    val = data
                merged[key] = val
            else:
                print(f'  Warning: {src_fname} not found, writing empty {key}')
        path = RESOURCES_DIR / merged_name
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(merged, f, indent=4, ensure_ascii=False)
        print(f'  Written: {merged_name}')
    print('  Merged files created successfully.')
def _delete_individual_files():
    print('\n=== Cleaning Up Individual Files ===')
    individual_files = ['paldata.json', 'npcdata.json', 'passivedata.json', 'skilldata.json', 'elementdata.json', 'structuredata.json', 'technologydata.json', 'itemdata.json', 'labresearchdata.json', 'items_dynamic.json', 'palpassivedata.json']
    for fname in individual_files:
        fpath = RESOURCES_DIR / fname
        if fpath.exists():
            fpath.unlink()
            print(f'  Deleted: {fname}')
    print('  Individual files cleaned up.')
def _cleanup_stale_icons():
    referenced = set()
    scan_files = _MERGED_FILES.keys()
    for fname in scan_files:
        fpath = RESOURCES_DIR / fname
        if not fpath.exists():
            continue
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except:
            continue
        if isinstance(data, dict):
            for key, entries in data.items():
                if isinstance(entries, list):
                    for entry in entries:
                        if isinstance(entry, dict):
                            icns = entry.get('icons', {})
                            if isinstance(icns, dict):
                                for ikey, ival in icns.items():
                                    if isinstance(ival, str) and ival.startswith('/icons/'):
                                        referenced.add(ival)
                            icon = entry.get('icon', '')
                            if icon and icon.startswith('/icons/'):
                                referenced.add(icon)
                elif isinstance(entries, dict):
                    for ikey, ival in entries.items():
                        if isinstance(ival, str) and ival.startswith('/icons/'):
                            referenced.add(ival)
    def _collect_icon_refs(data, refs):
        if isinstance(data, dict):
            for v in data.values():
                _collect_icon_refs(v, refs)
        elif isinstance(data, list):
            for item in data:
                _collect_icon_refs(item, refs)
        elif isinstance(data, str) and data.startswith('/icons/'):
            refs.add(data)
    also_check = ['uidata.json', 'friendship.json']
    for fname in also_check:
        fpath = RESOURCES_DIR / fname
        if fpath.exists():
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except:
                continue
            if isinstance(data, dict):
                _collect_icon_refs(data, referenced)
    referenced_local = set()
    for icon_path in referenced:
        parts = icon_path.lstrip('/').split('/', 2)
        if len(parts) == 3:
            referenced_local.add(f'{parts[1]}/{parts[2]}')
    removed_count = 0
    for subdir in ['pals', 'items', 'structures', 'technologies', 'passives', 'npcs', 'elements', 'ui']:
        subdir_path = ICONS_DIR / subdir
        if not subdir_path.exists():
            continue
        for f in subdir_path.iterdir():
            if f.is_file():
                rel_path = f'{subdir}/{f.name}'
                if rel_path not in referenced_local:
                    f.unlink()
                    removed_count += 1
    if removed_count:
        print(f'  Removed {removed_count} stale icon files')
    else:
        print('  No stale icons to remove')
def main():
    if os.name == 'nt':
        os.system('title PalworldSaveTools - Game Data Extractor and Updater')
    vpy = _venv_python()
    if not vpy.exists() or os.path.abspath(sys.executable) != os.path.abspath(str(vpy)):
        if not _ensure_venv():
            input('Press Enter to exit...')
            sys.exit(1)
        os.execv(str(vpy), [str(vpy), __file__] + sys.argv[1:])
    logo = "\n  ___      _                _    _ ___              _____         _    \n | _ \\__ _| |_ __ _____ _ _| |__| / __| __ ___ ____|_   _|__  ___| |___\n |  _/ _` | \\ V  V / _ \\ '_| / _` \\__ \\/ _` \\ V / -_)| |/ _ \\/ _ \\(_-<\n |_| \\__,_|_|\\_/\\_/\\___/_| |_\\__,_|___/\\__,_|\\_/\\___||_|\\___/\\___/_/__/\n"
    print(logo)
    print('=' * 60)
    print('  PalworldSaveTools Game Data Extractor and Updater')
    print('=' * 60)
    print(f'  Base directory: {BASE_DIR}')
    print(f'  Resources directory: {RESOURCES_DIR}')
    print(f'  Exports directory: {EXPORTS_DIR}')
    print('=' * 60)
    ensure_dir(RESOURCES_DIR)
    for subdir in ['pals', 'items', 'structures', 'technologies', 'passives', 'npcs', 'elements', 'ui']:
        ensure_dir(ICONS_DIR / subdir)
    if not EXPORTS_DIR.exists():
        print(f'\nERROR: Exports directory not found at {EXPORTS_DIR}')
        print('Please run the Palworld exporter first to generate the required export files.')
        print('Nothing to update.\n')
        input('Press Enter to exit...')
        sys.exit(1)
    print()
    def _run_step(label, fn):
        stop = _spinner(label)
        try:
            with io.StringIO() as buf, __import__('contextlib').redirect_stdout(buf):
                fn()
        except Exception as e:
            stop.set()
            print(f'\r  [FAIL] {label} - {e}')
            return
        stop.set()
        print(f'\r  [OK]  {label}')
    global icon_name_to_path
    def _build_lookup():
        global icon_name_to_path
        icon_name_to_path = _build_icon_lookup()
    _run_step('Building icon lookup...', _build_lookup)
    _run_step('Updating element data...', update_element_data)
    _run_step('Updating pal data...', update_pal_data)
    _run_step('Updating pal descriptions...', update_pal_descriptions)
    _run_step('Updating NPC data...', update_npc_data)
    _run_step('Updating item data...', update_item_data)
    _run_step('Updating structure data...', update_structure_data)
    _run_step('Updating passive data...', update_passive_data)
    _run_step('Updating technology data...', update_technology_data)
    _run_step('Updating skill data...', update_skill_data)
    _run_step('Updating pal EXP table...', update_pal_exp_table)
    _run_step('Updating friendship data...', update_friendship_data)
    _run_step('Updating items dynamic...', update_items_dynamic)
    _run_step('Updating pal passive data...', update_pal_passive_data)
    _run_step('Updating lab research data...', update_lab_research_data)
    _run_step('Updating relic data...', update_relic_data)
    _run_step('Updating UI icons...', update_ui_icons)
    _run_step('Updating boss mapping...', update_boss_mapping)
    _run_step('Updating world map areas...', update_world_map_area_data)
    _run_step('Updating map data...', update_map_data)
    _run_step('Writing merged game data files...', _write_merged_files)
    _run_step('Deleting individual source files...', _delete_individual_files)
    _run_step('Cleaning up unused icons...', _cleanup_stale_icons)
    print('\n=== Optimizing assets (PNG -> WEBP) ===')
    try:
        from PIL import Image
        has_pil = True
    except ImportError:
        has_pil = False
        Image = None
        print('  Pillow not available, will copy files as-is')
    if has_pil:
        _run_step('Converting map textures...', lambda: _convert_map_pngs(Image))
    if has_pil:
        _run_step('Converting icons...', lambda: _convert_icons(Image))
    else:
        print('  No icons to optimize')
    print('\n' + '=' * 60)
    print(logo)
    print('=' * 60)
    print('  Update successfully completed! Enjoy latest update!')
    print('=' * 60)
    input('\nPress Enter to exit...')
if __name__ == '__main__':
    main()