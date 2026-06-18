@echo off
title PalworldSaveTools Clear Fog
cd /d "%~dp0\.."
where uv >nul 2>&1 || (
    echo uv not found. Install from https://docs.astral.sh/uv/
    pause
    exit /b 1
)
if exist .venv\Scripts\python.exe (
    rmdir /s /q .venv
)
uv venv .venv
uv pip install --no-cache -r requirements.txt
if "%~1"=="" (
    echo No .sav file specified. Drag a .sav file onto this .cmd.
    pause
    exit /b 1
)
".venv\Scripts\python.exe" scripts\scrs\clear_fog.py %*
if exist uv.lock del uv.lock
pause
exit /b %errorlevel%
