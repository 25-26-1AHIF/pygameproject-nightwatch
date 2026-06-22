import math
import pygame
from game_variables.game_variables import GameVariables

SW  = GameVariables.SCREEN_W
SH  = GameVariables.SCREEN_H
DC  = GameVariables.DASH_COOLDOWN
AK  = GameVariables.AKKU_FARBE
SK  = GameVariables.SCHLUESSEL_FARBE
ANZ = GameVariables.SCHLUESSEL_ANZAHL


def draw_battery(surface: pygame.Surface, battery: float) -> None:
    # akkuanzeige unten rechts zeichnen
    bw = 120
    bh = 14
    bx = SW - bw - 20
    by = SH - bh - 16

    hg = pygame.Surface((bw + 24, bh + 20), pygame.SRCALPHA)
    hg.fill((10, 10, 20, 160))
    surface.blit(hg, (bx - 8, by - 8))

    pygame.draw.rect(surface, (60, 60, 70), (bx, by, bw, bh), border_radius=3)
    pygame.draw.rect(surface, (60, 60, 70), (bx + bw, by + 3, 6, bh - 6), border_radius=2)

    fuellung = max(0.0, battery / GameVariables.LAMPE_AKKU_MAX)
    fuell_w  = int((bw - 4) * fuellung)

    if fuellung > 0.5:
        farbe = AK
    elif fuellung > 0.2:
        farbe = (220, 200, 50)
    else:
        farbe = (220, 50, 50)

    if fuell_w > 0:
        pygame.draw.rect(surface, farbe, (bx + 2, by + 2, fuell_w, bh - 4), border_radius=2)

    pygame.draw.rect(surface, (120, 120, 140), (bx, by, bw, bh), 2, border_radius=3)

    font = pygame.font.SysFont("monospace", 11)
    text = font.render(f"Lampe {int(battery)}%", True, (180, 180, 200))
    surface.blit(text, (bx, by - 14))


def draw_keys(surface: pygame.Surface, gesammelt: int) -> None:
    # gesammelte schluessel oben links anzeigen
    font = pygame.font.SysFont("monospace", 12)
    beschr = font.render("Schluessel:", True, (180, 180, 200))
    surface.blit(beschr, (16, 38))

    for i in range(ANZ):
        kx = 16 + i * 26
        ky = 55
        if i < gesammelt:
            pygame.draw.circle(surface, SK, (kx + 10, ky + 8), 9)
            pygame.draw.circle(surface, (200, 160, 20), (kx + 10, ky + 8), 9, 2)
            pygame.draw.rect(surface, SK, (kx + 16, ky + 5, 8, 3))
            pygame.draw.rect(surface, SK, (kx + 20, ky + 5, 2, 5))
        else:
            pygame.draw.circle(surface, (50, 50, 60), (kx + 10, ky + 8), 9)
            pygame.draw.circle(surface, (70, 70, 80), (kx + 10, ky + 8), 9, 1)


def draw_task_list(surface: pygame.Surface, tasks_done: list[bool]) -> None:
    # mini-aufgabenliste oben rechts zeichnen
    aufgaben = [
        "R1: Kerzen anzuenden",
        "R2: Schalter umlegen",
        "R3: Kiste tragen",
        "R4: Memory-Puzzle",
        "R5: Zahlenkombination",
    ]

    font    = pygame.font.SysFont("monospace", 12)
    panel_w = 210
    panel_h = len(aufgaben) * 18 + 28
    px      = SW - panel_w - 12
    py      = 40

    bg = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    bg.fill((10, 10, 20, 170))
    surface.blit(bg, (px, py))
    pygame.draw.rect(surface, (60, 60, 80), (px, py, panel_w, panel_h), 1)

    titel = font.render("Aufgaben:", True, (200, 200, 230))
    surface.blit(titel, (px + 8, py + 6))

    for i, (name, fertig) in enumerate(zip(aufgaben, tasks_done)):
        ty   = py + 26 + i * 18
        sym  = "[x]" if fertig else "[ ]"
        col  = (80, 200, 100) if fertig else (180, 180, 200)
        zeile = font.render(f"{sym} {name}", True, col)
        surface.blit(zeile, (px + 8, ty))


def draw_pulse(surface: pygame.Surface, intensity: float) -> None:
    # rote vignette wenn das monster nah ist
    if intensity <= 0:
        return

    t    = pygame.time.get_ticks() / 300
    puls = abs(math.sin(t * math.pi)) * intensity

    vig  = pygame.Surface((SW, SH), pygame.SRCALPHA)
    rand = int(120 + 30 * puls)
    a    = int(90 * puls)

    for i in range(0, rand, 12):
        ia = int(a * (1 - i / rand) ** 1.5)
        if ia > 0:
            pygame.draw.rect(vig, (200, 0, 0, ia), (i, i, SW - 2*i, SH - 2*i), 12)
    surface.blit(vig, (0, 0))


