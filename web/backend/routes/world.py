from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from web.backend.schemas import (
    BaseListResponse, ContainerListResponse, GuildListResponse,
    PalListResponse, PlayerListResponse,
)
from web.backend.services import data_service, world_service
from web.backend.state import save_state

router = APIRouter()


def _level_dict() -> dict:
    loaded = save_state.get()
    if loaded is None:
        raise HTTPException(409, "No save loaded")
    return loaded.level_dict


@router.get("/players", response_model=PlayerListResponse)
async def get_players() -> PlayerListResponse:
    players = world_service.list_players(_level_dict())
    return PlayerListResponse(players=players, total=len(players))


@router.get("/guilds", response_model=GuildListResponse)
async def get_guilds() -> GuildListResponse:
    guilds = world_service.list_guilds(_level_dict())
    return GuildListResponse(guilds=guilds, total=len(guilds))


@router.get("/bases", response_model=BaseListResponse)
async def get_bases() -> BaseListResponse:
    level = _level_dict()
    bases = world_service.list_bases(level)
    guilds = world_service.list_guilds(level)
    world_service.attach_guild_names(bases, guilds)
    return BaseListResponse(bases=bases, total=len(bases))


@router.get("/containers", response_model=ContainerListResponse)
async def get_containers(
    limit: int = Query(200, ge=1, le=5000),
) -> ContainerListResponse:
    containers = world_service.list_containers(_level_dict(), limit=limit)
    return ContainerListResponse(containers=containers, total=len(containers))


@router.get("/pals", response_model=PalListResponse)
async def get_pals(
    limit: int = Query(300, ge=1, le=5000),
) -> PalListResponse:
    pals = world_service.list_pals(
        _level_dict(),
        name_map=data_service.character_name_map(),
        limit=limit,
    )
    return PalListResponse(pals=pals, total=len(pals))
