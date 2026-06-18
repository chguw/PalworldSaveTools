@echo off
title PalworldSaveTools Builder (cx_Freeze)
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
.venv\Scripts\python.exe build\cx_freeze\build_cx.py --use-venv %*
rmdir /s /q .venv
if exist uv.lock del uv.lock
pause
exit /b %errorlevel%
