@echo off
title Test Integration Imports
cd /d "%~dp0\..\.."
where uv >nul 2>&1 || (
    echo uv not found. Install from https://docs.astral.sh/uv/
    pause
    exit /b 1
)
if exist .venv\Scripts\python.exe (
    rmdir /s /q .venv
)
uv venv .venv
uv sync --all-extras
".venv\Scripts\python.exe" -m pytest tests\integration\test_imports.py %*
if exist uv.lock del uv.lock
pause
exit /b %errorlevel%
