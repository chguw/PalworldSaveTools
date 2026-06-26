from __future__ import annotations

from fastapi import APIRouter

from web.backend import __version__
from web.backend.schemas import HealthResponse
from web.backend.state import save_state

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        version=__version__,
        save_loaded=save_state.is_loaded(),
    )
