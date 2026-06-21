"""
Nightwatch – Sprite-Generierung mit Pillow.
Erstellt monster_sheet.png und player_sheet.png im assets/-Ordner.
Wird beim ersten Start automatisch ausgeführt wenn die Dateien fehlen.

Autoren: Onur Gündüz, Fabi
Schuljahr: 2025/26
"""

import math
import os
import sys

try:
    from PIL import Image, ImageDraw, ImageFilter
    PIL_OK = True
except ImportError:
    PIL_OK = False

MONSTER_B      = 80
MONSTER_H      = 110
MONSTER_FRAMES = 6
MONSTER_STATES = ["patrol", "alert", "hunt"]

SPIELER_B      = 38
SPIELER_H      = 38
SPIELER_FRAMES = 4

ASSETS_PFAD = os.path.join(os.path.dirname(__file__), "..", "assets")


def _glow(img: "Image.Image", cx: int, cy: int,
          radius: int, farbe: tuple, staerke: float = 3.0) -> None:
    """Zeichnet einen weichen Leuchtkreis auf das PIL-Bild."""
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    r, g, b = farbe
    for i in range(radius + int(staerke * 4), 0, -1):
        alpha = int(200 * (1 - i / (radius + staerke * 4)) ** 1.2)
        d.ellipse((cx - i, cy - i, cx + i, cy + i), fill=(r, g, b, alpha))
    unscharf = overlay.filter(ImageFilter.GaussianBlur(radius=staerke))
    img.alpha_composite(unscharf)

    d2 = ImageDraw.Draw(img)
    d2.ellipse((cx - radius, cy - radius, cx + radius, cy + radius),
               fill=(r, g, b, 255))
    kr = max(1, radius // 3)
    d2.ellipse((cx - kr, cy - kr, cx + kr, cy + kr), fill=(5, 0, 0, 255))


def _monster_frame(frame: int, zustand: str) -> "Image.Image":
    """Erstellt einen einzelnen Monster-Frame für den angegebenen Zustand."""
    img = Image.new("RGBA", (MONSTER_B, MONSTER_H), (0, 0, 0, 0))
    d   = ImageDraw.Draw(img)

    cx   = MONSTER_B // 2
    wipp = math.sin(frame / MONSTER_FRAMES * 2 * math.pi) * 2.5
    t    = frame / MONSTER_FRAMES

    if zustand == "patrol":
        koerper_f = (16, 9, 24)
        akzent_f  = (25, 12, 32)
        auge_f    = (210, 30, 15)
        arm_f     = (12, 7, 18)
    elif zustand == "alert":
        koerper_f = (34, 14, 10)
        akzent_f  = (48, 20, 8)
        auge_f    = (240, 130, 15)
        arm_f     = (26, 10, 8)
    else:
        koerper_f = (55, 8, 8)
        akzent_f  = (75, 10, 5)
        auge_f    = (255, 50, 10)
        arm_f     = (42, 6, 6)

    schatten = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(schatten)
    sd.ellipse((cx - 22, MONSTER_H - 16, cx + 22, MONSTER_H - 2), fill=(0, 0, 0, 60))
    schatten = schatten.filter(ImageFilter.GaussianBlur(radius=4))
    img.alpha_composite(schatten)
    d = ImageDraw.Draw(img)

    bein_phase = math.sin(t * 2 * math.pi)
    for v in (-1, 1):
        lx   = cx + v * 11
        step = int(bein_phase * 9 * v)
        d.line([(lx, 78), (lx + step // 2, 94)], fill=(*koerper_f, 220), width=9)
        d.line([(lx + step // 2, 94), (lx + step, MONSTER_H - 4)],
               fill=(*arm_f, 200), width=6)
        fx = lx + step
        d.ellipse((fx - 9, MONSTER_H - 8, fx + 9, MONSTER_H - 1), fill=(*arm_f, 180))

    d.ellipse((cx - 16, 36, cx + 16, 78), fill=(*koerper_f, 235))
    d.ellipse((cx - 20, 26, cx + 20, 55), fill=(*akzent_f,  230))

    for ri in range(4):
        ry = 42 + ri * 8
        d.arc((cx - 13, ry - 5, cx + 13, ry + 5), -160, -20,
              fill=(*arm_f, 100), width=1)

    arm_schw = math.sin(t * 2 * math.pi) * 18
    for v in (-1, 1):
        ax = cx + v * 20
        ay = 38
        if zustand == "hunt":
            end_x = ax + v * 22 + int(arm_schw * v * 0.3)
            end_y = 88
        else:
            end_x = ax + v * 12 + int(arm_schw * v * 0.5)
            end_y = 93
        mid_x = (ax * 2 + end_x) // 3
        mid_y = 64
        d.line([(ax, ay), (mid_x, mid_y)], fill=(*arm_f, 220), width=8)
        d.line([(mid_x, mid_y), (end_x, end_y)], fill=(*arm_f, 200), width=6)
        for fi in range(4):
            fa   = math.radians(-30 + fi * 20 + v * 12)
            flen = 14 if fi == 1 else 11
            fx   = int(end_x + math.cos(fa) * flen)
            fy   = int(end_y + math.sin(fa) * flen)
            d.line([(end_x, end_y), (fx, fy)], fill=(*arm_f, 180), width=2)

    d.rectangle((cx - 5, 18, cx + 5, 30), fill=(*koerper_f, 220))

    kopf_y = int(15 + wipp)
    d.ellipse((cx - 15, kopf_y - 16, cx + 15, kopf_y + 16), fill=(*koerper_f, 240))
    d.ellipse((cx - 10, kopf_y - 22, cx + 10, kopf_y - 6),  fill=(*koerper_f, 230))

    for v in (-1, 1):
        ex = cx + v * 6
        ey = kopf_y - 3
        _glow(img, ex, ey, 4, auge_f, staerke=4.5)

    d = ImageDraw.Draw(img)

    if zustand in ("hunt", "alert"):
        mund_y = kopf_y + 8
        d.arc((cx - 11, mund_y - 3, cx + 11, mund_y + 7),
              10, 170, fill=(100, 5, 5, 200), width=2)
        if zustand == "hunt":
            for ti in range(5):
                tx  = cx - 9 + ti * 5
                pts = [(tx, mund_y + 1), (tx + 3, mund_y + 1),
                       (tx + 1, mund_y + 6)]
                d.polygon(pts, fill=(220, 210, 192, 230))

    if zustand == "hunt":
        aura = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ad   = ImageDraw.Draw(aura)
        pr   = 32 + int(math.sin(t * math.pi * 2) * 4)
        ad.ellipse((cx - pr, MONSTER_H // 2 - pr,
                    cx + pr, MONSTER_H // 2 + pr),
                   fill=(130, 0, 0, 35))
        aura  = aura.filter(ImageFilter.GaussianBlur(radius=8))
        basis = img.copy()
        basis.alpha_composite(aura)
        img.paste(basis)

    return img


def _spieler_frame(frame: int, bewegt: bool) -> "Image.Image":
    """Erstellt einen einzelnen Spieler-Frame."""
    img = Image.new("RGBA", (SPIELER_B, SPIELER_H), (0, 0, 0, 0))
    d   = ImageDraw.Draw(img)

    cx  = SPIELER_B // 2
    cy  = SPIELER_H // 2
    t   = frame / SPIELER_FRAMES if bewegt else 0
    bob = int(math.sin(t * 2 * math.pi) * 1.5) if bewegt else 0

    schatten = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(schatten)
    sd.ellipse((cx - 10, cy + 10, cx + 10, cy + 16), fill=(0, 0, 0, 50))
    schatten = schatten.filter(ImageFilter.GaussianBlur(radius=3))
    img.alpha_composite(schatten)
    d = ImageDraw.Draw(img)

    bein_schw = math.sin(t * 2 * math.pi) * 6 if bewegt else 0
    for v in (-1, 1):
        lx  = cx + v * 5
        ly  = cy + 5 + bob
        ldx = int(bein_schw * v)
        d.line([(lx, ly), (lx + ldx, ly + 10)], fill=(30, 28, 42, 230), width=5)
        d.ellipse((lx + ldx - 5, ly + 8, lx + ldx + 5, ly + 13),
                  fill=(20, 18, 30, 210))

    d.ellipse((cx - 10, cy - 6 + bob, cx + 10, cy + 8 + bob), fill=(38, 33, 50, 240))
    d.line([(cx, cy - 4 + bob), (cx, cy + 6 + bob)], fill=(25, 22, 36, 150), width=1)

    arm_schw = math.sin(t * 2 * math.pi) * 5 if bewegt else 0
    for v in (-1, 1):
        ax  = cx + v * 10
        ay  = cy - 1 + bob
        adx = int(arm_schw * v)
        d.line([(ax, ay), (ax + v * 2 + adx, ay + 8)],
               fill=(33, 28, 44, 230), width=4)

    d.ellipse((cx - 7, cy - 14 + bob, cx + 7, cy - 2 + bob),  fill=(195, 165, 135, 255))
    d.ellipse((cx - 7, cy - 17 + bob, cx + 7, cy - 10 + bob), fill=(55, 38, 26, 255))
    d.ellipse((cx + 4, cy -  9 + bob, cx + 8, cy -  6 + bob), fill=(220, 210, 180, 160))

    return img


def build_monster_sheet() -> "Image.Image":
    """
    Erstellt das Monster-Sprite-Sheet.
    Layout: Zeilen = Zustände (patrol/alert/hunt), Spalten = Frames.
    """
    sheet_b = MONSTER_B * MONSTER_FRAMES
    sheet_h = MONSTER_H * len(MONSTER_STATES)
    sheet   = Image.new("RGBA", (sheet_b, sheet_h), (0, 0, 0, 0))

    for si, zustand in enumerate(MONSTER_STATES):
        for fi in range(MONSTER_FRAMES):
            frame_img = _monster_frame(fi, zustand)
            sheet.paste(frame_img, (fi * MONSTER_B, si * MONSTER_H), frame_img)

    return sheet


def build_player_sheet() -> "Image.Image":
    """
    Erstellt das Spieler-Sprite-Sheet.
    Layout: Lauf-Frames | Idle-Frame (letzte Spalte).
    """
    sheet_b = SPIELER_B * (SPIELER_FRAMES + 1)
    sheet   = Image.new("RGBA", (sheet_b, SPIELER_H), (0, 0, 0, 0))

    for fi in range(SPIELER_FRAMES):
        frame_img = _spieler_frame(fi, True)
        sheet.paste(frame_img, (fi * SPIELER_B, 0), frame_img)

    idle = _spieler_frame(0, False)
    sheet.paste(idle, (SPIELER_FRAMES * SPIELER_B, 0), idle)

    return sheet


def generate(force: bool = False) -> bool:
    """
    Generiert alle Sprites wenn noch nicht vorhanden.
    Gibt True zurück wenn erfolgreich (Pillow verfügbar).
    """
    if not PIL_OK:
        return False

    os.makedirs(ASSETS_PFAD, exist_ok=True)

    monster_pfad = os.path.join(ASSETS_PFAD, "monster_sheet.png")
    spieler_pfad = os.path.join(ASSETS_PFAD, "player_sheet.png")

    try:
        if force or not os.path.exists(monster_pfad):
            sheet = build_monster_sheet()
            sheet.save(monster_pfad)

        if force or not os.path.exists(spieler_pfad):
            sheet = build_player_sheet()
            sheet.save(spieler_pfad)

        return True

    except Exception as e:
        print(f"[gen_sprites] Fehler beim Erstellen: {e}", file=sys.stderr)
        return False


if __name__ == "__main__":
    ok = generate(force=True)
    print("Sprites erfolgreich generiert."
          if ok
          else "Pillow nicht verfügbar – pygame.draw-Fallback wird genutzt.")
