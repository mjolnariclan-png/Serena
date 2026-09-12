@echo off
title Serena Web Interface
echo Starting Serena Web Interface...
echo.

cd /d "%~dp0"

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python and add it to your PATH
    pause
    exit /b 1
)

REM Check if web_main.py exists
if not exist "web_main.py" (
    echo Error: web_main.py not found in current directory
    echo Please make sure you're running this from the Serena folder
    pause
    exit /b 1
)

REM Start Serena Web Interface
echo Launching Serena Web Interface...
echo Open http://localhost:8080 in your browser
echo.
python web_main.py

REM Pause only if there was an error
if errorlevel 1 (
    echo.
    echo Serena Web Interface encountered an error. Press any key to exit...
    pause
)