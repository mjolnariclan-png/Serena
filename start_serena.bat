@echo off
title Serena
echo Starting Serena...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python and add it to your PATH
    pause
    exit /b 1
)

REM Change to script directory
cd /d "%~dp0"

REM Check if main.py exists
if not exist "main.py" (
    echo Error: main.py not found in current directory
    echo Please make sure you're running this from the Serena folder
    pause
    exit /b 1
)

REM Start Serena
echo Launching Serena...
python main.py

REM Pause only if there was an error
if errorlevel 1 (
    echo.
    echo Serena encountered an error. Press any key to exit...
    pause
)