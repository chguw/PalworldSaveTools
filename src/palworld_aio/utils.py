import os
import sys
import re
import ssl
import mmap
import pickle
from palsav import json_tools
import math
import urllib.request
from palsav.archive import UUID
from palsav.gvas import GvasFile
from palsav.core import decompress_sav_to_gvas, compress_gvas_to_sav
from palsav.paltypes import PALWORLD_TYPE_HINTS
from common import get_versions, get_base_directory
from palobject import SKP_PALWORLD_CUSTOM_PROPERTIES
from palworld_aio import constants
from resource_resolver import resource_path
def resolve_name(character_id: str, name_map: dict) -> str | None:
    if not character_id:
        return None
    key = character_id.lower()
    name = name_map.get(key)
    if name is not None:
        return name
    stripped = re.sub('_v\\d+$', '', key)
    if stripped != key:
        name = name_map.get(stripped)
        if name is not None:
            return name
    return None
def check_for_update():
    try:
        context = ssl._create_unverified_context()
        req = urllib.request.Request(constants.GITHUB_RAW_URL)
        req.add_header('Range', 'bytes=0-1024')
        with urllib.request.urlopen(req, timeout=10, context=context) as r:
            content = r.read().decode('utf-8')
        match = re.search('APP_VERSION\\s*=\\s*"([^"]+)"', content)
        latest = match.group(1) if match else None
        local, _ = get_versions()
        if not latest:
            return None
        local_tuple = tuple((int(x) for x in local.split('.')))
        latest_tuple = tuple((int(x) for x in latest.split('.')))
        return {'local': local, 'latest': latest, 'update_available': latest_tuple > local_tuple}
    except Exception as e:
        print('Update check error:', e)
        return None
def as_uuid(val):
    return str(val).lower() if val else ''
def are_equal_uuids(a, b):
    return as_uuid(a) == as_uuid(b)
def fast_deepcopy(json_dict):
    return pickle.loads(pickle.dumps(json_dict, -1))
def sav_to_json(path):
    file_size = os.path.getsize(path)
    if file_size > 100 * 1024 * 1024:
        print(f'Large file detected({file_size / (1024 * 1024):.1f}MB),using memory mapping for decompression...')
        with open(path, 'rb') as f:
            with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                raw_gvas, _ = decompress_sav_to_gvas(mm.read())
    else:
        with open(path, 'rb') as f:
            data = f.read()
        raw_gvas, _ = decompress_sav_to_gvas(data)
    g = GvasFile.read(raw_gvas, PALWORLD_TYPE_HINTS, SKP_PALWORLD_CUSTOM_PROPERTIES, allow_nan=True)
    return g.dump()
def json_to_sav(j, path):
    g = GvasFile.load(j)
    t = 50 if 'Pal.PalworldSaveGame' in g.header.save_game_class_name else 49
    data = compress_gvas_to_sav(g.write(SKP_PALWORLD_CUSTOM_PROPERTIES), t)
    with open(path, 'wb') as f:
        f.write(data)
def sav_to_gvasfile(path):
    file_size = os.path.getsize(path)
    if file_size > 100 * 1024 * 1024:
        print(f'Large file detected({file_size / (1024 * 1024):.1f}MB),using memory mapping for decompression...')
        with open(path, 'rb') as f:
            with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                raw_gvas, _ = decompress_sav_to_gvas(mm.read())
    else:
        with open(path, 'rb') as f:
            data = f.read()
        raw_gvas, _ = decompress_sav_to_gvas(data)
    g = GvasFile.read(raw_gvas, PALWORLD_TYPE_HINTS, SKP_PALWORLD_CUSTOM_PROPERTIES, allow_nan=True)
    return g
def gvasfile_to_sav(gvas_file, path):
    data = gvas_file.write(SKP_PALWORLD_CUSTOM_PROPERTIES)
    t = 50 if 'Pal.PalworldSaveGame' in gvas_file.header.save_game_class_name else 49
    compressed = compress_gvas_to_sav(data, t)
    with open(path, 'wb') as f:
        f.write(compressed)
class GvasFileWrapper:
    def __init__(self, gvas_file):
        self._gvas_file = gvas_file
    def __getitem__(self, key):
        if key == 'properties':
            return self._gvas_file.properties
        elif key == 'header':
            return self._gvas_file.header.dump()
        elif key == 'trailer':
            import base64
            return base64.b64encode(self._gvas_file.trailer).decode('utf-8')
        else:
            return self._gvas_file.properties[key]
    def __contains__(self, key):
        return key in self._gvas_file.properties
    def __iter__(self):
        return iter(self._gvas_file.properties)
    def __len__(self):
        return len(self._gvas_file.properties)
    def keys(self):
        return self._gvas_file.properties.keys()
    def values(self):
        return self._gvas_file.properties.values()
    def items(self):
        return self._gvas_file.properties.items()
    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default
    @property
    def gvas_file(self):
        return self._gvas_file
