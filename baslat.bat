@echo off
cd /d "%~dp0"
if not exist "venv\Scripts\python.exe" (
    echo venv klasoru bulunamadi.
    echo Once kurulum yapin: python -m venv venv ve sonra venv\Scripts\activate ve pip install -r requirements.txt
    pause
    exit /b 1
)
"venv\Scripts\python.exe" launcher.py
if errorlevel 1 pause
