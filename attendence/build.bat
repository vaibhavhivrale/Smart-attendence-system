@echo off
title Smart Attendance System — Build
echo ========================================
echo   Building Standalone Executable
echo ========================================
echo.

:: Activate venv
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

:: Install PyInstaller if missing
pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo [*] Installing PyInstaller...
    pip install pyinstaller
)

echo [*] Building executable...
echo.

pyinstaller --noconfirm --onedir --name SmartAttendance ^
    --add-data "src;src" ^
    --add-data "config.py;." ^
    --add-data "assets;assets" ^
    --hidden-import streamlit ^
    --hidden-import streamlit_option_menu ^
    --hidden-import cv2 ^
    --hidden-import bcrypt ^
    --hidden-import plotly ^
    --collect-all streamlit ^
    --collect-all streamlit_option_menu ^
    app.py

echo.
echo ========================================
echo   Build complete! Output in dist/SmartAttendance/
echo   To run: dist\SmartAttendance\SmartAttendance.exe
echo ========================================
pause
