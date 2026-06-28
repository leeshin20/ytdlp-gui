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
