@echo off
REM ==========================================
REM AI Interview Analyzer - Complete Setup
REM With Speech Analysis Support
REM ==========================================

echo.
echo ======================================================================
echo     AI INTERVIEW ANALYZER - COMPLETE SETUP
echo     Including Speech Analysis with HuggingFace Models
echo ======================================================================
echo.

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from python.org
    pause
    exit /b 1
)

echo [1/5] Python found!
python --version
echo.

REM Create virtual environment
echo [2/5] Creating virtual environment...
if exist venv (
    echo Virtual environment already exists, skipping...
) else (
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created successfully!
)
echo.

REM Activate virtual environment
echo [3/5] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)
echo Virtual environment activated!
echo.

REM Upgrade pip
echo [4/5] Upgrading pip...
python -m pip install --upgrade pip
echo.

REM Install requirements
echo [5/5] Installing dependencies...
echo This may take 5-10 minutes, please be patient...
echo.

REM Install core packages first
echo Installing core packages...
pip install flask flask-cors opencv-python numpy pillow imutils
echo.

REM Install MediaPipe and face analysis
echo Installing face analysis packages...
pip install mediapipe tensorflow keras
echo.

REM Install speech analysis packages
echo Installing speech analysis packages (this is the big one)...
echo.
echo NOTE: PyAudio installation on Windows...
echo If PyAudio installation fails, we'll try an alternative method.
echo.

pip install librosa soundfile scipy sentencepiece accelerate
pip install transformers torch torchaudio --index-url https://download.pytorch.org/whl/cpu

REM Try to install PyAudio
pip install pyaudio
if errorlevel 1 (
    echo.
    echo ========================================================================
    echo WARNING: PyAudio installation failed!
    echo ========================================================================
    echo.
    echo PyAudio requires manual installation on Windows.
    echo Please follow ONE of these methods:
    echo.
    echo Method 1 - Using pipwin:
    echo   pip install pipwin
    echo   pipwin install pyaudio
    echo.
    echo Method 2 - Download precompiled wheel:
    echo   1. Visit: https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
    echo   2. Download the .whl file matching your Python version
    echo   3. Run: pip install downloaded-file.whl
    echo.
    echo The application will work without PyAudio, but speech analysis
    echo will not be available.
    echo.
    pause
)

echo.
echo ======================================================================
echo     INSTALLATION COMPLETE!
echo ======================================================================
echo.

REM Download speech models
echo.
echo Do you want to download speech analysis models now? (Y/N)
echo This will download ~300MB of data.
set /p choice="Enter choice: "

if /i "%choice%"=="Y" (
    echo.
    echo Downloading HuggingFace speech models...
    python setup_speech_models.py
    if errorlevel 1 (
        echo.
        echo Model download encountered an issue.
        echo You can run 'python setup_speech_models.py' later to download models.
    )
) else (
    echo.
    echo Skipping model download.
    echo Run 'python setup_speech_models.py' when you're ready.
)

echo.
echo ======================================================================
echo     SETUP SUMMARY
echo ======================================================================
echo.
echo Virtual environment: venv\
echo Python packages: Installed
echo Speech models: %choice%
echo.
echo To run the application:
echo   1. Activate virtual environment: venv\Scripts\activate
echo   2. Run: python app.py
echo   3. Open browser: http://localhost:5000
echo.
echo For speech analysis setup details, see: SPEECH_SETUP.md
echo.
echo ======================================================================
echo.

pause
