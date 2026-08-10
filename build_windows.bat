@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo [1/4] Python 확인...
python --version || (
  echo Python이 필요합니다. https://www.python.org/downloads/ 에서 설치 후 PATH에 추가하세요.
  pause
  exit /b 1
)

echo [2/4] 가상환경 생성...
if not exist .venv (
  python -m venv .venv
)
call .venv\Scripts\activate.bat

echo [3/4] 의존성 설치...
python -m pip install --upgrade pip
pip install -r requirements-desktop.txt

echo [4/4] 실행 파일 빌드...
pyinstaller --noconfirm CSVColumnCompare.spec

echo.
echo 완료: dist\CSVColumnCompare.exe
explorer dist
pause
