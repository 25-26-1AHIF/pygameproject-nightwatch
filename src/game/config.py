import json
import os

CONFIG_PFAD = os.path.join(os.path.dirname(__file__), "..", "nightwatch_config.json")

STANDARDS: dict = {
    "resolution": "1080p",
    "quality":    "Hoch",
    "master_vol": 80,
    "music_vol":  55,
    "sfx_vol":    80,
}

# aktuell geladene konfigurationswerte (wird beim import befüllt)
daten: dict = {}


def load() -> None:
    # konfigurationsdatei laden oder standardwerte verwenden
    daten.clear()
    if os.path.exists(CONFIG_PFAD):
        try:
            with open(CONFIG_PFAD, "r", encoding="utf-8") as f:
                geladen = json.load(f)
            daten.update({**STANDARDS, **geladen})
        except (json.JSONDecodeError, OSError):
            daten.update(STANDARDS)
    else:
        daten.update(STANDARDS)


def save() -> None:
    # aktuelle konfiguration in datei schreiben
    try:
        with open(CONFIG_PFAD, "w", encoding="utf-8") as f:
            json.dump(daten, f, ensure_ascii=False, indent=2)
    except OSError as e:
        print(f"[Config] Konnte Konfiguration nicht speichern: {e}")


def get(key: str, default=None):
    # einen konfigurationswert abfragen
    if not daten:
        load()
    return daten.get(key, default if default is not None else STANDARDS.get(key))


def set_val(key: str, value) -> None:
    # einen konfigurationswert setzen (noch nicht speichern)
    if not daten:
        load()
    daten[key] = value


load()
