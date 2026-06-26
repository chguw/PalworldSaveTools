"""Pydantic schemas - the API contract.

These mirror the TypeScript interfaces in ``web/frontend/src/types/index.ts``.
Most fields are optional because raw save shapes vary across game versions;
the frontend treats anything missing as "unknown".
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel


# ---- health / system --------------------------------------------------------

class HealthResponse(BaseModel):
    status: str = "ok"
    version: str
    save_loaded: bool


class LanguageInfo(BaseModel):
    code: str
    label: str


class LanguagesResponse(BaseModel):
    current: str
    default: str
    available: list[LanguageInfo]


# ---- save lifecycle ---------------------------------------------------------

class SaveSummary(BaseModel):
    filename: str
    save_dir: str
    players_dir: str
    class_name: str
    save_type: int
    file_size: int
    loaded_at: float


class WorldCounts(BaseModel):
    guilds: int = 0
    players: int = 0
    bases: int = 0
    containers: int = 0
    characters: int = 0


class SaveStateResponse(BaseModel):
    loaded: bool
    summary: Optional[SaveSummary] = None
    counts: Optional[WorldCounts] = None


class LoadResponse(BaseModel):
    summary: SaveSummary
    counts: WorldCounts


class ExportResponse(BaseModel):
    status: str
    filename: str
    size_bytes: int


# ---- world viewers (read-only) ---------------------------------------------

class PlayerSummary(BaseModel):
    uid: str
    name: str = "Unknown"
    guild_id: Optional[str] = None
    guild_name: Optional[str] = None
    last_seen_seconds: Optional[float] = None
    last_seen_text: Optional[str] = None


class PlayerListResponse(BaseModel):
    players: list[PlayerSummary]
    total: int


class GuildSummary(BaseModel):
    id: str
    name: str = "Unnamed Guild"
    player_count: int = 0
    base_count: int = 0
    leader_uid: Optional[str] = None
    player_uids: list[str] = []


class GuildListResponse(BaseModel):
    guilds: list[GuildSummary]
    total: int


class BaseSummary(BaseModel):
    id: str
    guild_id: Optional[str] = None
    guild_name: Optional[str] = None
    location: Optional[tuple[float, float, float]] = None
    worker_count: int = 0
    raw: dict[str, Any] = {}


class BaseListResponse(BaseModel):
    bases: list[BaseSummary]
    total: int


class ContainerSummary(BaseModel):
    id: str
    owner_player_uid: Optional[str] = None
    guild_id: Optional[str] = None
    slot_count: int = 0
    item_count: int = 0


class ContainerListResponse(BaseModel):
    containers: list[ContainerSummary]
    total: int


class PalSummary(BaseModel):
    instance_id: str
    character_id: str = ""
    display_name: Optional[str] = None
    owner_uid: Optional[str] = None
    nickname: Optional[str] = None
    level: Optional[int] = None
    rank: Optional[int] = None
    is_illegal: bool = False


class PalListResponse(BaseModel):
    pals: list[PalSummary]
    total: int


# ---- static data -----------------------------------------------------------

class GameDataResponse(BaseModel):
    name: str
    data: Any


class I18nResponse(BaseModel):
    lang: str
    keys: dict[str, str]