def draw_dash_hud(surface: pygame.Surface, cooldown_frames: int, is_dashing: bool) -> None:
    # dash-cooldown als kreisbogen unten links anzeigen
    cx = 56
    cy = SH - 56
    r  = 28

    bereit   = cooldown_frames <= 0
    fortschr = 1.0 - (cooldown_frames / DC) if not bereit else 1.0

    bg = pygame.Surface((r * 2 + 20, r * 2 + 20), pygame.SRCALPHA)
    pygame.draw.circle(bg, (10, 8, 14, 180), (r + 10, r + 10), r + 8)
    surface.blit(bg, (cx - r - 10, cy - r - 10))

    bogen_farbe = (60, 200, 255) if bereit else (120, 80, 160)
    if is_dashing:
        bogen_farbe = (200, 240, 255)

    if fortschr > 0:
        start_a  = -math.pi / 2
        schritte = 48
        punkte   = []
        for i in range(int(schritte * fortschr) + 1):
            a  = start_a + i / schritte * 2 * math.pi
            px = cx + int(math.cos(a) * r)
            py = cy + int(math.sin(a) * r)
            punkte.append((px, py))
        if len(punkte) > 1:
            pygame.draw.lines(surface, bogen_farbe, False, punkte, 4)

    inner_farbe = (50, 160, 220) if bereit else (50, 40, 70)
    pygame.draw.circle(surface, inner_farbe, (cx, cy), r - 6)

    blitz_punkte = [
        (cx + 4,  cy - 12), (cx - 2,  cy - 2),  (cx + 3,  cy - 2),
        (cx - 4,  cy + 12), (cx + 2,  cy + 2),  (cx - 3,  cy + 2),
    ]
    blitz_farbe = (220, 240, 255) if bereit else (80, 70, 100)
    pygame.draw.polygon(surface, blitz_farbe, blitz_punkte)

    font = pygame.font.SysFont("monospace", 11)
    if bereit:
        beschr = font.render("DASH", True, (80, 200, 255))
        surface.blit(beschr, (cx - beschr.get_width() // 2, cy + r + 6))
    else:
        sek_rest = math.ceil(cooldown_frames / 120)
        beschr   = font.render(f"{sek_rest}s", True, (100, 80, 120))
        surface.blit(beschr, (cx - beschr.get_width() // 2, cy + r + 6))

    if bereit and not is_dashing:
        hinweis = font.render("[SPACE]", True, (50, 120, 160))
        surface.blit(hinweis, (cx - hinweis.get_width() // 2, cy + r + 18))


def draw_caught_overlay(surface: pygame.Surface, alpha: int = 180) -> None:
    # rotes overlay wenn der spieler gefangen wird
    overlay = pygame.Surface((SW, SH))
    overlay.fill((120, 0, 0))
    overlay.set_alpha(alpha)
    surface.blit(overlay, (0, 0))


def draw_hint_bar(surface: pygame.Surface, text: str, duration_ratio: float) -> None:
    # hinweistext am unteren bildschirmrand anzeigen
    alpha = int(255 * min(1.0, duration_ratio * 5))
    if alpha <= 0:
        return

    font = pygame.font.SysFont("monospace", 14)
    txt  = font.render(text, True, (255, 255, 255))
    bw   = txt.get_width() + 24
    bh   = 28
    bx   = SW // 2 - bw // 2
    by   = SH - 60

    bg = pygame.Surface((bw, bh), pygame.SRCALPHA)
    bg.fill((10, 10, 20, 180))
    bg.set_alpha(alpha)
    surface.blit(bg, (bx, by))
    txt.set_alpha(alpha)
    surface.blit(txt, (bx + 12, by + 6))


def draw_hud(surface: pygame.Surface,
             battery: float,
             keys_collected: int,
             tasks_done: list[bool],
             pulse_intensity: float,
             hint_text: str = "",
             hint_ratio: float = 0.0,
             dash_cooldown: int = 0,
             is_dashing: bool = False) -> None:
    # komplettes hud in einem aufruf zeichnen
    draw_pulse(surface, pulse_intensity)
    draw_battery(surface, battery)
    draw_keys(surface, keys_collected)
    draw_task_list(surface, tasks_done)
    draw_dash_hud(surface, dash_cooldown, is_dashing)

    if hint_text and hint_ratio > 0:
        draw_hint_bar(surface, hint_text, hint_ratio)
