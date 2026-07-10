# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

import customtkinter


ROOT = Path(SPECPATH).resolve()
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
    contents_directory=".",
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    name="ytdlp-gui",
)
