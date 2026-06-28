import threading
import yt_dlp

QUALITY_FILTER = {
    "best": "",
    "1080p": "[height<=1080]",
    "720p": "[height<=720]",
    "480p": "[height<=480]",
    "360p": "[height<=360]",
}

QUALITIES = ["best", "1080p", "720p", "480p", "360p"]


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
    ) -> None:
        self._cancelled = False
        self._thread = threading.Thread(
            target=self._run,
            args=(url, fmt, quality, save_folder, on_progress, on_status, on_complete),
            daemon=True,
        )
        self._thread.start()

    def cancel(self) -> None:
        self._cancelled = True

    def _run(self, url, fmt, quality, save_folder, on_progress, on_status, on_complete):
        ydl_opts = {
            "format": build_format_string(fmt, quality),
            "outtmpl": f"{save_folder}/%(title)s.%(ext)s",
            "progress_hooks": [self._make_hook(on_progress, on_status)],
            "quiet": True,
            "no_warnings": True,
        }
        if fmt == "mp3":
            ydl_opts["postprocessors"] = [
                {"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}
            ]
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
                    on_status(f"영상 {p_idx}/{p_count} 다운로드 중... {filename}")
                else:
                    on_status(f"다운로드 중: {filename}")
            elif d["status"] == "finished":
                on_progress(1.0)
                on_status("변환 중...")
        return hook
