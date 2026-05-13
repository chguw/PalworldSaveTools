from __future__ import annotations
import json
import os
from typing import Dict, Any
_LANG: str = 'zh_CN'
_RES: Dict[str, Dict[str, str]] = {}
_BASE: str = os.path.dirname(__file__)
_CFG: str = os.path.join(os.path.dirname(os.path.dirname(_BASE)), 'src', 'data', 'configs', 'config.json')
_SUPPORTED_LANGS = ['en_US', 'zh_CN', 'ru_RU', 'fr_FR', 'es_ES', 'de_DE', 'ja_JP', 'ko_KR']
def _load_json(path: str) -> Dict[str, Any]:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}
def load_resources(lang: str | None=None) -> None:
    global _RES, _LANG
    for l in _SUPPORTED_LANGS:
        _RES[l] = _load_json(os.path.join(_BASE, f'{l}.json'))
    if lang:
        _LANG = lang
def get_language() -> str:
    return _LANG
def set_language(lang: str) -> None:
    global _LANG
    if lang not in _SUPPORTED_LANGS:
        lang = 'zh_CN'
    _LANG = lang
    try:
        cfg = _load_json(_CFG) if os.path.exists(_CFG) else {}
        cfg['lang'] = lang
        with open(_CFG, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
def get_config_value(key: str, default: Any=None) -> Any:
    if os.path.exists(_CFG):
        cfg = _load_json(_CFG)
        return cfg.get(key, default)
    return default
def init_language(default_lang: str='zh_CN') -> None:
    lang = default_lang
    if os.path.exists(_CFG):
        cfg = _load_json(_CFG)
        lang = cfg.get('lang', default_lang)
    load_resources(lang)
    set_language(lang)
_DEF = object()
def t(key: str, default: str | object=_DEF, **fmt) -> str:
    src = _RES.get(_LANG, {})
    fallback = _RES.get('en_US', {})
    text = src.get(key) or fallback.get(key)
    if text is None:
        text = key if default is _DEF else default
    try:
        return text.format(**fmt) if fmt else text
    except Exception:
        return text