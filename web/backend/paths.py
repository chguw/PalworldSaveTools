"""Resource path resolution.

The backend lives at ``<repo>/web/backend`` but reads game-data, i18n and
config JSON from the main project tree (``<repo>/resources`` and
``<repo>/src/data``). Nothing under ``src/palworld_aio`` is touched (Qt-bound).
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

# web/backend/paths.py -> web/backend -> web -> <repo_root>
REPO_ROOT: Path = Path(__file__).resolve().parents[2]

RESOURCES_DIR: Path = REPO_ROOT / "resources"
GAME_DATA_DIR: Path = RESOURCES_DIR / "game_data"
I18N_DIR: Path = RESOURCES_DIR / "i18n"
CONFIGS_DIR: Path = REPO_ROOT / "src" / "data" / "configs"

# Built Svelte SPA is served from here in production.
FRONTEND_DIR: Path = REPO_ROOT / "web" / "frontend"
FRONTEND_BUILD_DIR: Path = FRONTEND_DIR / "build"


@lru_cache(maxsize=1)
def game_data_files() -> list[str]:
    """Names of every ``*.json`` (no extension) under resources/game_data."""
    if not GAME_DATA_DIR.is_dir():
        return []
    return sorted(p.stem for p in GAME_DATA_DIR.glob("*.json"))


@lru_cache(maxsize=1)
def i18n_languages() -> list[str]:
    """Available language codes, e.g. ``['de_DE', 'en_US', ...]``."""
    if not I18N_DIR.is_dir():
        return []
    return sorted(p.stem for p in I18N_DIR.glob("*.json") if p.stem != "config")
