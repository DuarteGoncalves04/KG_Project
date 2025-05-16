@echo off
REM Batch file to launch Streamlit app with virtual environment

SET VENV_PATH=.\venv\Scripts\activate
SET APP_SCRIPT=.\src\main.py

echo Starting Knowledge Graph application...
echo.

REM Check if virtual environment exists
if not exist "%VENV_PATH%" (
    echo Error: Virtual environment not found at %VENV_PATH%
    echo Please create it with: python -m venv venv
    pause
    exit /b 1
)

REM Activate virtual environment
call %VENV_PATH%
if errorlevel 1 (
    echo Failed to activate virtual environment
    pause
    exit /b 1
)

REM Check if requirements are installed
pip show streamlit >nul 2>&1
if errorlevel 1 (
    echo Installing requirements...
    pip install -r requirements.txt
)

REM Run the Streamlit application
echo Launching application...
streamlit run %APP_SCRIPT%

pause