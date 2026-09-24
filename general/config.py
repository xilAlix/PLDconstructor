import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SETTINGS_PATH = BASE_DIR / "general" / "settings.json"


def load_settings() -> dict:
    """Загружает настройки из settings.json."""

    with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)