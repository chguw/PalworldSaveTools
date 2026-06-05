@echo off
title PalworldSaveTools Clear Fog
cd /d "%~dp0\.."
where uv >nul 2>&1 || (
    echo uv not found. Install from https://docs.astral.sh/uv/
    pause
    exit /b 1
)
if not exist .venv\Scripts\python.exe (
    uv venv .venv
)
uv pip install -r requirements.txt
if "%~1"=="" (
    echo No .sav file specified. Drag a .sav file onto this .cmd.
    pause
    exit /b 1
)
".venv\Scripts\python.exe" scripts\scripts\clear_fog.py %*
pause
exit /b %errorlevel%
