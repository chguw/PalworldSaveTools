"""Runtime configuration for the WebUI backend.

All values are overridable via environment variables so the same code runs in
dev (separate Vite + uvicorn processes) and production (single process serving
the built SPA).
"""

from __future__ import annotations

import os
from pathlib import Path

from web.backend import paths


def _env_bool(name: str, default: bool) -> bool:
    val = os.environ.get(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}


class Settings:
    # Networking
    host: str = os.environ.get("PST_WEB_HOST", "127.0.0.1")
    port: int = int(os.environ.get("PST_WEB_PORT", "16921"))

    # When False the SPA static mount is skipped (dev mode uses Vite directly).
    serve_frontend: bool = _env_bool("PST_WEB_SERVE_FRONTEND", True)

    # Allow overriding the frontend build location for frozen/packaged builds.
    frontend_build_dir: Path = Path(
        os.environ.get("PST_WEB_FRONTEND_BUILD", str(paths.FRONTEND_BUILD_DIR))
    )

    # CORS: open in local-single-user mode; tighten for a real deployment.
    cors_origins: list[str] = ["*"]


settings = Settings()
