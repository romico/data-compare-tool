# CSV 컬럼 합계 비교

외부 CSV 두 파일을 선택하고, 각 파일에서 컬럼을 골라 전체 합계를 비교합니다.

## Windows에서 실행

### A) GitHub Release에서 받기 (권장)

1. https://github.com/romico/data-compare-tool/releases 에서 최신 `CSVColumnCompare.exe` 다운로드
2. 더블클릭으로 실행

새 버전 배포:

```bash
git tag v1.0.1
git push origin v1.0.1
```

또는 Actions → **Build Windows EXE** → Run workflow → version에 `v1.0.1` 입력

### B) GitHub Actions artifact

태그 없이 수동 실행하면 Artifacts에서도 받을 수 있습니다.

### C) GitLab CI로 빌드

1. GitLab에 리포지토리 push
2. CI/CD → Pipelines에서 `build-windows-exe` 확인
3. Job artifacts에서 `CSVColumnCompare.exe` 다운로드

> GitLab Windows runner(`saas-windows-medium-amd64`)가 없으면 `.gitlab-ci.yml`의 `tags`를 보유 runner에 맞게 바꾸세요.

### D) 로컬 Windows에서 빌드

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