def sav_to_gvas_wrapper(path):
    file_size = os.path.getsize(path)
    if file_size > 100 * 1024 * 1024:
        print(f'Large file detected({file_size / (1024 * 1024):.1f}MB), using memory mapping for decompression...')
        with open(path, 'rb') as f:
            with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                raw_gvas, _ = decompress_sav_to_gvas(mm.read())
    else:
        with open(path, 'rb') as f:
            data = f.read()
        raw_gvas, _ = decompress_sav_to_gvas(data)
    g = GvasFile.read(raw_gvas, PALWORLD_TYPE_HINTS, SKP_PALWORLD_CUSTOM_PROPERTIES, allow_nan=True)
    return GvasFileWrapper(g)
def wrapper_to_sav(wrapper, path):
    gvasfile_to_sav(wrapper.gvas_file, path)
def extract_value(data, key, default_value=''):
    value = data.get(key, default_value)
    if isinstance(value, dict):
        value = value.get('value', default_value)
        if isinstance(value, dict):
            value = value.get('value', default_value)
    return value
def safe_str(s):
    return s.encode('utf-8', 'replace').decode('utf-8')
def sanitize_filename(name):
    invalid_chars = '<>:"/\\|?*' if os.name == 'nt' else '/'
    control_chars = {chr(i) for i in range(32)}
    return ''.join((c if c not in invalid_chars and c not in control_chars else '_' for c in name))
def format_duration(s):
    d, h = divmod(int(s), 86400)
    hr, m = divmod(h, 3600)
    mm, ss = divmod(m, 60)
    return f'{d}d:{hr}h:{mm}m'
def format_duration_short(seconds):
    seconds = int(seconds)
    if seconds < 60:
        return f'{seconds}s ago'
    m, s = divmod(seconds, 60)
    if m < 60:
        return f'{m}m {s}s ago'
    h, m = divmod(m, 60)
    if h < 24:
        return f'{h}h {m}m ago'
    d, h = divmod(h, 24)
    return f'{d}d {h}h ago'
def is_valid_level(level):
    try:
        return int(level) > 0
    except:
        return False
def normalize_uid(uid):
    if isinstance(uid, dict):
        uid = uid.get('value', '')
    return str(uid).replace('-', '').lower()
def toUUID(val):
    if hasattr(val, 'bytes'):
        return val
    s = str(val).replace('-', '').lower()
    if len(s) == 32:
        return UUID.from_str(f'{s[:8]}-{s[8:12]}-{s[12:16]}-{s[16:20]}-{s[20:]}')
    return val
def restart_program():
    python = sys.executable
    os.execl(python, python, *sys.argv)
_pal_data_cache = None
def get_pal_data(character_key):
    global _pal_data_cache
    if _pal_data_cache is None:
        try:
            paldata_path = resource_path(get_base_directory(), 'game_data', 'characters.json')
            if os.path.exists(paldata_path):
                data = json_tools.load(paldata_path)
                pals_list = data.get('pals', [])
                _pal_data_cache = {pal['asset'].lower(): pal for pal in pals_list}
        except Exception as e:
            print(f'Error loading pal data: {e}')
            _pal_data_cache = {}
    default_scaling = {'scaling': {'hp': 10, 'attack': 10, 'defense': 10}}
    return _pal_data_cache.get(character_key.lower(), default_scaling)
def get_friendship_rank(trust_points):
    thr = [0, 6000, 13000, 21000, 30000, 40000, 55000, 80000, 110000, 150000, 200000]
    for r in range(len(thr) - 1, 0, -1):
        if int(trust_points) >= thr[r]:
            return r
    return 0

def _auto_awake_approx(base, is_awake, ratio=0.092):
    if not is_awake:
        return 0
    return max(0, math.floor(base * ratio))

def calculate_max_hp(pal_data, level, talent_hp=0, rank_hp=0, is_boss=False, is_lucky=False,
                     friendship_rank=0, condenser_rank=1, is_awake=False,
                     trust_bonus=None, awake_bonus=None, passive_bonus=0):
    if not pal_data:
        return 0
    bd = _hp_breakdown(pal_data, level, talent_hp, rank_hp, is_boss, is_lucky,
                       friendship_rank, condenser_rank, is_awake,
                       trust_bonus, awake_bonus, passive_bonus)
    return bd['final'] * 1000

