@echo off
setlocal

REM ===========================================================
REM  Saffin OS - One-click Windows Setup (v2 - uses 'py' launcher)
REM  Place this file in the SAME folder as requirements.txt
REM  (the root of the SelfDevelopement folder), then double-click it.
REM ===========================================================

cd /d %~dp0

echo ============================================
echo  Saffin OS Setup
echo ============================================
echo.

REM --- Check the py launcher is installed ---
where py >nul 2>nul
if errorlevel 1 (
    echo [ERROR] The 'py' launcher was not found on your system.
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    echo IMPORTANT: During install, check "Add python.exe to PATH".
    echo Then re-run this setup.bat.
    pause
    exit /b 1
)

echo [OK] Python launcher found.
py --version
echo.

REM --- Create virtual environment if it doesn't exist ---
if not exist .venv (
    echo Creating virtual environment in .venv ...
    py -3 -m venv .venv
) else (
    echo Virtual environment already exists, skipping creation.
)

if not exist .venv\Scripts\activate.bat (
    echo.
    echo [ERROR] Virtual environment creation failed - .venv\Scripts\activate.bat not found.
    pause
    exit /b 1
)
echo.

REM --- Activate venv ---
call .venv\Scripts\activate.bat

REM --- Upgrade pip ---
echo Upgrading pip...
python -m pip install --upgrade pip
echo.

REM --- Install requirements ---
echo Installing dependencies from requirements.txt ...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo [ERROR] Dependency installation failed. See the messages above.
    pause
    exit /b 1
)
echo.

echo ============================================
echo  Setup complete!
echo ============================================
echo.
echo Running a quick status check to confirm everything works...
echo.
python scripts\saffin.py status

echo.
echo ----------------------------------------------------------------
echo You're all set. From now on, use "saffin.bat" to run commands.
echo Examples:
echo    saffin.bat status
echo    saffin.bat log 30 20 --notes "Worked on project X"
echo    saffin.bat review
echo    saffin.bat score
echo ----------------------------------------------------------------
echo.
pause