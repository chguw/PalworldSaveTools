@echo off
title PalworldSaveTools Auto-Update
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
    if exist "scripts\Level.sav" (
        ".venv\Scripts\python.exe" scripts\scrs\auto_update.py "scripts\Level.sav"
    ) else (
        echo No Level.sav found in scripts folder. Drag a .sav file onto this .cmd.
        pause
        exit /b 1
    )
) else (
        ".venv\Scripts\python.exe" scripts\scrs\auto_update.py %*
)
if exist uv.lock del uv.lock
pause
exit /b %errorlevel%
