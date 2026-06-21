import pygame


class GameVariables:
    """Zentrale Spielkonstanten für Nightwatch."""

    # Fenster & Timing
    SCREEN_W = 1280
    SCREEN_H = 720
    FPS = 120
    TITEL = "Nightwatch"

    # Spielwelt
    WORLD_W = 2400
    WORLD_H = 1100

    # Farben
    SCHWARZ    = (0,   0,   0)
    WEISS      = (255, 255, 255)
    ROT        = (200,  40,  40)
    GRUEN      = (40,  180,  80)
    GRAU       = (90,   90,  90)
    DUNKELGRAU = (40,   40,  40)

    # Bodenfarben
    PARKETT_FARBE = (100, 70,  40)
    TEPPICH_FARBE = (70,  60,  90)
    FLIESEN_FARBE = (110, 110, 130)
    WAND_FARBE    = (30,  30,  45)

    # Spieler
    SPIELER_GESCHWINDIGKEIT      = 3.0
    SPIELER_SCHLEICH_GESCHW      = 1.6
    SPIELER_RADIUS               = 14

    # Taschenlampe
    LAMPE_LAENGE   = 280
    LAMPE_WINKEL   = 38.0
    LAMPE_AKKU_MAX = 100.0
    LAMPE_VERBRAUCH = 0.015
    LAMPE_AUFLADEN  = 0.018

    # Monster
    MONSTER_RADIUS = 16
    MONSTER_SICHT  = 340
    MONSTER_DUNKEL = 90
    MONSTER_HOER   = 180
    MONSTER_HOER_PARKETT  = 240
    MONSTER_HOER_FLIESEN  = 200
    MONSTER_HOER_TEPPICH  = 80

    ALERT_DAUER    = 300
    JAGD_VERLIER_DIST = 420

    # Dash
    DASH_GESCHWINDIGKEIT = 9.0
    DASH_DAUER           = 18
    DASH_COOLDOWN        = 7200
    DASH_STUN_BEREICH    = 130
    DASH_STUN_DAUER      = 210

    # Aufgaben & Schlüssel
    SCHLUESSEL_ANZAHL    = 5
    SCHLUESSEL_FARBE     = (240, 200, 50)
    SCHLUESSEL_RADIUS    = 8
    KERZEN_ANZAHL        = 5
    SCHALTER_ANZAHL      = 3
    KOMBINATION          = (2, 4, 1)
    MEMORY_GROESSE       = 4

    # Jumpscares
    JUMPSCARE_DAUER = 45
    BLITZ_DAUER     = 12
    SHAKE_AMPLITUDE = 18
    SHAKE_DAUER     = 60

    # Bodentypen
    BODEN_PARKETT = "parquet"
    BODEN_TEPPICH = "carpet"
    BODEN_FLIESEN = "tile"

    # HUD
    HUD_HINTERGRUND  = (10, 10, 20, 180)
    AKKU_FARBE       = (60, 220, 120)
    PULS_FARBE       = (220, 60, 60)

    # Schwierigkeitsgrade
    SCHWIERIGKEITEN = {
        "Sehr Einfach": {
            "patrol": 0.2, "alert": 0.3, "hunt": 0.45,
            "sight": 80,   "hear_factor": 0.2,
            "label": "SEHR EINFACH",
            "desc":  "Monster extrem lahm. Weglaufen immer möglich.",
            "color": (40, 200, 120),
        },
        "Einfach": {
            "patrol": 0.6, "alert": 0.9, "hunt": 1.5,
            "sight": 200,  "hear_factor": 0.55,
            "label": "EINFACH",
            "desc":  "Monster träge & fast blind. Wegrennen möglich.",
            "color": (60, 180, 80),
        },
        "Normal": {
            "patrol": 1.2, "alert": 1.8, "hunt": 3.4,
            "sight": 340,  "hear_factor": 1.0,
            "label": "NORMAL",
            "desc":  "Ausgewogene Herausforderung.",
            "color": (200, 160, 40),
        },
        "Schwer": {
            "patrol": 1.8, "alert": 2.6, "hunt": 4.6,
            "sight": 440,  "hear_factor": 1.4,
            "label": "SCHWER",
            "desc":  "Sehr schnell, hört alles. Viel Glück.",
            "color": (200, 30, 30),
        },
    }

    # BFS-Navigationsgraph
    NAV_NODES = {
        0:  (340,  250),
        1:  (630,  250),
        2:  (920,  250),
        3:  (1210, 250),
        4:  (1500, 250),
        5:  (1790, 250),
        6:  (2080, 250),
        7:  (340,  550),
        13: (2080, 550),
        8:  (340,  850),
        9:  (630,  850),
        10: (950,  850),
        11: (1500, 850),
        12: (2080, 850),
    }

    NAV_EDGES = [
        (0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6),
        (0, 7), (7, 8),
        (8, 9), (9, 10), (10, 11), (11, 12), (12, 13), (13, 6),
    ]

    # Anzeigeauflösungen
    AUFLÖSUNGEN = {
        "720p":  (1280,  720),
        "1080p": (1920, 1080),
        "1440p": (2560, 1440),
        "4K":    (3840, 2160),
    }

    QUALITAETS_STUFEN = ["Niedrig", "Mittel", "Hoch", "Extreme"]

    # Schriftarten – werden in init() gesetzt
    FONT_GROSS  = None
    FONT_MITTEL = None
    FONT_KLEIN  = None

    @staticmethod
    def init():
        """Initialisiert pygame und setzt die Schriftarten."""
        pygame.init()
        pygame.font.init()  # auf python 3.14 manchmal nötig wegen circular import bug
        GameVariables.FONT_GROSS  = pygame.font.SysFont("monospace", 48, bold=True)
        GameVariables.FONT_MITTEL = pygame.font.SysFont("monospace", 24, bold=True)
        GameVariables.FONT_KLEIN  = pygame.font.SysFont("monospace", 14)


class GameScreens:
    """Alle möglichen Spielbildschirme / Zustände."""
    MENU        = "menu"
    DIFFICULTY  = "difficulty"
    PLAYING     = "playing"
    PAUSED      = "paused"
    CAUGHT      = "caught"
    WIN         = "win"
    NAME_INPUT  = "name_input"
    HIGHSCORE   = "highscore"
    EXIT        = "exit"

    aktuell = MENU
