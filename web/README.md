# PST WebUI

A decoupled web interface for PalworldSaveTools: a **Svelte 5 + Tailwind** frontend
with a lightweight **FastAPI** backend that wraps the project's `palsav` engine.

## Design provenance

- **Visual/layout/vibe**: ported from `web/.web_ref` (a scraped Reflex project) —
  color tokens, typography, navigation structure. **No functional logic** is taken
  from `.web_ref`; it is a visual reference only.
- **Functional logic**: comes exclusively from the main project. The backend talks
  directly to the installed `palsav` workspace package (SAV<->dict) and reads static
  game-data/i18n JSON from `resources/`. It does **not** import `palworld_aio` (Qt-bound)
  and runs fully headless.

## Layout

```
web/
  backend/    FastAPI app, services, routes, schemas  (uv run python -m web.backend.main)
  frontend/   SvelteKit 5 + Tailwind SPA              (npm run dev / build)
  .web_ref/   visual reference only (do not import)
```

## Run — production (single process)

The FastAPI server serves the built SPA, the `/api` REST endpoints, and the `/ws`
WebSocket on one port. This is the "local desktop replacement" mode.

```bash
# 1. build the SPA once
cd web/frontend && npm install && npm run build && cd ../..

# 2. serve everything on http://127.0.0.1:8000
uv run python -m web.backend.main
```

Open <http://127.0.0.1:8000>, click **Load Save**, point it at a `Level.sav`
(inside a folder that has a `Players/` sibling).

## Run — development (two processes)

Hot-reloading frontend + backend:

```bash
# terminal 1: backend (API + ws only, no SPA mount)
PST_WEB_SERVE_FRONTEND=0 uv run python -m web.backend.main
# -> http://127.0.0.1:8000  (API)

# terminal 2: Vite dev server (proxies /api and /ws to :8000)
cd web/frontend && npm run dev
# -> http://127.0.0.1:5173  (open this in your browser)
```

## API surface (15 endpoints)

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | backend liveness + save-loaded flag |
| GET | `/api/save/state` | current loaded-save summary + counts |
| POST | `/api/save/load` | load `Level.sav` from a filesystem path |
| POST | `/api/save/upload` | load from an uploaded `.sav` blob |
| POST | `/api/save/export` | re-encode + download the current save |
| DELETE | `/api/save` | unload |
| GET | `/api/players` `/guilds` `/bases` `/containers` `/pals` | read-only viewers |
| GET | `/api/data/game-data` `/{name}` | game data JSON |
| GET | `/api/data/i18n/{lang}` `/languages` | translations |
| WS | `/ws` | save-state push |

## Round-trip fidelity

The backend uses the **full** `PALWORLD_CUSTOM_PROPERTIES` table (CLI-grade), not
the GUI's 6-path no-op override, so foliage/spawner/MapObject data round-trips
completely. The `save_type` reported by decompression is reused on encode for
byte-faithful re-compression.
