@echo off
echo ============================================================
echo AI Interview Analyzer - Starting Application
echo ============================================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo ERROR: Virtual environment not found!
    echo Please run setup.bat first
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Check if dependencies are installed
python -c "import flask" >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Dependencies not installed!
    echo Please run setup.bat first
    pause
    exit /b 1
)

echo Starting AI Interview Analyzer...
echo.
echo The application will open in your browser at:
echo http://localhost:5000
echo.
echo Press CTRL+C to stop the server
echo ============================================================
echo.

REM Start the application
python app.py

pause
