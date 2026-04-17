@echo off
title Smart Attendance System
echo ========================================
echo   Smart Attendance System - Launcher
echo ========================================
echo.

:: Check for virtual environment
if exist ".venv\Scripts\activate.bat" (
    echo [*] Activating virtual environment...
    call .venv\Scripts\activate.bat
) else (
    echo [!] No .venv found. Using system Python.
)

echo [*] Starting Streamlit server...
echo [*] Open http://localhost:8502 in your browser.
echo.
streamlit run app.py --server.port 8502 --server.headless true --browser.gatherUsageStats false

pause
