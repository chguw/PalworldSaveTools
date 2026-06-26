from __future__ import annotations

from fastapi import APIRouter, HTTPException

from web.backend.schemas import (
    GameDataResponse, I18nResponse, LanguagesResponse, LanguageInfo,
)
from web.backend.services import data_service

router = APIRouter(prefix="/data")


@router.get("/game-data")
async def list_game_data() -> dict:
    return {"resources": data_service.available_game_data()}


@router.get("/game-data/{name}", response_model=GameDataResponse)
async def get_game_data(name: str) -> GameDataResponse:
    try:
        return GameDataResponse(name=name, data=data_service.load_game_data(name))
    except KeyError:
        raise HTTPException(404, f"Unknown game-data resource: {name}")


@router.get("/i18n/{lang}", response_model=I18nResponse)
async def get_i18n(lang: str) -> I18nResponse:
    try:
        return I18nResponse(lang=lang, keys=data_service.load_i18n(lang))
    except KeyError:
        raise HTTPException(404, f"Unknown language: {lang}")


@router.get("/languages", response_model=LanguagesResponse)
async def get_languages() -> LanguagesResponse:
    current, default, avail = data_service.list_languages()
    return LanguagesResponse(
        current=current, default=default,
        available=[LanguageInfo(**a) for a in avail],
    )
