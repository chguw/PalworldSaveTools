@echo off
title Update Translation Keys
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
".venv\Scripts\python.exe" scripts\scripts\update_translation_keys.py %*
pause
exit /b %errorlevel%
