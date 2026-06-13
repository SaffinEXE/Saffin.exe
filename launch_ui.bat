@echo off
setlocal

REM ===========================================================
REM  Saffin OS - Launch the UI (Streamlit app)
REM  Place this file in the SAME folder as app.py / requirements.txt
REM  (the root of the SelfDevelopement folder), then double-click it.
REM ===========================================================

cd /d %~dp0

if not exist .venv (
    echo Virtual environment not found.
    echo Please run setup.bat first.
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat

REM Make sure streamlit is installed (only installs if missing)
python -m pip show streamlit >nul 2>nul
if errorlevel 1 (
    echo Installing Streamlit (one-time)...
    python -m pip install streamlit
)

echo Launching Saffin OS UI in your browser...
python -m streamlit run app.py

endlocal
