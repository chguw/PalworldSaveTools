@echo off
title Translate README
cd /d "%~dp0\.."
where uv >nul 2>&1 || (
    echo uv not found. Install from https://docs.astral.sh/uv/
    pause
    exit /b 1
)
uv run python scripts\scripts\translate_readme.py
pause
