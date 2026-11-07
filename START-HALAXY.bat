@echo off
title Halaxy Clinic - SQLite Website
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 app.py
) else (
  where python >nul 2>nul
  if %errorlevel%==0 (
    python app.py
  ) else (
    echo Python was not found.
    echo Install Python from https://www.python.org/downloads/
    echo IMPORTANT: tick "Add Python to PATH" during installation.
    pause
  )
)
pause
