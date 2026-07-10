# 릴리스 방법

macOS와 Windows 빌드는 같은 소스와 같은 버전 태그로 관리합니다. 운영체제별 영구 브랜치는 만들지 않습니다.

## 자동 빌드 확인

GitHub의 **Actions → Build and release → Run workflow**에서 수동 실행할 수 있습니다. 수동 실행은 두 플랫폼의 ZIP을 Actions artifact로 만들지만 GitHub Release를 생성하지는 않습니다.

## 새 버전 배포

배포할 커밋이 기본 브랜치에 반영된 후 버전 태그를 푸시합니다.

```bash
git tag -a v1.0.0 -m "v1.0.0"
git push origin v1.0.0
```

`v*` 태그가 푸시되면 다음 파일이 동일한 GitHub Release에 등록됩니다.

- `ytdlp-gui-mac.zip`
- `ytdlp-gui-windows.zip`
- `SHA256SUMS.txt`

릴리스 작업을 다시 실행하면 같은 태그의 기존 asset을 새 빌드로 교체합니다.

## 로컬 Windows 빌드

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt pyinstaller pytest
.\scripts\prepare_ffmpeg_windows.ps1
python -m pytest -q
.\scripts\build_windows.ps1
```

Windows FFmpeg 바이너리는 Git에 커밋하지 않고 로컬 또는 GitHub Actions 빌드 시 내려받아 체크섬을 검증합니다.
