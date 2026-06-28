from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any
from tests.test_registry import PROJECT_ROOT


CACHE_DIR = Path(__file__).resolve().parent.parent.parent / '.pytest_cache' / 'structural'


def _hash_file(path: Path) -> float:
    try:
        return os.path.getmtime(str(path))
    except OSError:
        return 0.0


def _scan_timestamps(roots: list[Path]) -> dict[str, float]:
    timestamps: dict[str, float] = {}
    for root in roots:
        if not root.exists():
            continue
        for f in root.rglob('*'):
            if f.is_file() and f.suffix in {'.py', '.json', '.toml', '.yaml', '.yml', '.cfg', '.ini', '.pem', '.crt', '.key', '.ttf', '.otf', '.woff', '.woff2', '.html', '.css', '.qss', '.png', '.jpg', '.jpeg', '.webp', '.gif', '.svg', '.ico', '.bmp', '.wav', '.mp3', '.ogg'}:
                timestamps[str(f)] = _hash_file(f)
    return timestamps


def cache_key(roots: list[Path]) -> str:
    ts = _scan_timestamps(roots)
    return json.dumps(ts, sort_keys=True)


def is_valid(cache_name: str, roots: list[Path]) -> bool:
    cache_file = CACHE_DIR / f'{cache_name}.json'
    if not cache_file.exists():
        return False
    try:
        cached = json.loads(cache_file.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, OSError):
        return False
    current = _scan_timestamps(roots)
    return cached.get('timestamps') == current


def save(cache_name: str, roots: list[Path], data: Any) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f'{cache_name}.json'
    payload = {
        'timestamps': _scan_timestamps(roots),
        'data': data,
    }
    cache_file.write_text(json.dumps(payload, indent=2, default=str), encoding='utf-8')


def load(cache_name: str) -> Any | None:
    cache_file = CACHE_DIR / f'{cache_name}.json'
    if not cache_file.exists():
        return None
    try:
        return json.loads(cache_file.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, OSError):
        return None


def clear(cache_name: str | None = None) -> None:
    if cache_name:
        cache_file = CACHE_DIR / f'{cache_name}.json'
        if cache_file.exists():
            cache_file.unlink()
    elif CACHE_DIR.exists():
        for f in CACHE_DIR.iterdir():
            if f.suffix == '.json':
                f.unlink()
