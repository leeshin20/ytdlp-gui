from core import downloader
from core.downloader import build_format_string


def test_mp4_best_quality():
    result = build_format_string("mp4", "best")
    assert "mp4" in result
    assert "[height<=" not in result


def test_mp4_720p():
    result = build_format_string("mp4", "720p")
    assert "[height<=720]" in result
    assert "mp4" in result


def test_mp3_ignores_quality():
    result = build_format_string("mp3", "720p")
    assert "bestaudio" in result
    assert "[height<=" not in result


def test_webm_best_quality():
    result = build_format_string("webm", "best")
    assert "webm" in result
    assert "[height<=" not in result


def test_webm_480p():
    result = build_format_string("webm", "480p")
    assert "[height<=480]" in result
    assert "webm" in result


def test_frozen_app_uses_bundled_ffmpeg(monkeypatch, tmp_path):
    ffmpeg = tmp_path / "ffmpeg"
    ffmpeg.write_bytes(b"binary")
    ffmpeg.chmod(0o755)
    monkeypatch.setattr(downloader.sys, "frozen", True, raising=False)
    monkeypatch.setattr(downloader.sys, "_MEIPASS", str(tmp_path), raising=False)
    monkeypatch.setattr(downloader.sys, "platform", "darwin")

    assert downloader.get_ffmpeg_location() == str(ffmpeg)


def test_frozen_windows_app_uses_bundled_ffmpeg(monkeypatch, tmp_path):
    ffmpeg = tmp_path / "ffmpeg.exe"
    ffmpeg.write_bytes(b"binary")
    ffmpeg.chmod(0o755)
    monkeypatch.setattr(downloader.sys, "frozen", True, raising=False)
    monkeypatch.setattr(downloader.sys, "_MEIPASS", str(tmp_path), raising=False)
    monkeypatch.setattr(downloader.sys, "platform", "win32")

    assert downloader.get_ffmpeg_location() == str(ffmpeg)


def test_ydl_options_pass_bundled_ffmpeg_location():
    options = downloader.build_ydl_options(
        "webm",
        "1080p",
        "/tmp/downloads",
        lambda _download: None,
        "/Applications/ytdlp-gui.app/Contents/Frameworks/ffmpeg",
    )

    assert options["ffmpeg_location"] == "/Applications/ytdlp-gui.app/Contents/Frameworks/ffmpeg"


def test_playlist_option_is_explicit():
    hook = lambda _download: None

    playlist_options = downloader.build_ydl_options(
        "mp4", "best", "/tmp/downloads", hook, None, playlist=True
    )
    single_video_options = downloader.build_ydl_options(
        "mp4", "best", "/tmp/downloads", hook, None, playlist=False
    )

    assert playlist_options["noplaylist"] is False
    assert single_video_options["noplaylist"] is True


def test_long_filename_is_truncated_but_extension_is_kept():
    filename = "a" * 100 + ".mp4"

    result = downloader.shorten_filename(filename, max_length=50)

    assert len(result) == 50
    assert result.endswith("...mp4")
