import threading
import shutil
import sys
from pathlib import Path

import yt_dlp

QUALITY_FILTER = {
    "best": "",
    "1080p": "[height<=1080]",
    "720p": "[height<=720]",
    "480p": "[height<=480]",
    "360p": "[height<=360]",
}

QUALITIES = ["best", "1080p", "720p", "480p", "360p"]


def shorten_filename(filename: str, max_length: int = 50) -> str:
    """Keep status text bounded while preserving the filename extension."""
    name = str(filename).replace("\\", "/").rsplit("/", 1)[-1]
    if len(name) <= max_length:
        return name

    suffix = Path(name).suffix
    marker = "..."
    prefix_length = max_length - len(marker) - len(suffix)
    if prefix_length <= 0:
        return name[: max_length - len(marker)] + marker
    return name[:prefix_length] + marker + suffix


def shorten_status(text: str, max_length: int = 90) -> str:
    text = str(text)
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def build_format_string(fmt: str, quality: str) -> str:
    q = QUALITY_FILTER.get(quality, "")
    if fmt == "mp4":
        return f"bestvideo{q}[ext=mp4]+bestaudio[ext=m4a]/best{q}[ext=mp4]/best"
    if fmt == "webm":
        return f"bestvideo{q}[ext=webm]+bestaudio[ext=webm]/best{q}[ext=webm]/best"
    if fmt == "mp3":
        return "bestaudio/best"
    return "best"


class _Cancelled(Exception):
    pass


def get_ffmpeg_location() -> str | None:
    """Return the bundled ffmpeg path when running from a PyInstaller app."""
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
    return shutil.which("ffmpeg")


def get_js_runtime_location() -> str | None:
    executable_name = "deno.exe" if sys.platform == "win32" else "deno"
    if getattr(sys, "frozen", False):
        roots = [Path(getattr(sys, "_MEIPASS", ""))]
        executable = getattr(sys, "executable", "")
        if executable and sys.platform != "win32":
            roots.append(Path(executable).resolve().parent.parent / "Frameworks")
        for root in roots:
            candidate = root / executable_name
            if candidate.is_file():
                return str(candidate)
        return None
    return shutil.which("deno")


def build_ydl_options(
    fmt: str,
    quality: str,
    save_folder: str,
    progress_hook,
    ffmpeg_location: str | None,
    playlist: bool = True,
    js_runtime: str | None = None,
) -> dict:
    options = {
        "format": build_format_string(fmt, quality),
        "outtmpl": f"{save_folder}/%(title)s.%(ext)s",
        "progress_hooks": [progress_hook],
        "quiet": True,
        "no_warnings": True,
        "noplaylist": not playlist,
    }
    if ffmpeg_location:
        options["ffmpeg_location"] = ffmpeg_location
    if js_runtime:
        options["js_runtimes"] = {"deno": {"path": js_runtime}}
    if fmt == "mp3":
        options["postprocessors"] = [
            {"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}
        ]
    return options


class Downloader:
    def __init__(self):
        self._thread: threading.Thread | None = None
        self._cancelled = False

    def download(
        self,
        url: str,
        fmt: str,
        quality: str,
        save_folder: str,
        on_progress,   # callback(float 0.0-1.0)
        on_status,     # callback(str)
        on_complete,   # callback(success: bool, message: str)
        playlist: bool = True,
    ) -> None:
        self._cancelled = False
        self._thread = threading.Thread(
            target=self._run,
            args=(url, fmt, quality, save_folder, on_progress, on_status, on_complete, playlist),
            daemon=True,
        )
        self._thread.start()

    def cancel(self) -> None:
        self._cancelled = True

    def _run(self, url, fmt, quality, save_folder, on_progress, on_status, on_complete, playlist):
        ydl_opts = build_ydl_options(
            fmt, quality, save_folder,
            self._make_hook(on_progress, on_status),
            get_ffmpeg_location(),
            playlist=playlist,
            js_runtime=get_js_runtime_location(),
        )
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            if not self._cancelled:
                on_complete(True, "다운로드 완료!")
        except _Cancelled:
            on_complete(False, "취소됨")
        except Exception as e:
            on_complete(False, str(e))

    def _make_hook(self, on_progress, on_status):
        def hook(d: dict):
            if self._cancelled:
                raise _Cancelled()
            if d["status"] == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
                downloaded = d.get("downloaded_bytes", 0)
                if total:
                    on_progress(downloaded / total)
                p_idx = d.get("playlist_index")
                p_count = d.get("playlist_count")
                filename = d.get("filename", "")
                if p_idx and p_count:
                    on_status(
                        f"영상 {p_idx}/{p_count} 다운로드 중... "
                        f"{shorten_filename(filename)}"
                    )
                else:
                    on_status(f"다운로드 중: {shorten_filename(filename)}")
            elif d["status"] == "finished":
                on_progress(1.0)
                on_status("변환 중...")
        return hook
