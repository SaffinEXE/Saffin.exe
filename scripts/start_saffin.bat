@echo off
REM One-click helper for Windows CMD to prepare environment and start Saffin.
REM Usage:
REM   scripts\start_saffin.bat        - starts Streamlit UI
REM   scripts\start_saffin.bat cli    - starts CLI assistant
REM   scripts\start_saffin.bat deps   - install/upgrade dependencies first

SET ROOT_DIR=%~dp0..
PUSHD %ROOT_DIR%

IF NOT EXIST .venv (
  python -m venv .venv
)

CALL .venv\Scripts\activate.bat

IF "%1"=="deps" (
  python -m pip install --upgrade pip
  python -m pip install -r requirements.txt
)

IF "%1"=="cli" (
  python scripts\saffin.py chat
) ELSE (
  python -m streamlit run app.py
)

POPD
