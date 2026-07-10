# Windows 빌드 작업 안내

이 문서는 Mac에서 작업하던 `ytdlp-gui`를 Windows PC로 옮긴 뒤, Windows용 실행 파일을 만들기 위한 작업 순서입니다.

## 현재 상태

- 작업 브랜치: `leeshin20`
- 최신 수정 커밋: `e3ee834`
- Mac 배포물은 `dist/ytdlp-gui-mac.zip`으로 생성됩니다.
- Mac용 빌드 설정(`build.spec`)은 `/opt/homebrew/...` 경로와 `.app` 번들을 사용하므로 Windows에서 그대로 실행하면 안 됩니다.
- Windows에서는 `ffmpeg.exe`와 `ffprobe.exe`를 함께 포함해야 합니다. 둘 중 하나라도 빠지면 yt-dlp의 병합 단계가 실패합니다.

## 1. Windows에서 프로젝트 받기

PowerShell에서 실행합니다.

```powershell
git clone -b leeshin20 https://github.com/leeshin20/ytdlp-gui.git
cd ytdlp-gui
```

## 2. Python 환경 만들기

Python 3.12 (64-bit)을 설치하고, 설치할 때 **Add Python to PATH**를 선택합니다.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller pytest
```

PowerShell이 스크립트 실행을 막으면 현재 사용자에 대해서만 다음을 한 번 실행합니다.

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

## 3. ffmpeg 준비

Windows용 `ffmpeg.exe`와 `ffprobe.exe`를 준비해 다음 위치에 둡니다.

```text
third_party/ffmpeg.exe
third_party/ffprobe.exe
```

두 파일이 실제로 실행되는지 확인합니다.

```powershell
& .\third_party\ffmpeg.exe -version
& .\third_party\ffprobe.exe -version
```

## 4. Windows용 PyInstaller spec 만들기

Mac용 `build.spec`를 수정하지 말고, 프로젝트 루트에 `build_windows.spec`를 새로 만듭니다. 아래 경로는 현재 가상환경의 `customtkinter`를 자동으로 찾도록 작성되어 있습니다.

```python
# build_windows.spec
from pathlib import Path
import customtkinter

ROOT = Path(__file__).resolve().parent
FFMPEG = ROOT / "third_party" / "ffmpeg.exe"
FFPROBE = ROOT / "third_party" / "ffprobe.exe"
CTK_DIR = Path(customtkinter.__file__).resolve().parent

if not FFMPEG.is_file():
    raise SystemExit(f"Missing bundled binary: {FFMPEG}")
if not FFPROBE.is_file():
    raise SystemExit(f"Missing bundled binary: {FFPROBE}")

a = Analysis(
    [str(ROOT / "app.py")],
    pathex=[str(ROOT)],
    binaries=[
        (str(FFMPEG), "."),
        (str(FFPROBE), "."),
    ],
    datas=[(str(CTK_DIR), "customtkinter")],
    hiddenimports=["customtkinter"],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
)

pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,
    name="ytdlp-gui",
    debug=False,
    strip=False,
    upx=False,
    console=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    name="ytdlp-gui",
)
```

## 5. Windows 경로 처리 수정

현재 `core/downloader.py`의 `get_ffmpeg_location()`은 Mac/Linux 이름인 `ffmpeg`만 찾습니다. Windows 빌드 전에 frozen 앱에서 `.exe`를 찾도록 수정해야 합니다.

`if getattr(sys, "frozen", False):` 블록을 다음 형태로 바꿉니다.

```python
    if getattr(sys, "frozen", False):
        executable_name = "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg"
        roots = [Path(getattr(sys, "_MEIPASS", ""))]
        executable = getattr(sys, "executable", "")
        if executable and sys.platform != "win32":
            roots.append(Path(executable).resolve().parent.parent / "Frameworks")
        for root in roots:
            candidate = root / executable_name
            if candidate.is_file():
                return str(candidate)
        return None
```

Windows용 테스트도 추가합니다.

```python
def test_frozen_windows_app_uses_bundled_ffmpeg(monkeypatch, tmp_path):
    ffmpeg = tmp_path / "ffmpeg.exe"
    ffmpeg.write_bytes(b"binary")
    ffmpeg.chmod(0o755)
    monkeypatch.setattr(downloader.sys, "frozen", True, raising=False)
    monkeypatch.setattr(downloader.sys, "_MEIPASS", str(tmp_path), raising=False)
    monkeypatch.setattr(downloader.sys, "platform", "win32")

    assert downloader.get_ffmpeg_location() == str(ffmpeg)
```

## 6. 테스트 실행

```powershell
python -m pytest -q
```

기존 테스트와 Windows 경로 테스트가 모두 통과해야 합니다.

## 7. Windows 앱 빌드

```powershell
Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue
pyinstaller --clean --noconfirm build_windows.spec
```

성공하면 다음 파일이 생깁니다.

```text
dist/ytdlp-gui/ytdlp-gui.exe
dist/ytdlp-gui/ffmpeg.exe
dist/ytdlp-gui/ffprobe.exe
```

개발 PC에서 먼저 실행합니다.

```powershell
& .\dist\ytdlp-gui\ytdlp-gui.exe
```

## 8. 배포용 ZIP 만들기

```powershell
Compress-Archive -Path .\dist\ytdlp-gui -DestinationPath .\dist\ytdlp-gui-windows.zip -Force
Get-FileHash .\dist\ytdlp-gui-windows.zip -Algorithm SHA256
```

친구에게는 `dist/ytdlp-gui-windows.zip`을 보내고, 압축을 해제한 폴더 안의 `ytdlp-gui.exe`를 실행하도록 안내합니다. `.exe` 하나만 따로 보내면 `ffmpeg.exe`, `ffprobe.exe`가 빠져서 다시 오류가 납니다.

## 9. Windows 보안 경고

코드 서명과 공증이 없는 개인 배포본이므로 Windows Defender SmartScreen이 경고할 수 있습니다. 파일 출처를 확인한 뒤 **More info → Run anyway**를 선택합니다. 정식 배포 시에는 Windows 코드 서명 인증서를 별도로 적용해야 합니다.

## 문제 해결 체크리스트

- `ffmpeg.exe`와 `ffprobe.exe`가 `dist/ytdlp-gui` 폴더에 모두 있는가?
- 친구에게 ZIP 전체를 보냈고, EXE만 따로 보내지 않았는가?
- `core/downloader.py`가 Windows에서 `ffmpeg.exe`를 찾도록 수정되었는가?
- `python -m pytest -q`가 통과하는가?
- 다운로드 형식이 mp4/webm/mp3 모두 동일하게 실패하는가? 그렇다면 병합 바이너리 경로를 먼저 확인합니다.
