@echo off
cd /d "%~dp0\.."
if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    uv venv .venv
    if errorlevel 1 (
        echo Failed to create venv
        pause
        exit /b 1
    )
    echo Installing dependencies...
    uv pip install -r requirements.txt
    if errorlevel 1 (
        echo Failed to install dependencies
        pause
        exit /b 1
    )
)
.venv\Scripts\python.exe scripts\update_game_data.py
pause
