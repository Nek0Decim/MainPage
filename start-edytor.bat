@echo off
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 edytor.py
) else (
  python edytor.py
)
pause
