import json
from pathlib import Path

CONFIG_PATH = Path.home() / ".ytdlp_gui_config.json"

DEFAULTS = {
    "save_folder": str(Path.home() / "Downloads"),
    "format": "mp4",
    "quality": "best",
}


def load() -> dict:
    if CONFIG_PATH.exists():
        try:
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            return {**DEFAULTS, **data}
        except (json.JSONDecodeError, OSError):
            return dict(DEFAULTS)
    return dict(DEFAULTS)


def save(cfg: dict) -> None:
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
