import json
import os
import datetime
import pygame
from game_variables.game_variables import GameVariables

SW = GameVariables.SCREEN_W
SH = GameVariables.SCREEN_H

_HIGHSCORE_DATEI = os.path.join(os.path.dirname(__file__), "..", "highscores.json")

HighscoreEintrag = dict


def load_highscores() -> list[HighscoreEintrag]:
    # lädt die highscore-liste aus der json-datei

    if not os.path.exists(_HIGHSCORE_DATEI):
        return []
    try:
        with open(_HIGHSCORE_DATEI, "r", encoding="utf-8") as f:
            data = json.load(f)
        valid = [
            e for e in data
            if isinstance(e, dict)
            and "name" in e and "time" in e and "date" in e
        ]
        return sorted(valid, key=lambda e: e["time"])
    except (json.JSONDecodeError, OSError):
        return []


def save_highscore(name: str, sekunden: float) -> int:
    # speichert einen neuen eintrag und gibt den erreichten rang zurück

    eintraege = load_highscores()

    neuer = HighscoreEintrag({
        "name": name[:12],
        "time": round(sekunden, 2),
        "date": datetime.datetime.now().strftime("%d.%m.%Y"),
    })
    eintraege.append(neuer)
    eintraege = sorted(eintraege, key=lambda e: e["time"])[:10]

    try:
        with open(_HIGHSCORE_DATEI, "w", encoding="utf-8") as f:
            json.dump(eintraege, f, ensure_ascii=False, indent=2)
    except OSError:
        pass

    for i, e in enumerate(eintraege):
        if e["name"] == neuer["name"] and e["time"] == neuer["time"]:
            return i + 1
    return -1


def draw_highscore_screen(surface, clock_ms: int) -> None:
    # zeichnet den kompletten highscore-bildschirm

    surface.fill((5, 5, 15))

    fnt_titel = pygame.font.SysFont("monospace", 48, bold=True)
    fnt_kopf  = pygame.font.SysFont("monospace", 16, bold=True)
    fnt_eing  = pygame.font.SysFont("monospace", 15)
    fnt_klein = pygame.font.SysFont("monospace", 13)

    titel = fnt_titel.render("HIGHSCORES", True, (220, 180, 50))
    surface.blit(titel, (SW // 2 - titel.get_width() // 2, 60))

    pygame.draw.line(surface, (80, 70, 30),
                     (SW // 2 - 200, 120), (SW // 2 + 200, 120), 2)

    eintraege = load_highscores()

    hx = SW // 2 - 250
    hy = 140
    for text, ox in [("Platz", 0), ("Name", 80), ("Zeit", 240), ("Datum", 360)]:
        col_txt = fnt_kopf.render(text, True, (160, 160, 200))
        surface.blit(col_txt, (hx + ox, hy))

    medaillen = [
        (255, 215,  50),
        (192, 192, 192),
        (180, 100,  50),
    ]

    if not eintraege:
        leer = fnt_eing.render("Noch keine Einträge vorhanden...", True, (120, 120, 140))
        surface.blit(leer, (SW // 2 - leer.get_width() // 2, 200))
    else:
        for i, e in enumerate(eintraege[:10]):
            ey  = hy + 28 + i * 24
            col = medaillen[i] if i < 3 else (180, 180, 200)

            if i % 2 == 0:
                zebra = pygame.Surface((510, 22), pygame.SRCALPHA)
                zebra.fill((255, 255, 255, 12))
                surface.blit(zebra, (hx - 5, ey - 2))

            mins  = int(e["time"] // 60)
            seks  = int(e["time"] % 60)
            mseks = int((e["time"] % 1) * 100)
            zeit  = f"{mins:02d}:{seks:02d}.{mseks:02d}"

            surface.blit(fnt_eing.render(f"#{i+1:2d}",   True, col),           (hx,       ey))
            surface.blit(fnt_eing.render(e["name"],       True, col),           (hx + 80,  ey))
            surface.blit(fnt_eing.render(zeit,            True, col),           (hx + 240, ey))
            surface.blit(fnt_eing.render(e["date"],       True, (140, 140, 160)), (hx + 360, ey))

    hinweis = fnt_klein.render("ESC – Zurück zum Menü", True, (100, 100, 120))
    surface.blit(hinweis, (SW // 2 - hinweis.get_width() // 2, SH - 40))
