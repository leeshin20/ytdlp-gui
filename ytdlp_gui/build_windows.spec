# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

import customtkinter
import yt_dlp_ejs


ROOT = Path(SPECPATH).resolve()
FFMPEG = ROOT / "third_party" / "ffmpeg.exe"
FFPROBE = ROOT / "third_party" / "ffprobe.exe"
DENO = ROOT / "third_party" / "deno.exe"
CTK_DIR = Path(customtkinter.__file__).resolve().parent
EJS_DIR = Path(yt_dlp_ejs.__file__).resolve().parent

if not FFMPEG.is_file():
    raise SystemExit(f"Missing bundled binary: {FFMPEG}")
if not FFPROBE.is_file():
    raise SystemExit(f"Missing bundled binary: {FFPROBE}")
if not DENO.is_file():
    raise SystemExit(f"Missing bundled binary: {DENO}")

a = Analysis(
    [str(ROOT / "app.py")],
    pathex=[str(ROOT)],
    binaries=[
        (str(FFMPEG), "."),
        (str(FFPROBE), "."),
        (str(DENO), "."),
    ],
    datas=[(str(CTK_DIR), "customtkinter"), (str(EJS_DIR), "yt_dlp_ejs")],
    hiddenimports=["customtkinter", "yt_dlp_ejs"],
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
