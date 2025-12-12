@echo off
echo ============================================================
echo AI Interview Analyzer - Setup Script
echo ============================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/4] Python found!
echo.

REM Create virtual environment if it doesn't exist
if not exist "venv\" (
    echo [2/4] Creating virtual environment...
    python -m venv venv
    echo Virtual environment created!
) else (
    echo [2/4] Virtual environment already exists!
)
echo.

REM Activate virtual environment and install dependencies
echo [3/4] Installing dependencies (this may take 5-10 minutes)...
echo Please wait...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to install dependencies
    echo Trying again with verbose output...
    pip install -r requirements.txt
    pause
    exit /b 1
)

echo.
echo [4/4] Dependencies installed successfully!
echo.
echo ============================================================
echo Setup Complete!
echo ============================================================
echo.
echo To start the application, run: start.bat
echo Or manually: venv\Scripts\activate ^&^& python app.py
echo.
pause
