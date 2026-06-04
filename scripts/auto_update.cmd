@echo off
title PalworldSaveTools Auto-Update
cd /d "%~dp0\.."
where uv >nul 2>&1 || (
    echo uv not found. Install from https://docs.astral.sh/uv/
    pause
    exit /b 1
)
if "%~1"=="" (
    if exist "scripts\Level.sav" (
        uv run python scripts\scripts\auto_update.py "scripts\Level.sav"
    ) else (
        echo No Level.sav found in scripts folder. Drag a .sav file onto this .cmd.
        pause
        exit /b 1
    )
) else (
    uv run python scripts\scripts\auto_update.py %*
)
pause
exit /b %errorlevel%
