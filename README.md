# CSV 컬럼 합계 비교

외부 CSV 두 파일을 선택하고, 각 파일에서 컬럼을 골라 전체 합계를 비교합니다.

## Windows에서 실행

### A) GitHub Actions로 빌드 (권장)

1. GitHub에 리포지토리 push
2. Actions 탭에서 **Build Windows EXE** 워크플로 실행 (push 시 자동, 또는 Run workflow)
3. 완료 후 Artifacts에서 `CSVColumnCompare-windows` 다운로드 → `CSVColumnCompare.exe` 실행

### B) GitLab CI로 빌드

1. GitLab에 리포지토리 push
2. CI/CD → Pipelines에서 `build-windows-exe` 확인
3. Job artifacts에서 `CSVColumnCompare.exe` 다운로드

> GitLab Windows runner(`saas-windows-medium-amd64`)가 없으면 `.gitlab-ci.yml`의 `tags`를 보유 runner에 맞게 바꾸세요.

### C) 로컬 Windows에서 빌드

1. [Python 3.11+](https://www.python.org/downloads/) 설치 (**Add python.exe to PATH**)
2. `build_windows.bat` 실행 → `dist\CSVColumnCompare.exe`

빌드 없이 바로 실행: `run_windows.bat`

## macOS에서 실행

```bash
source .venv/bin/activate
pip install -r requirements-desktop.txt
python desktop_app.py
```

```bash
pyinstaller --noconfirm CSVColumnCompare.spec
open dist/CSVColumnCompare
```

## 웹(Streamlit)

```bash
pip install -r requirements.txt
streamlit run app.py
```
