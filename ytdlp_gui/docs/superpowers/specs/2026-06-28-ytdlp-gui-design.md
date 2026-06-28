# yt-dlp GUI — Design Spec
Date: 2026-06-28

## Overview

A cross-platform desktop GUI for yt-dlp, targeting Mac and Windows. Users can paste a YouTube (or any yt-dlp-supported) URL, choose format and quality, pick a save folder, and download — including full playlist support. Built with Python + CustomTkinter, distributed as a standalone executable via PyInstaller.

## Architecture

```
ytdlp_gui/
├── app.py              # Entry point — creates and runs MainWindow
├── ui/
│   ├── main_window.py  # Main window layout and event wiring
│   └── widgets.py      # Reusable UI components (progress bar, format selector)
├── core/
│   ├── downloader.py   # yt-dlp integration, threading, progress callbacks
│   └── config.py       # JSON config persistence (~/.ytdlp_gui_config.json)
├── requirements.txt
└── build.spec          # PyInstaller build configuration
```

Data flow:
- UI events (button clicks) → call `Downloader` methods on a background thread
- `Downloader` fires progress callbacks → UI updates via `tkinter.after()` (thread-safe)
- On app start/exit, `Config` loads/saves last-used folder, format, and quality

## UI Layout

Single-window app with dark/light mode toggle.

```
┌─────────────────────────────────────────┐
│  yt-dlp GUI                 [다크/라이트 토글] │
├─────────────────────────────────────────┤
│  URL  [ https://...              ] [붙여넣기] │
├─────────────────────────────────────────┤
│  포맷   ( mp4 ) ( mp3 ) ( webm )         │
│  화질   [ 최고화질 ▼ ]                     │
│  저장폴더 [ /Users/... ] [찾아보기]          │
├─────────────────────────────────────────┤
│         [ 다운로드 시작 ]                   │
├─────────────────────────────────────────┤
│  진행률  [████████░░░░] 65%               │
│  상태   Downloading: video.mp4...        │
└─────────────────────────────────────────┘
```

Behavior rules:
- Selecting mp3 disables the quality dropdown (audio-only, no resolution concept)
- If a playlist URL is detected, a "플레이리스트 전체 다운로드" checkbox appears automatically
- While downloading, the button label changes to "취소" and cancels the download thread on click

## Core Logic

### downloader.py

Uses yt-dlp as a Python library (import, not subprocess).

**Format strings:**
- `mp4` → `bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]`
- `mp3` → `bestaudio` + FFmpegExtractAudio postprocessor
- `webm` → `bestvideo[ext=webm]+bestaudio[ext=webm]`
- Quality filter appended when selected: e.g. `bestvideo[ext=mp4][height<=720]+bestaudio`

**Progress:**
- yt-dlp `progress_hooks` callback receives `downloaded_bytes` and `total_bytes`
- Callback posts update to main thread via `root.after(0, callback)`

**Playlist:**
- yt-dlp auto-detects playlists from the URL — no special-case code needed
- Status line shows "영상 N/M 다운로드 중..." using the `info_dict` from the hook

### config.py

- Reads/writes `~/.ytdlp_gui_config.json`
- Persists: last save folder, last format selection, last quality selection
- Loaded on startup to pre-fill UI fields; saved on every successful download

## Dependencies

```
yt-dlp
customtkinter
```

ffmpeg must be bundled via PyInstaller for mp3 conversion to work on end-user machines.

## Build & Distribution

```bash
# Mac → .app
pyinstaller --windowed --onefile --name "ytdlp-gui" app.py

# Windows → .exe
pyinstaller --windowed --onefile --name "ytdlp-gui" app.py
```

- `--windowed`: no terminal window shown
- `--onefile`: single executable output
- Must build separately on each target OS (no cross-compilation)
- ffmpeg binary included in PyInstaller bundle via `--add-binary`

## Out of Scope

- Cookies / private video login support
- Download queue with concurrent downloads
- Video thumbnail preview
- Cross-compilation (build Mac app from Windows or vice versa)
