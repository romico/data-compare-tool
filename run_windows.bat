@echo off
chcp 65001 >nul
cd /d "%~dp0"

python --version || (
  echo Python이 필요합니다. https://www.python.org/downloads/ 에서 설치하세요.
  pause
  exit /b 1
)

if not exist .venv (
  python -m venv .venv
)
call .venv\Scripts\activate.bat
pip install -q -r requirements-desktop.txt
python desktop_app.py
