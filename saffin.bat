@echo off
setlocal

REM ===========================================================
REM  Saffin OS - Command Runner
REM  Place this file in the SAME folder as requirements.txt
REM  (the root of the SelfDevelopement folder).
REM
REM  Usage examples:
REM    saffin.bat status
REM    saffin.bat log 30 20 --notes "Worked on project X"
REM    saffin.bat idea "New idea title" --description "details"
REM    saffin.bat score
REM    saffin.bat review
REM    saffin.bat chat
REM ===========================================================

cd /d %~dp0

if not exist .venv (
    echo Virtual environment not found.
    echo Please run setup.bat first.
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat
python scripts\saffin.py %*

endlocal