def calculate_shot_attack(pal_data, level, talent_shot=0, rank_attack=0, friendship_rank=0,
                          condenser_rank=1, trust_bonus=None, awake_bonus=None, passive_bonus=0,
                          is_awake=False):
    if not pal_data:
        return 0
    bd = _atk_breakdown(pal_data, level, talent_shot, rank_attack, friendship_rank,
                        condenser_rank, trust_bonus, awake_bonus, passive_bonus, is_awake)
    return bd['final']

def calculate_attack(pal_data, level, talent_shot=0, rank_attack=0,
                     trust_bonus=None, awake_bonus=None, passive_bonus=0,
                     is_awake=False):
    if not pal_data:
        return 0
    return calculate_shot_attack(pal_data, level, talent_shot, rank_attack, 0,
                                 1, trust_bonus, awake_bonus, passive_bonus, is_awake)

def calculate_defense(pal_data, level, talent_defense=0, rank_defense=0, friendship_rank=0,
                      condenser_rank=1, trust_bonus=None, awake_bonus=None, passive_bonus=0,
                      is_awake=False):
    if not pal_data:
        return 0
    bd = _def_breakdown(pal_data, level, talent_defense, rank_defense, friendship_rank,
                        condenser_rank, trust_bonus, awake_bonus, passive_bonus, is_awake)
    return bd['final']

def _hp_breakdown(pal_data, level, talent_hp=0, rank_hp=0, is_boss=False, is_lucky=False,
                  friendship_rank=0, condenser_rank=1, is_awake=False,
                  trust_bonus=None, awake_bonus=None, passive_bonus=0):
    stats = (pal_data.get('scaling', None) or pal_data.get('stats', {})) if pal_data else {}
    hp_scaling = stats.get('hp', 0) if stats else 0
    hp_iv = talent_hp * 0.3 / 100
    soul_bonus = rank_hp * 0.03
    condenser_bonus = max(0, condenser_rank - 1) * 0.05
    lucky_alpha = 1.2 if (is_lucky and not is_boss) else 1.0
    base = math.floor(500 + 5 * level + hp_scaling * 0.5 * level * (1 + hp_iv) * lucky_alpha)
    base_wc = math.floor(base * (1 + condenser_bonus))
    if trust_bonus is None:
        f_hp = float(pal_data.get('friendship_hp', 0) or 0) if pal_data else 0
        trust_bonus = int(level * friendship_rank * (hp_scaling / 82.3 - f_hp * 0.0181) + 0.5) if hp_scaling else 0
    if awake_bonus is None:
        awake_bonus = _auto_awake_approx(base_wc, is_awake, 0.089)
    subtotal = base_wc + trust_bonus + awake_bonus
    return {
        'base': base, 'cond_mult': 1 + condenser_bonus, 'base_wc': base_wc,
        'trust': trust_bonus, 'awake': awake_bonus, 'subtotal': subtotal,
        'soul_mult': 1 + soul_bonus, 'passive_mult': 1 + passive_bonus,
        'final': math.floor(subtotal * (1 + soul_bonus) * (1 + passive_bonus))
    }

def _atk_breakdown(pal_data, level, talent_shot=0, rank_attack=0, friendship_rank=0,
                   condenser_rank=1, trust_bonus=None, awake_bonus=None, passive_bonus=0,
                   is_awake=False):
    stats = (pal_data.get('stats', pal_data.get('scaling', {}))) if pal_data else {}
    shot_scaling = stats.get('shot_attack', 0) if stats else 0
    attack_iv = talent_shot * 0.3 / 100
    soul_bonus = rank_attack * 0.03
    condenser_bonus = max(0, condenser_rank - 1) * 0.05
    additive_const = math.floor(1.5 * level)
    base = math.floor(additive_const + shot_scaling * 0.075 * level * (1 + attack_iv) * (1 + condenser_bonus))
    if trust_bonus is None:
        f_atk = float(pal_data.get('friendship_shotattack', 0) or 0) if pal_data else 0
        trust_bonus = math.floor(level * friendship_rank * f_atk / 8.6)
    if awake_bonus is None:
        awake_bonus = _auto_awake_approx(base, is_awake)
    subtotal = base + trust_bonus + awake_bonus
    return {
        'base': base, 'cond_mult': 1 + condenser_bonus, 'base_wc': base,
        'trust': trust_bonus, 'awake': awake_bonus, 'subtotal': subtotal,
        'soul_mult': 1 + soul_bonus, 'passive_mult': 1 + passive_bonus,
        'final': math.floor(subtotal * (1 + soul_bonus) * (1 + passive_bonus))
    }

