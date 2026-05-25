@echo off
cd /d "%~dp0\.."
python scripts\update_game_data.py
pause
