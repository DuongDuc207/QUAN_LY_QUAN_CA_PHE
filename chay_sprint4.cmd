@echo off
setlocal
cd /d "%~dp0sprint4"
py app.py
if errorlevel 1 pause
endlocal
