import json
import os

_CONFIG_PFAD = os.path.join(os.path.dirname(__file__), "..", "nightwatch_config.json")

_STANDARDS: dict = {
    "resolution": "1080p",
    "quality":    "Hoch",
    "master_vol": 80,
    "music_vol":  55,
    "sfx_vol":    80,
}

# aktuell geladene konfigurationswerte (wird beim import befüllt)
_daten: dict = {}


def load() -> None:
    # konfigurationsdatei laden oder standardwerte verwenden
    _daten.clear()
    if os.path.exists(_CONFIG_PFAD):
        try:
            with open(_CONFIG_PFAD, "r", encoding="utf-8") as f:
                geladen = json.load(f)
            _daten.update({**_STANDARDS, **geladen})
        except (json.JSONDecodeError, OSError):
            _daten.update(_STANDARDS)
    else:
        _daten.update(_STANDARDS)


def save() -> None:
    # aktuelle konfiguration in datei schreiben
    try:
        with open(_CONFIG_PFAD, "w", encoding="utf-8") as f:
            json.dump(_daten, f, ensure_ascii=False, indent=2)
    except OSError as e:
        print(f"[Config] Konnte Konfiguration nicht speichern: {e}")


def get(key: str, default=None):
    # einen konfigurationswert abfragen
    if not _daten:
        load()
    return _daten.get(key, default if default is not None else _STANDARDS.get(key))


def set_val(key: str, value) -> None:
    # einen konfigurationswert setzen (noch nicht speichern)
    if not _daten:
        load()
    _daten[key] = value


load()
