"""FastAPI application factory.

Mirrors the Bonfire pattern: CORS, routers under ``/api``, a ``/ws`` endpoint,
and an optional SPA static mount for the built Svelte frontend. The backend
never imports Qt - it talks only to the installed ``palsav`` package and reads
static JSON resources.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from web.backend import __version__
from web.backend.config import settings
from web.backend.routes import data, health, save, world
from web.backend.ws_manager import manager


class SpaStaticFiles(StaticFiles):
    """SPA fallback: unknown paths return index.html so client routing works."""

    async def get_response(self, path: str, scope):
        try:
            response = await super().get_response(path, scope)
            if response.status_code != 404:
                return response
        except Exception:
            response = None
        # Any 404 (or raised HTTPException) falls back to the SPA shell.
        if path != "index.html":
            return await super().get_response("index.html", scope)
        return response if response is not None else await super().get_response("index.html", scope)


def _resolve_frontend_build() -> Path | None:
    p = settings.frontend_build_dir
    if p and p.exists():
        return p.resolve()
    return None


def create_app(serve_frontend: bool | None = None) -> FastAPI:
    if serve_frontend is None:
        serve_frontend = settings.serve_frontend

    app = FastAPI(
        title="PalworldSaveTools WebUI",
        description="Web frontend for PalworldSaveTools, backed by palsav.",
        version=__version__,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router, prefix="/api")
    app.include_router(save.router, prefix="/api")
    app.include_router(world.router, prefix="/api")
    app.include_router(data.router, prefix="/api")

    @app.websocket("/ws")
    async def _ws_endpoint(websocket: WebSocket) -> None:
        await manager.connect(websocket)
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            await manager.disconnect(websocket)
        except Exception:
            await manager.disconnect(websocket)

    if serve_frontend:
        frontend_dir = _resolve_frontend_build()
        if frontend_dir is not None:
            app.mount(
                "/",
                SpaStaticFiles(directory=str(frontend_dir), html=True),
                name="frontend",
            )

    return app
