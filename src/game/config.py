import json
import os

_CONFIG_FILE = os.path.join(os.path.dirname(__file__), "..", "nightwatch_config.json")

_DEFAULTS: dict = {
    "resolution":  "1080p",
    "quality":     "Hoch",
    "master_vol":  80,
    "music_vol":   55,
    "sfx_vol":     80,
}

_data: dict = {}


def load() -> None:
    """Lädt die Konfigurationsdatei, oder legt Standardwerte an."""
    global _data
    if os.path.exists(_CONFIG_FILE):
        try:
            with open(_CONFIG_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            _data = {**_DEFAULTS, **loaded}
        except (json.JSONDecodeError, OSError):
            _data = dict(_DEFAULTS)
    else:
        _data = dict(_DEFAULTS)


def save() -> None:
    """Schreibt die aktuelle Konfiguration in die Datei."""
    try:
        with open(_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(_data, f, ensure_ascii=False, indent=2)
    except OSError as e:
        print(f"[Config] Konnte Konfiguration nicht speichern: {e}")


def get(key: str, default=None):
    """Gibt einen Konfigurationswert zurück."""
    if not _data:
        load()
    return _data.get(key, default if default is not None else _DEFAULTS.get(key))


def set_val(key: str, value) -> None:
    """Setzt einen Konfigurationswert (ohne sofortiges Speichern)."""
    if not _data:
        load()
    _data[key] = value


load()
