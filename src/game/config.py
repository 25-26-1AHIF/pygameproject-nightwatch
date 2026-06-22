import json
import os

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "..", "nightwatch_config.json")

DEFAULTS: dict = {
    "resolution":  "1080p",
    "quality":     "Hoch",
    "master_vol":  80,
    "music_vol":   55,
    "sfx_vol":     80,
}

_data: dict = {}


def load() -> None:
    # lädt die konfigurationsdatei, oder legt standardwerte an

    global _data
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            _data = {**DEFAULTS, **loaded}
        except (json.JSONDecodeError, OSError):
            _data = dict(DEFAULTS)
    else:
        _data = dict(DEFAULTS)


def save() -> None:
    # schreibt die aktuelle konfiguration in die datei

    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(_data, f, ensure_ascii=False, indent=2)
    except OSError as e:
        print(f"[Config] Konnte Konfiguration nicht speichern: {e}")


def get(key: str, default=None):
    # gibt einen konfigurationswert zurück

    if not _data:
        load()
    return _data.get(key, default if default is not None else DEFAULTS.get(key))


def set_val(key: str, value) -> None:
    # setzt einen konfigurationswert (ohne sofortiges speichern)

    if not _data:
        load()
    _data[key] = value

load()