def _def_breakdown(pal_data, level, talent_defense=0, rank_defense=0, friendship_rank=0,
                   condenser_rank=1, trust_bonus=None, awake_bonus=None, passive_bonus=0,
                   is_awake=False):
    stats = (pal_data.get('scaling', None) or pal_data.get('stats', {})) if pal_data else {}
    defense_scaling = stats.get('defense', 0) if stats else 0
    defense_iv = talent_defense * 0.3 / 100
    soul_bonus = rank_defense * 0.03
    condenser_bonus = max(0, condenser_rank - 1) * 0.05
    additive_const = math.floor(0.75 * level)
    base = math.floor(additive_const + defense_scaling * 0.075 * level * (1 + defense_iv) * (1 + condenser_bonus))
    if trust_bonus is None:
        f_def = float(pal_data.get('friendship_defense', 0) or 0) if pal_data else 0
        trust_bonus = math.floor(level * friendship_rank * f_def / 8.5)
    if awake_bonus is None:
        awake_bonus = _auto_awake_approx(base, is_awake, 0.094)
    subtotal = base + trust_bonus + awake_bonus
    return {
        'base': base, 'cond_mult': 1 + condenser_bonus, 'base_wc': base,
        'trust': trust_bonus, 'awake': awake_bonus, 'subtotal': subtotal,
        'soul_mult': 1 + soul_bonus, 'passive_mult': 1 + passive_bonus,
        'final': math.floor(subtotal * (1 + soul_bonus) * (1 + passive_bonus))
    }

def _ws_breakdown(pal_data, level, rank_craftspeed=0, passive_bonus=0):
    craft_speed = 100
    if pal_data:
        stats = pal_data.get('stats', pal_data.get('scaling', {}))
        craft_speed = stats.get('craft_speed', 100) if stats else 100
    soul_bonus = rank_craftspeed * 0.03
    ws_base = 70 + craft_speed * level // 280
    return {
        'base': ws_base, 'cond_mult': 1.0, 'base_wc': ws_base,
        'trust': 0, 'awake': 0, 'subtotal': ws_base,
        'soul_mult': 1 + soul_bonus, 'passive_mult': 1 + passive_bonus,
        'final': int(ws_base * (1 + soul_bonus) * (1 + passive_bonus) + 0.5)
    }

def stat_breakdown_tooltip(label, bd, show_awake=True):
    base = bd['base']; base_wc = bd['base_wc']; trust = bd['trust']; awake = bd['awake']
    subtotal = bd['subtotal']; sm = bd['soul_mult']; pm = bd['passive_mult']
    final = bd['final'] * 1000 if label == 'HP' else bd['final']
    cm = bd['cond_mult']
    lines = [f'<b>{label}</b>']
    if cm != 1.0 and base_wc != base:
        lines.append(f'{base}(base) → ×{cm:.2f}(cond) → {base_wc}')
    elif cm != 1.0:
        lines.append(f'Base: {base} (cond ×{cm:.2f})')
    else:
        lines.append(f'Base: {base}')
    if trust:
        lines.append(f'+{trust} trust')
    if awake and show_awake:
        lines.append(f'+{awake} awaken')
    if subtotal != base_wc:
        lines.append(f'= {subtotal}')
    mults = []
    if sm != 1.0:
        mults.append(f'×{sm:.2f} souls')
    if pm != 1.0:
        mults.append(f'×{pm:.2f} passives')
    if mults:
        lines.append(' '.join(mults))
    lines.append(f'<b>= {final}</b>')
    return '<br>'.join(lines)

def calculate_work_speed(pal_data=None, level=1, rank_craftspeed=0, passive_bonus=0):
    if not pal_data:
        return 0
    bd = _ws_breakdown(pal_data, level, rank_craftspeed, passive_bonus)
    return bd['final']
def format_character_key(character_id: str) -> str:
    character_id_lower = character_id.lower()
    if character_id_lower.startswith('boss_'):
        return character_id_lower[5:]
    elif character_id_lower.startswith('predator_'):
        return character_id_lower[9:]
    elif character_id_lower.endswith('_avatar'):
        return character_id_lower[:-7]
    else:
        return character_id_lower
def safe_dict_get(data, *keys, default=None):
    result = data
    for key in keys:
        if not isinstance(result, (dict, list)):
            return default
        if isinstance(result, dict):
            result = result.get(key, default)
            if result is default:
                return default
        elif isinstance(result, list) and isinstance(key, int):
            try:
                result = result[key]
            except (IndexError, TypeError):
                return default
        else:
            return default
    return result
def safe_nested_get(data, path, default=None):
    keys = path if isinstance(path, (list, tuple)) else path.split('.')
    return safe_dict_get(data, *keys, default=default)