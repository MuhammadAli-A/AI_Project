@echo off
echo ============================================================
echo    AI Interview Analyzer
echo    Facial Emotion + Speech Emotion Analysis
echo ============================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

REM Check if virtual environment exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

echo.
echo Starting Flask application...
echo Access the app at: http://localhost:5000
echo Press CTRL+C to stop
echo.
python app.py
pause
