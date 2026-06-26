"""Entry point for the PST WebUI backend.

Runs either as a module (``python -m web.backend.main``) or as a bare script
path (``python /abs/path/web/backend/main.py``). The sys.path bootstrap below
handles both - a bare-script launch only puts ``web/backend`` on sys.path, so
without this the ``from web.backend...`` imports would fail.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Repo root = web/backend/main.py -> backend -> web -> <repo>
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import uvicorn

from web.backend.app import create_app
from web.backend.config import settings


def main() -> None:
    app = create_app()
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
