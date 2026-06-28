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
