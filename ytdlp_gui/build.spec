# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['app.py'],
    pathex=['/Users/yubeen/ytdlp_gui'],
    binaries=[('/opt/homebrew/bin/ffmpeg', '.')],
    datas=[('/opt/miniconda3/lib/python3.12/site-packages/customtkinter', 'customtkinter')],
    hiddenimports=['customtkinter'],
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
)
