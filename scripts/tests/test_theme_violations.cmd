@echo off
title Check Theme Violations
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
uv sync
".venv\Scripts\python.exe" scripts\scrs\check_theme_violations.py --root src\ %*
if exist uv.lock del uv.lock
pause
exit /b %errorlevel%
