@echo off
title Serena Launcher
echo Starting Serena Launcher...
echo.
echo Hotkeys:
echo   Ctrl+Alt+S - Launch Serena
echo   Ctrl+Alt+Q - Quit Launcher
echo.
echo Launcher running in background...
echo Close this window to stop the launcher.
echo.

cd /d "%~dp0"
python launcher.py

pause