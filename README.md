# NIGHTWATCH – Horror Escape Game

**Entwickler:** Onur Gündüz & Fabian Bechter  
**Schule:** HTL Rankweil | Klasse 1AHIF | Schuljahr 2025/26  
**Fach:** Programmieren und Objektorientierung (POS)  

---

## Spielbeschreibung

Nightwatch ist ein 2D-Horror-Escape-Game (Top-Down), entwickelt in Python mit pygame.  
Der Spieler erwacht in einem dunklen Haus, muss 5 Aufgaben in verschiedenen Räumen erfüllen,  
5 Schlüssel einsammeln und durch den Eingangsbereich fliehen – während ein Monster patrouilliert.

---

## Starten

```bash
# Abhängigkeiten installieren
pip install -r requirements.txt

# Spiel starten
cd src
python main.py
```

Das Spiel startet automatisch im Vollbild. Mit **F11** kann zwischen Vollbild und Fenster gewechselt werden.

---

## Steuerung

| Taste | Aktion |
|---|---|
| W / A / S / D oder Pfeiltasten | Bewegen |
| Maus | Taschenlampe ausrichten |
| F | Taschenlampe ein/aus |
| SPACE | Dash (betäubt Monster, 60s Cooldown) |
| SHIFT | Schleichen |
| E | Interagieren / Tür öffnen |
| P / ESC | Pause |
| F11 | Vollbild umschalten |

---

## Abhängigkeiten

| Paket                | Version | Verwendung                                         |
|----------------------|---|----------------------------------------------------|
| pygame               | 2.6.1 | Game-Framework (Fenster, Events, Zeichnen, Sound)  |
| pygame.draw & Pillow | 10.0.0 | Erstellung von Level Grafiken                      |
| numpy                | >=1.26.0 | Film-Grain-Effekt (Beleuchtung), Sound-Generierung |

---

## Herkunft der Inhalte

### Selbst entwickelt (Onur Gündüz & Fabian Bechter)

- Gesamte Spiellogik (main.py, player.py, monster.py, items.py, level.py, hud.py, jumpscare.py, sounds.py, highscore.py, config.py, game_variables.py)
- **Sprite-Generierung** – Alle Level-Grafiken also Assets wie Boden, Wände wurden gezeichnet mit pygame.draw und Pillow, keine externen Grafiken
- **Sound-Generierung** (`sounds.py`) – alle Sounds synthetisch via NumPy + wave generiert, keine externen Audio-Dateien
- Levelaufbau mit 6 Haupträumen und 6 Verbindungsgängen
- Alle 5 Aufgaben (Kerzen, Schalter, Kiste, Memory, Code)
- Beleuchtungssystem (Taschenlampen-Lichtkegel, Kerzenlicht, Vignette)
- Kamera-System mit automatischem Zoom (ZoomCamera)
- BFS-Navigationsgraph für Monster-Wegfindung
- Highscore-System

### KI-generierte Hintergrundbilder (ChatGPT Image / DALL-E)

- `assets/menu_bg.png` – Hintergrundbild des Hauptmenüs  
  *(Pixel-Art Stil: dunkler Raum mit Monster in der Tür, Mondlicht, Laterne)*
- `assets/pause_bg.png` – Hintergrundbild des Pause-Menüs  
  *(Gleiche Szene mit "PAUSE"-Schriftzug)*

Diese Bilder wurden mit ChatGPT Image (DALL-E) generiert und dienen ausschließlich als Menü-Hintergründe.  
Die gesamte Spielgrafik während des Spiels ist prozedural (durch Code) erzeugt.

### KI-unterstützter Code (Claude Opus 4.8 / Claude Sonnet 4.6)

Im Code sind alle KI-generierten Abschnitte mit folgendem Format markiert:

```python
# KI CODE ANFANG
# Claude Opus 4.8
# Prompt: "..."
[Code]
# KI CODE ENDE
```

**Markierte Stellen (7 insgesamt):**

1. `main.py` – `ZoomCamera` Klasse (Lerp-Zoom-Kamerasystem)
2. `monster.py` – `Monster._bewege()` Methode (Bewegung mit Wandkollision + BFS)
3. `lighting.py` – `Lighting._filmkorn_erstellen()` (Film-Grain via NumPy)
4. `lighting.py` – `Lighting._lichtkegel_zeichnen()` (Taschenlampen-Lichtkegel-Polygon)
5. `utils.py` – `bfs_path()` + `next_waypoint()` (BFS-Wegfindung)

---

## Projektstruktur

```
nightwatch-abgabe/
├── requirements.txt          # Python-Abhängigkeiten
├── README.md                 # Diese Datei
├── src/
│   ├── main.py               # Spielschleife, Menüs, Kamera
│   ├── assets/
│   │   ├── menu_bg.png       # Hauptmenü-Hintergrund (ChatGPT)
│   │   ├── pause_bg.png      # Pause-Hintergrund (ChatGPT)
│   │   ├── monster_sheet.png # Monster-Sprites (selbst, generiert)
│   │   └── player_sheet.png  # Spieler-Sprites (selbst, generiert)
│   ├── game/
│   │   ├── config.py         # Einstellungen (JSON)
│   │   ├── gen_sprites.py    # Sprite-Generierung mit Pillow (selbst)
│   │   ├── highscore.py      # Highscore-Verwaltung
│   │   ├── hud.py            # HUD-Anzeige
│   │   ├── items.py          # Alle 5 Aufgaben + Schlüssel
│   │   ├── jumpscare.py      # Jumpscare-Effekte
│   │   ├── level.py          # Räume, Gänge, Türen
│   │   ├── lighting.py       # Beleuchtungssystem
│   │   ├── monster.py        # Monster-KI (3 Zustände + BFS)
│   │   ├── player.py         # Spieler-Logik
│   │   ├── sounds.py         # Sound-Generierung (NumPy)
│   │   ├── sprites.py        # Sprite-Klassen
│   │   └── utils.py          # Mathematik + BFS-Wegfindung
│   └── game_variables/
│       └── game_variables.py # Zentrale Spielkonstanten
└── doc/
    └── Nightwatch_Dokumentation.pdf
```

---

## HTL Rankweil | POS | 2025/26
