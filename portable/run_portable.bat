@echo off
echo Starting Experimental Results Sharing Tool...
echo Database will be stored on OneDrive if available

REM Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Python is not installed or not in PATH
    echo Please install Python 3.6+ and try again
    pause
    exit /b 1
)

REM Check if pip is installed
pip --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo pip is not installed or not in PATH
    echo Please install pip and try again
    pause
    exit /b 1
)

REM Check if requirements are installed
echo Checking requirements...
pip install -r requirements.txt

REM Run the application
echo Starting application...
cd ..
python run.py

pause
