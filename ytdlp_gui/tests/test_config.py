import json
import pytest
from pathlib import Path
from unittest.mock import patch


def test_load_returns_defaults_when_no_file(tmp_path):
    config_path = tmp_path / "config.json"
    with patch("core.config.CONFIG_PATH", config_path):
        from core import config
        result = config.load()
    assert result["format"] == "mp4"
    assert result["quality"] == "best"
    assert "save_folder" in result


def test_save_and_load_roundtrip(tmp_path):
    config_path = tmp_path / "config.json"
    with patch("core.config.CONFIG_PATH", config_path):
        from core import config
        config.save({"format": "mp3", "quality": "720p", "save_folder": "/tmp"})
        result = config.load()
    assert result["format"] == "mp3"
    assert result["quality"] == "720p"
    assert result["save_folder"] == "/tmp"


def test_load_falls_back_to_defaults_on_corrupt_file(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text("not valid json")
    with patch("core.config.CONFIG_PATH", config_path):
        from core import config
        result = config.load()
    assert result["format"] == "mp4"
