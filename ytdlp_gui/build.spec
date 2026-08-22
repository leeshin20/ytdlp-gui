# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
import shutil

import customtkinter
import yt_dlp_ejs


ROOT = Path(SPECPATH).resolve()
FFMPEG = shutil.which('ffmpeg')
FFPROBE = shutil.which('ffprobe')
DENO = shutil.which('deno')
CTK_DIR = Path(customtkinter.__file__).resolve().parent
EJS_DIR = Path(yt_dlp_ejs.__file__).resolve().parent

if not FFMPEG:
    raise SystemExit('Missing required executable: ffmpeg')
if not FFPROBE:
    raise SystemExit('Missing required executable: ffprobe')
if not DENO:
    raise SystemExit('Missing required executable: deno')

a = Analysis(
    [str(ROOT / 'app.py')],
    pathex=[str(ROOT)],
    binaries=[
        (FFMPEG, '.'),
        (FFPROBE, '.'),
        (DENO, '.'),
    ],
    datas=[(str(CTK_DIR), 'customtkinter'), (str(EJS_DIR), 'yt_dlp_ejs')],
    hiddenimports=['customtkinter', 'yt_dlp_ejs'],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,
    name='ytdlp-gui',
    debug=False,
    strip=False,
    upx=True,
    console=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    name='ytdlp-gui',
)
app = BUNDLE(
    coll,
    name='ytdlp-gui.app',
    bundle_identifier='com.ytdlp.gui',
    codesign_identity='-',
)
