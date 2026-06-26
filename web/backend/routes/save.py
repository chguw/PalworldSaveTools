from __future__ import annotations

import time
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from web.backend.schemas import (
    LoadResponse, SaveStateResponse, SaveSummary, WorldCounts,
)
from web.backend.services import save_service, world_service
from web.backend.state import LoadedSave, save_state

router = APIRouter(prefix="/save")

_LEVEL_SUFFIX = "Level.sav"


class LoadPathRequest(BaseModel):
    path: str


def _summarize(gvas, save_type: int, path: Path, level_dict: dict) -> LoadedSave:
    return LoadedSave(
        filename=path.name,
        save_dir=str(path.parent),
        players_dir=str(path.parent / "Players"),
        save_type=save_type,
        class_name=gvas.header.save_game_class_name,
        file_size=path.stat().st_size,
        loaded_at=time.time(),
        gvas=gvas,
        level_dict=level_dict,
    )


@router.get("/state", response_model=SaveStateResponse)
async def get_state() -> SaveStateResponse:
    loaded = save_state.get()
    if loaded is None:
        return SaveStateResponse(loaded=False)
    summary = SaveSummary(
        filename=loaded.filename,
        save_dir=loaded.save_dir,
        players_dir=loaded.players_dir,
        class_name=loaded.class_name,
        save_type=loaded.save_type,
        file_size=loaded.file_size,
        loaded_at=loaded.loaded_at,
    )
    return SaveStateResponse(
        loaded=True, summary=summary,
        counts=WorldCounts(**world_service.count_world(loaded.level_dict)),
    )


@router.post("/load", response_model=LoadResponse)
async def load_from_path(body: LoadPathRequest) -> LoadResponse:
    p = Path(body.path).expanduser()
    if not p.name.endswith(_LEVEL_SUFFIX):
        raise HTTPException(400, f"Path must point to a {_LEVEL_SUFFIX} file")
    if not p.is_file():
        raise HTTPException(404, f"File not found: {p}")
    players = p.parent / "Players"
    if not players.is_dir():
        raise HTTPException(400, "Expected a 'Players' folder next to Level.sav")
    with save_state.lock:
        try:
            gvas, save_type, level_dict, size = save_service.decode_file(p)
        except save_service.SaveDecodeError as exc:
            raise HTTPException(422, str(exc))
        save_state.set(_summarize(gvas, save_type, p, level_dict))
    return LoadResponse(
        summary=SaveSummary(
            filename=p.name, save_dir=str(p.parent), players_dir=str(players),
            class_name=gvas.header.save_game_class_name, save_type=save_type,
            file_size=size, loaded_at=time.time(),
        ),
        counts=WorldCounts(**world_service.count_world(level_dict)),
    )


@router.post("/upload", response_model=LoadResponse)
async def upload_save(file: UploadFile = File(...)) -> LoadResponse:
    data = await file.read()
    if not data:
        raise HTTPException(400, "Empty upload")
    with save_state.lock:
        try:
            gvas, save_type, level_dict = save_service.decode_bytes(data)
        except save_service.SaveDecodeError as exc:
            raise HTTPException(422, str(exc))
        loaded = LoadedSave(
            filename=file.filename or "Level.sav",
            save_dir="(uploaded)", players_dir="(unknown)",
            save_type=save_type, class_name=gvas.header.save_game_class_name,
            file_size=len(data), loaded_at=time.time(),
            gvas=gvas, level_dict=level_dict,
        )
        save_state.set(loaded)
    return LoadResponse(
        summary=SaveSummary(
            filename=loaded.filename, save_dir=loaded.save_dir,
            players_dir=loaded.players_dir, class_name=loaded.class_name,
            save_type=loaded.save_type, file_size=loaded.file_size,
            loaded_at=loaded.loaded_at,
        ),
        counts=WorldCounts(**world_service.count_world(level_dict)),
    )


@router.post("/export", response_class=StreamingResponse)
async def export_save() -> StreamingResponse:
    loaded = save_state.require()
    with save_state.lock:
        try:
            stream = save_service.encode_to_stream(loaded.gvas, loaded.save_type)
        except save_service.SaveDecodeError as exc:
            raise HTTPException(500, str(exc))
    size = len(stream.getvalue())
    return StreamingResponse(
        stream,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{loaded.filename}"',
            "X-Export-Size": str(size),
        },
    )


@router.delete("", response_model=SaveStateResponse)
async def unload() -> SaveStateResponse:
    save_state.clear()
    return SaveStateResponse(loaded=False)
