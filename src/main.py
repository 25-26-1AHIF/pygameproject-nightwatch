import math
import os
import sys
import random
import pygame
from enum import Enum, auto

# src/ muss im Suchpfad liegen damit alle Untermodule gefunden werden
sys.path.insert(0, os.path.dirname(__file__))

from game_variables.game_variables import GameVariables, GameScreens
from game import config as _cfg
from game.level import PLAYER_START, MONSTER_START, draw as draw_level, get_room_at
from game.player import Player
from game.monster import Monster, MonsterState
from game.items import ItemManager
from game.lighting import Lighting
from game.hud import draw_hud, draw_caught_overlay
from game.jumpscare import JumpscareManager, JumpscareEffect
from game.highscore import draw_highscore_screen, save_highscore
from game.sounds import SoundManager
from game.utils import dist, clamp
from game.sprites import draw_blood_splatter

GV = GameVariables


class GameState(Enum):
    # alle bildschirmzustände - der hauptloop wechselt zwischen diesen
    MENU        = auto()
    DIFFICULTY  = auto()
    PLAYING     = auto()
    PAUSED      = auto()
    CAUGHT      = auto()
    WIN         = auto()
    NAME_INPUT  = auto()
    HIGHSCORE   = auto()


# KI CODE ANFANG
# Claude Opus 4.8
# Prompt: "Implementiere eine ZoomCamera-Klasse für ein pygame-Spiel die sanft in
# den aktuellen Raum hineinzoomt. Berechne den Ziel-Zoom aus Raumgröße / Fenstergröße.
# Benutze lineares Lerp (ZOOM_LERP=0.045) für smooth transitions. Beschränke den
# Zoom auf ZOOM_MIN=0.65 und ZOOM_MAX=1.80. Berechne cam_x/cam_y zentriert um den
# Raummittelpunkt. Stelle view_size als Property zur Verfügung."
class ZoomCamera:
    """Kamera mit sanftem Lerp-Zoom: passt sich an den aktuellen Raum an."""

    ZOOM_MIN   = 0.65
    ZOOM_MAX   = 1.80
    ZOOM_LERP  = 0.045
    FILL_RATIO = 0.62

    def __init__(self):
        self._zoom:  float = 1.0
        self._cam_x: int   = 0
        self._cam_y: int   = 0

    def update(self, spieler_x: float, spieler_y: float,
               aktueller_raum) -> None:
        """Aktualisiert Zoom und Kameraposition einmal pro Frame."""
        if aktueller_raum is not None:
            # ENT-Raum ist extrem breit (1640px) → spieler direkt verfolgen
            # statt auf raummitte zu zentrieren, sonst läuft man am bildschirmrand entlang
            if aktueller_raum.name == "Eingangsbereich":
                ziel_zoom = 1.30   # nah an den spieler ranzoomen
                zentrum_x = spieler_x
                zentrum_y = spieler_y
            else:
                rw = aktueller_raum.rect.width
                rh = aktueller_raum.rect.height
                ziel_zoom = (min(GV.SCREEN_W / rw, GV.SCREEN_H / rh) * self.FILL_RATIO)
                ziel_zoom = max(self.ZOOM_MIN, min(self.ZOOM_MAX, ziel_zoom))
                zentrum_x = float(aktueller_raum.rect.centerx)
                zentrum_y = float(aktueller_raum.rect.centery)
        else:
            ziel_zoom = 1.0
            zentrum_x = spieler_x
            zentrum_y = spieler_y

        self._zoom += (ziel_zoom - self._zoom) * self.ZOOM_LERP

        view_b = max(1, int(GV.SCREEN_W / self._zoom))
        view_h = max(1, int(GV.SCREEN_H / self._zoom))

        raw_cam_x = int(zentrum_x - view_b / 2)
        raw_cam_y = int(zentrum_y - view_h / 2)
        self._cam_x = max(0, min(GV.WORLD_W - view_b, raw_cam_x))
        self._cam_y = max(0, min(GV.WORLD_H - view_h, raw_cam_y))

    @property
    def zoom(self) -> float:
        return self._zoom

    @property
    def cam_x(self) -> int:
        return self._cam_x

    @property
    def cam_y(self) -> int:
        return self._cam_y

    @property
    def view_size(self) -> tuple[int, int]:
        """Größe der View-Surface (Breite, Höhe) in Weltpixeln."""
        return (max(1, int(GV.SCREEN_W / self._zoom)),
                max(1, int(GV.SCREEN_H / self._zoom)))
# KI CODE ENDE


class FullscreenManager:
    """kümmert sich um vollbild/fenster-umschalten und auflösungswechsel."""

    def __init__(self):
        self.fullscreen: bool = False
        self._screen: pygame.Surface | None = None
        self._res_key: str = _cfg.get("resolution", "1080p")

    def get_screen(self) -> pygame.Surface:
        # startet immer im vollbild mit pygame.SCALED - skaliert automatisch
        if self._screen is None:
            self.fullscreen = True
            info = pygame.display.Info()
            w = info.current_w if info.current_w > 0 else 1920
            h = info.current_h if info.current_h > 0 else 1080
            self._screen = pygame.display.set_mode(
                (w, h), pygame.FULLSCREEN | pygame.SCALED
            )
        return self._screen

    def apply_resolution(self, res_key: str) -> pygame.Surface:
        # auflösung wechseln ohne neustart
        self._res_key = res_key
        w, h = GV.AUFLÖSUNGEN.get(res_key, (1920, 1080))
        if self.fullscreen:
            self._screen = pygame.display.set_mode(
                (w, h), pygame.FULLSCREEN | pygame.SCALED
            )
        else:
            self._screen = pygame.display.set_mode((w, h), pygame.RESIZABLE)
        return self._screen

    def toggle(self) -> pygame.Surface:
        # F11 drücken = zwischen vollbild und fenster wechseln
        self.fullscreen = not self.fullscreen
        w, h = GV.AUFLÖSUNGEN.get(self._res_key, (1920, 1080))
        if self.fullscreen:
            self._screen = pygame.display.set_mode(
                (0, 0), pygame.FULLSCREEN | pygame.SCALED
            )
        else:
            self._screen = pygame.display.set_mode((w, h), pygame.RESIZABLE)
        return self._screen


# KI CODE ANFANG
# Claude Opus 4.8
# Prompt: "Implementiere ein PauseMenu für ein pygame Horror-Spiel mit 3 Tabs
# (Grafik, Audio, Über Uns). Das Menü soll vollständig per Tastatur (Pfeiltasten,
# 1/2/3/TAB) und Maus bedienbar sein. Audio-Tab: drei Slider mit klickbarer
# Balken-Fläche für Gesamt-, Musik- und SFX-Lautstärke. Grafik-Tab: Auflösung
# und Qualitätsstufe mit Links/Rechts-Buttons. Über-Uns-Tab: statischer Text.
# Jede Einstellungsänderung wird sofort in der config.py gespeichert."
class PauseMenu:
    """Pause-Menü mit 3 Tabs: Grafik, Audio, Über Uns. Maus + Tastatur."""

    TABS = ["1. Grafik", "2. Audio", "3. Über Uns"]

    def __init__(self, sounds, vollbild: bool = True) -> None:
        """lädt aktuelle einstellungen – vollbild-zustand kommt vom fs_manager."""
        self._sounds   = sounds
        self._tab:     int  = 0
        self._zeile:   int  = 0
        self._vollbild: bool = vollbild
        self._master   = _cfg.get("master_vol",  80)
        self._musik    = _cfg.get("music_vol",   55)
        self._sfx      = _cfg.get("sfx_vol",     80)

        self._tab_rects:    list = []
        self._zeilen_rects: list = []
        self._btn_links:    list = []
        self._btn_rechts:   list = []
        self._slider_bars:  list = []
        self._weiter_rect        = None
        self._menu_rect          = None

    def handle_event(self, event: pygame.event.Event):
        """Verarbeitet Tastatureingaben im Pause-Menü."""
        if event.type != pygame.KEYDOWN:
            return None
        k = event.key

        if k in (pygame.K_ESCAPE, pygame.K_p):
            return ("resume", None)

        if   k == pygame.K_1:   self._tab, self._zeile = 0, 0
        elif k == pygame.K_2:   self._tab, self._zeile = 1, 0
        elif k == pygame.K_3:   self._tab, self._zeile = 2, 0
        elif k == pygame.K_TAB:
            self._tab   = (self._tab + 1) % 3
            self._zeile = 0
        elif k == pygame.K_UP:
            self._zeile = max(0, self._zeile - 1)
        elif k == pygame.K_DOWN:
            max_zeile = [1, 2, 0][self._tab]
            self._zeile = min(max_zeile, self._zeile + 1)
        elif k == pygame.K_LEFT:
            return self._wert_aendern(-1)
        elif k == pygame.K_RIGHT:
            return self._wert_aendern(+1)

        return None

    def _wert_aendern(self, delta: int):
        """ändert den aktuell markierten einstellungswert."""
        if self._tab == 0:
            if self._zeile == 0:
                # vollbild umschalten – delta ignorieren, ist immer ein toggle
                self._vollbild = not self._vollbild
                return ("toggle_fullscreen", None)

        elif self._tab == 1:
            schritt = 5
            if self._zeile == 0:
                self._master = max(0, min(100, self._master + delta * schritt))
                _cfg.set_val("master_vol", self._master)
                _cfg.save()
                if self._sounds:
                    self._sounds.apply_volume_settings(self._master, self._musik, self._sfx)
            elif self._zeile == 1:
                self._musik = max(0, min(100, self._musik + delta * schritt))
                _cfg.set_val("music_vol", self._musik)
                _cfg.save()
                if self._sounds:
                    self._sounds.set_music_volume(self._master, self._musik)
            elif self._zeile == 2:
                self._sfx = max(0, min(100, self._sfx + delta * schritt))
                _cfg.set_val("sfx_vol", self._sfx)
                _cfg.save()
                if self._sounds:
                    self._sounds.apply_volume_settings(self._master, self._musik, self._sfx)
        return None

    def draw(self, surface: pygame.Surface) -> None:
        """Zeichnet das Pause-Menü als Overlay auf den Spielbildschirm."""
        sw, sh = surface.get_size()

        ov = pygame.Surface((sw, sh), pygame.SRCALPHA)
        ov.fill((0, 0, 10, 195))
        surface.blit(ov, (0, 0))

        pw, ph = 680, 488
        px = sw // 2 - pw // 2
        py = sh // 2 - ph // 2

        pygame.draw.rect(surface, (10,  6, 16), (px, py, pw, ph), border_radius=14)
        pygame.draw.rect(surface, (70, 22, 32), (px, py, pw, ph), 2, border_radius=14)

        fnt_gr   = pygame.font.SysFont("monospace", 30, bold=True)
        fnt_tab  = pygame.font.SysFont("monospace", 15, bold=True)
        fnt_item = pygame.font.SysFont("monospace", 14)
        fnt_val  = pygame.font.SysFont("monospace", 14, bold=True)
        fnt_sm   = pygame.font.SysFont("monospace", 12)

        titel = fnt_gr.render("PAUSE", True, (190, 50, 60))
        surface.blit(titel, (px + pw // 2 - titel.get_width() // 2, py + 12))

        tab_y = py + 56
        tab_h = 34
        tab_b = pw // 3
        self._tab_rects = []

        for i, beschr in enumerate(self.TABS):
            tx  = px + i * tab_b
            sel = (i == self._tab)
            bg  = (28, 12, 22) if sel else (14,  7, 14)
            brd = (130, 45, 55) if sel else (45, 22, 35)
            pygame.draw.rect(surface, bg,  (tx, tab_y, tab_b, tab_h))
            pygame.draw.rect(surface, brd, (tx, tab_y, tab_b, tab_h), 1)
            farbe = (215, 140, 150) if sel else (80, 55, 68)
            ls = fnt_tab.render(beschr, True, farbe)
            surface.blit(ls, (tx + tab_b // 2 - ls.get_width() // 2,
                               tab_y + tab_h // 2 - ls.get_height() // 2))
            self._tab_rects.append(pygame.Rect(tx, tab_y, tab_b, tab_h))

        inhalt_y = tab_y + tab_h + 10

        if   self._tab == 0: self._grafik_tab(surface, fnt_item, fnt_val, fnt_sm, px, inhalt_y, pw)
        elif self._tab == 1: self._audio_tab(surface, fnt_item, fnt_val, fnt_sm, px, inhalt_y, pw)
        else:                self._ueberuns_tab(surface, fnt_item, fnt_sm, px, inhalt_y, pw)

        btn_y = py + ph - 64
        pygame.draw.line(surface, (45, 18, 28), (px + 20, btn_y - 4), (px + pw - 20, btn_y - 4), 1)

        wt_w, wt_h = 190, 32
        wt_x = px + pw // 2 - wt_w - 8
        wt_y = btn_y + 4
        self._weiter_rect = pygame.Rect(wt_x, wt_y, wt_w, wt_h)
        pygame.draw.rect(surface, (10, 30, 14), self._weiter_rect, border_radius=6)
        pygame.draw.rect(surface, (36, 96, 48), self._weiter_rect, 1, border_radius=6)
        wt_txt = fnt_tab.render("FORTSETZEN", True, (72, 178, 92))
        surface.blit(wt_txt, (wt_x + wt_w // 2 - wt_txt.get_width() // 2,
                               wt_y + wt_h // 2 - wt_txt.get_height() // 2))

        mn_w, mn_h = 190, 32
        mn_x = px + pw // 2 + 8
        mn_y = btn_y + 4
        self._menu_rect = pygame.Rect(mn_x, mn_y, mn_w, mn_h)
        pygame.draw.rect(surface, (28,  8, 12), self._menu_rect, border_radius=6)
        pygame.draw.rect(surface, (88, 26, 36), self._menu_rect, 1, border_radius=6)
        mn_txt = fnt_tab.render("HAUPTMENÜ", True, (150, 55, 65))
        surface.blit(mn_txt, (mn_x + mn_w // 2 - mn_txt.get_width() // 2,
                               mn_y + mn_h // 2 - mn_txt.get_height() // 2))

        hint = fnt_sm.render(
            "ESC/P – Fortsetzen  |  M – Hauptmenü  |  TAB/1/2/3 – Reiter  |  Pfeiltasten",
            True, (45, 32, 42)
        )
        surface.blit(hint, (px + pw // 2 - hint.get_width() // 2, btn_y + 42))

    def _zeile_zeichnen(self, surface, fnt_item, fnt_val, fnt_sm,
                         px, zeile_y, pw, label, wert_str, sel,
                         hinweis="", zeile_h=52):
        """Zeichnet eine Einstellungszeile mit Pfeil-Buttons."""
        bg  = (48, 16, 26) if sel else (18, 10, 20)
        brd = (110, 42, 52) if sel else (0, 0, 0)
        pygame.draw.rect(surface, bg,  (px + 18, zeile_y, pw - 36, zeile_h), border_radius=7)
        if sel:
            pygame.draw.rect(surface, brd, (px + 18, zeile_y, pw - 36, zeile_h), 1, border_radius=7)

        lbl_col = (155, 125, 135) if sel else (95, 75, 88)
        lbl_s   = fnt_item.render(label, True, lbl_col)
        surface.blit(lbl_s, (px + 34, zeile_y + (zeile_h - lbl_s.get_height()) // 2))

        btn_h   = 24
        btn_b   = 24
        btn_y   = zeile_y + (zeile_h - btn_h) // 2
        r_btn_x = px + pw - 50
        l_btn_x = px + pw - 178

        l_farbe = (160, 80, 95) if sel else (55, 30, 42)
        l_bg    = (34, 13, 19) if sel else (16, 8, 13)
        pygame.draw.rect(surface, l_bg, (l_btn_x, btn_y, btn_b, btn_h), border_radius=4)
        if sel:
            pygame.draw.rect(surface, (74, 30, 44), (l_btn_x, btn_y, btn_b, btn_h), 1, border_radius=4)
        la = fnt_item.render("<", True, l_farbe)
        surface.blit(la, (l_btn_x + btn_b // 2 - la.get_width() // 2,
                           btn_y + btn_h // 2 - la.get_height() // 2))

        col_v = (225, 185, 195) if sel else (140, 110, 125)
        val_s = fnt_val.render(wert_str, True, col_v)
        mitte = l_btn_x + btn_b + (r_btn_x - l_btn_x - btn_b) // 2
        surface.blit(val_s, (mitte - val_s.get_width() // 2,
                              zeile_y + (zeile_h - val_s.get_height()) // 2))

        r_farbe = (160, 80, 95) if sel else (55, 30, 42)
        r_bg    = (34, 13, 19) if sel else (16, 8, 13)
        pygame.draw.rect(surface, r_bg, (r_btn_x, btn_y, btn_b, btn_h), border_radius=4)
        if sel:
            pygame.draw.rect(surface, (74, 30, 44), (r_btn_x, btn_y, btn_b, btn_h), 1, border_radius=4)
        ra = fnt_item.render(">", True, r_farbe)
        surface.blit(ra, (r_btn_x + btn_b // 2 - ra.get_width() // 2,
                           btn_y + btn_h // 2 - ra.get_height() // 2))

        if sel and hinweis:
            hs = fnt_sm.render(hinweis, True, (65, 50, 62))
            surface.blit(hs, (px + 34, zeile_y + zeile_h - 16))

        return (pygame.Rect(l_btn_x, btn_y, btn_b, btn_h),
                pygame.Rect(r_btn_x, btn_y, btn_b, btn_h))

    def _grafik_tab(self, surface, fnt_item, fnt_val, fnt_sm, px, cy, pw):
        # nur eine zeile: vollbild an/aus toggle
        self._zeilen_rects = []
        self._btn_links    = []
        self._btn_rechts   = []
        self._slider_bars  = []

        wert_str = "Vollbild" if self._vollbild else "Fenstermodus"
        zy = cy
        self._zeilen_rects.append(pygame.Rect(px + 18, zy, pw - 36, 52))
        lr, rr = self._zeile_zeichnen(surface, fnt_item, fnt_val, fnt_sm,
                                       px, zy, pw, "Anzeigemodus", wert_str,
                                       sel=(0 == self._zeile),
                                       hinweis="< > oder Klick zum Umschalten",
                                       zeile_h=52)
        self._btn_links.append(lr)
        self._btn_rechts.append(rr)

    def _audio_tab(self, surface, fnt_item, fnt_val, fnt_sm, px, cy, pw):
        """Zeichnet den Audio-Reiter mit drei Lautstärke-Schiebereglern."""
        self._zeilen_rects = []
        self._btn_links    = []
        self._btn_rechts   = []
        self._slider_bars  = []

        schieberegler = [
            ("Gesamtlautstärke", self._master),
            ("Musik",             self._musik),
            ("Soundeffekte",      self._sfx),
        ]
        fnt_bar = pygame.font.SysFont("monospace", 12)

        for i, (lbl, wert) in enumerate(schieberegler):
            zy  = cy + i * 76
            sel = (i == self._zeile)
            bg  = (48, 16, 26) if sel else (18, 10, 20)
            brd = (110, 42, 52) if sel else (0, 0, 0)
            pygame.draw.rect(surface, bg,  (px + 18, zy, pw - 36, 64), border_radius=7)
            if sel:
                pygame.draw.rect(surface, brd, (px + 18, zy, pw - 36, 64), 1, border_radius=7)

            self._zeilen_rects.append(pygame.Rect(px + 18, zy, pw - 36, 64))

            lbl_s = fnt_item.render(lbl, True, (155, 125, 135) if sel else (95, 75, 88))
            surface.blit(lbl_s, (px + 34, zy + 8))

            pct_s = fnt_val.render(f"{wert} %", True,
                                   (225, 185, 195) if sel else (140, 110, 125))
            surface.blit(pct_s, (px + pw - 80, zy + 8))

            bx = px + 52
            bw = pw - 160
            by = zy + 36
            bh = 12
            self._slider_bars.append((bx, by, bw, bh))
            pygame.draw.rect(surface, (28, 16, 26), (bx, by, bw, bh), border_radius=5)
            fw = int(bw * wert / 100)
            if fw > 0:
                fc = (130, 55, 75) if sel else (65, 38, 52)
                pygame.draw.rect(surface, fc, (bx, by, fw, bh), border_radius=5)
            pygame.draw.rect(surface, (65, 30, 45), (bx, by, bw, bh), 1, border_radius=5)

            griff_x = bx + max(0, min(bw - 8, fw - 4))
            griff_f = (180, 100, 120) if sel else (100, 60, 75)
            pygame.draw.rect(surface, griff_f, (griff_x, by - 3, 8, bh + 6), border_radius=3)

            btn_h2 = 18
            l_bx2  = bx - 22
            r_bx2  = bx + bw + 4
            btn_y2 = by + (bh - btn_h2) // 2
            b_col  = (140, 65, 80) if sel else (65, 35, 48)
            for bxb, txt in [(l_bx2, "<"), (r_bx2, ">")]:
                pygame.draw.rect(surface, (28, 12, 18), (bxb, btn_y2, 16, btn_h2), border_radius=3)
                if sel:
                    pygame.draw.rect(surface, (65, 28, 40), (bxb, btn_y2, 16, btn_h2), 1, border_radius=3)
                bt = fnt_bar.render(txt, True, b_col)
                surface.blit(bt, (bxb + 8 - bt.get_width() // 2,
                                   btn_y2 + btn_h2 // 2 - bt.get_height() // 2))
            self._btn_links.append(pygame.Rect(l_bx2, btn_y2, 16, btn_h2))
            self._btn_rechts.append(pygame.Rect(r_bx2, btn_y2, 16, btn_h2))

    def _ueberuns_tab(self, surface, fnt_item, fnt_sm, px, cy, pw):
        """Zeichnet den 'Über Uns'-Reiter mit Projektinformationen."""
        self._zeilen_rects = []
        self._btn_links    = []
        self._btn_rechts   = []
        self._slider_bars  = []

        fnt_h = pygame.font.SysFont("monospace", 16, bold=True)
        fnt_b = pygame.font.SysFont("monospace", 13)

        zeilen = [
            ("NIGHTWATCH",                         fnt_h, (175, 55, 65)),
            ("Ein Horror-Escape-Game",              fnt_b, (120, 95, 108)),
            ("",                                    fnt_b, (0, 0, 0)),
            ("Entwickelt von:",                     fnt_h, (140, 118, 128)),
            ("Onur Gündüz",                         fnt_b, (160, 140, 152)),
            ("Fabi",                                fnt_b, (160, 140, 152)),
            ("",                                    fnt_b, (0, 0, 0)),
            ("HTL Rankweil  |  1AHIF  |  2025/26",  fnt_b, (80, 68, 78)),
            ("",                                    fnt_b, (0, 0, 0)),
            ("Technologie:",                        fnt_h, (140, 118, 128)),
            ("Python 3  +  pygame 2.6.1",           fnt_b, (65, 88, 75)),
            ("Sounds: numpy-generiert",              fnt_b, (65, 88, 75)),
            ("Grafiken: Pillow-generiert",           fnt_b, (65, 88, 75)),
            ("KI-Wegfindung: BFS-Navigation",        fnt_b, (65, 88, 75)),
        ]
        ty = cy + 8
        for text, fnt, farbe in zeilen:
            if not text:
                ty += 8
                continue
            ts = fnt.render(text, True, farbe)
            surface.blit(ts, (px + pw // 2 - ts.get_width() // 2, ty))
            ty += ts.get_height() + 5

    def handle_mouse(self, mx: int, my: int, klick: bool):
        """Verarbeitet Maus-Klicks im Pause-Menü."""
        if not klick:
            return None

        if self._weiter_rect and self._weiter_rect.collidepoint(mx, my):
            return ("resume", None)
        if self._menu_rect and self._menu_rect.collidepoint(mx, my):
            return ("menu", None)

        for i, rect in enumerate(self._tab_rects):
            if rect.collidepoint(mx, my):
                if self._tab != i:
                    self._tab   = i
                    self._zeile = 0
                return None

        for i, rect in enumerate(self._btn_links):
            if rect.collidepoint(mx, my):
                self._zeile = i
                return self._wert_aendern(-1)

        for i, rect in enumerate(self._btn_rechts):
            if rect.collidepoint(mx, my):
                self._zeile = i
                return self._wert_aendern(+1)

        for i, (bx, by, bw, bh) in enumerate(self._slider_bars):
            if pygame.Rect(bx, by, bw, bh).collidepoint(mx, my):
                self._zeile = i
                verh = max(0.0, min(1.0, (mx - bx) / max(1, bw)))
                neu  = int(round(verh * 100))
                if   i == 0: self._master = neu; _cfg.set_val("master_vol", neu)
                elif i == 1: self._musik  = neu; _cfg.set_val("music_vol",  neu)
                elif i == 2: self._sfx    = neu; _cfg.set_val("sfx_vol",    neu)
                _cfg.save()
                if self._sounds:
                    self._sounds.apply_volume_settings(self._master, self._musik, self._sfx)
                return None

        for i, rect in enumerate(self._zeilen_rects):
            if rect.collidepoint(mx, my):
                self._zeile = i
                return None

        return None
# KI CODE ENDE


def _text_umbrechen(text: str, font: pygame.font.Font, max_b: int) -> list:
    # text umbrechen damit er in die karte passt
    woerter = text.split()
    zeilen: list = []
    aktuell = ""
    for wort in woerter:
        test = (aktuell + " " + wort).strip()
        if font.size(test)[0] <= max_b:
            aktuell = test
        else:
            if aktuell:
                zeilen.append(aktuell)
            aktuell = wort
    if aktuell:
        zeilen.append(aktuell)
    return zeilen if zeilen else [text]


def _schwierigkeitsscreen_zeichnen(surface: pygame.Surface,
                                    ausgewaehlt: int,
                                    clock_ms: int,
                                    hover: int = -1) -> list:
    # difficulty-karten zeichnen, gibt die rects zurück für mausklick-erkennung
    surface.fill((3, 2, 5))

    rng = random.Random(clock_ms // 4000)
    for _ in range(60):
        sx = rng.randint(0, GV.SCREEN_W)
        sy = rng.randint(0, GV.SCREEN_H)
        br = rng.randint(6, 25)
        pygame.draw.circle(surface, (br, br // 3, br // 3), (sx, sy), 1)

    fnt_titel = pygame.font.SysFont("monospace", 42, bold=True)
    fnt_sub   = pygame.font.SysFont("monospace", 16)
    fnt_med   = pygame.font.SysFont("monospace", 18, bold=True)
    fnt_sm    = pygame.font.SysFont("monospace", 12)

    titel = fnt_titel.render("SCHWIERIGKEITSGRAD", True, (140, 20, 20))
    surface.blit(titel, (GV.SCREEN_W // 2 - titel.get_width() // 2, 62))

    pygame.draw.line(surface, (60, 10, 10),
                     (GV.SCREEN_W // 2 - 280, 116), (GV.SCREEN_W // 2 + 280, 116), 1)

    sub = fnt_sub.render("Wähle deinen Schwierigkeitsgrad.", True, (60, 45, 50))
    surface.blit(sub, (GV.SCREEN_W // 2 - sub.get_width() // 2, 126))

    diff_keys = list(GV.SCHWIERIGKEITEN.keys())
    n       = len(diff_keys)
    luecke  = 16
    rand    = 28
    avail   = GV.SCREEN_W - 2 * rand
    karte_b = (avail - luecke * (n - 1)) // n
    karte_h = 240
    gesamt  = n * karte_b + (n - 1) * luecke
    start_x = rand + (avail - gesamt) // 2
    karte_y = 152

    karte_rects: list = []

    for i, key in enumerate(diff_keys):
        d   = GV.SCHWIERIGKEITEN[key]
        kx  = start_x + i * (karte_b + luecke)
        col = d["color"]
        sel = (i == ausgewaehlt)
        hov = (i == hover and not sel)
        rect = pygame.Rect(kx, karte_y, karte_b, karte_h)
        karte_rects.append(rect)

        if   sel: bg = (int(col[0]*0.28), int(col[1]*0.18), int(col[2]*0.14))
        elif hov: bg = (int(col[0]*0.18), int(col[1]*0.12), int(col[2]*0.10))
        else:     bg = (int(col[0]*0.11), int(col[1]*0.07), int(col[2]*0.06))
        pygame.draw.rect(surface, bg, rect, border_radius=8)

        brd_col = (col if sel else (tuple(int(c * 0.55) for c in col)
                   if hov else tuple(c // 4 for c in col)))
        brd_b   = 3 if sel else (2 if hov else 1)
        pygame.draw.rect(surface, brd_col, rect, brd_b, border_radius=8)

        if sel:
            puls = abs(math.sin(clock_ms / 600)) * 0.3 + 0.7
            pc   = tuple(int(c * puls) for c in col)
            pygame.draw.rect(surface, pc,
                             (kx - 2, karte_y - 2, karte_b + 4, karte_h + 4),
                             2, border_radius=9)

        lbl_col = col if sel else tuple(int(c * 0.65) for c in col)
        lbl = fnt_med.render(d["label"], True, lbl_col)
        surface.blit(lbl, (kx + karte_b // 2 - lbl.get_width() // 2, karte_y + 12))

        desc_zeilen = _text_umbrechen(d["desc"], fnt_sm, karte_b - 16)
        dy = karte_y + 40
        for zeile in desc_zeilen:
            ds = fnt_sm.render(zeile, True, (148, 128, 132))
            surface.blit(ds, (kx + karte_b // 2 - ds.get_width() // 2, dy))
            dy += fnt_sm.get_height() + 3

        trenn_y = karte_y + karte_h - 106
        pygame.draw.line(surface, tuple(c // 4 for c in col),
                         (kx + 10, trenn_y), (kx + karte_b - 10, trenn_y), 1)

        stats = [
            f"Patrol: {d['patrol']:.1f}",
            f"Alert:  {d['alert']:.1f}",
            f"Hunt:   {d['hunt']:.1f}",
            f"Sicht:  {d['sight']}px",
        ]
        for si, stat in enumerate(stats):
            farbe = (110, 100, 110) if sel else (78, 70, 78)
            st = fnt_sm.render(stat, True, farbe)
            surface.blit(st, (kx + 10, trenn_y + 8 + si * 22))

        if sel:
            ind = fnt_sm.render("[ AUSGEWÄHLT ]", True,
                                 tuple(int(c * 0.75) for c in col))
            surface.blit(ind, (kx + karte_b // 2 - ind.get_width() // 2,
                                karte_y + karte_h + 5))

    hinweis_txt = "Klick wählen  |  2× Klick / ENTER bestätigen  |  ← → Tasten  |  ESC zurück"
    hinweis = fnt_sub.render(hinweis_txt, True, (60, 50, 60))
    surface.blit(hinweis, (GV.SCREEN_W // 2 - hinweis.get_width() // 2, GV.SCREEN_H - 48))

    dash_info = fnt_sm.render(
        "SPACE = Dash (betäubt Monster kurz, 60s Cooldown)",
        True, (50, 100, 140)
    )
    surface.blit(dash_info, (GV.SCREEN_W // 2 - dash_info.get_width() // 2, GV.SCREEN_H - 76))

    vig = pygame.Surface((GV.SCREEN_W, GV.SCREEN_H), pygame.SRCALPHA)
    for i in range(0, 250, 18):
        a = int(150 * (1 - i / 250) ** 2)
        pygame.draw.rect(vig, (0, 0, 0, a), (i, i, GV.SCREEN_W - 2*i, GV.SCREEN_H - 2*i), 18)
    surface.blit(vig, (0, 0))

    return karte_rects


def _menu_zeichnen(surface: pygame.Surface, clock_ms: int) -> None:
    # hauptmenü mit titel, steuerungsübersicht und animation
    surface.fill((3, 2, 5))

    rng = random.Random(clock_ms // 3000)
    for _ in range(120):
        sx = rng.randint(0, GV.SCREEN_W)
        sy = rng.randint(0, GV.SCREEN_H)
        br = rng.randint(8, 35)
        pygame.draw.circle(surface, (br, br // 2, br), (sx, sy), 1)

    for i, (bx, by) in enumerate([(80, 60), (1180, 80), (200, 650), (1050, 680)]):
        draw_blood_splatter(surface, bx, by, seed=i * 3, groesse=2.0)

    fnt_titel = pygame.font.SysFont("monospace", 82, bold=True)
    fnt_sub   = pygame.font.SysFont("monospace", 18)
    fnt_sm    = pygame.font.SysFont("monospace", 14)

    puls  = abs(math.sin(clock_ms / 1400)) * 0.18 + 0.82
    r_col = int(200 * puls)
    g_col = int(10  * puls)

    for off in range(6, 0, -1):
        sh = fnt_titel.render("NIGHTWATCH", True, (off * 5, 0, 0))
        surface.blit(sh, (GV.SCREEN_W // 2 - sh.get_width() // 2 + off, 200 + off))

    titel = fnt_titel.render("NIGHTWATCH", True, (r_col, g_col, g_col))
    surface.blit(titel, (GV.SCREEN_W // 2 - titel.get_width() // 2, 200))

    pygame.draw.line(surface, (80, 0, 0),
                     (GV.SCREEN_W // 2 - 300, 295), (GV.SCREEN_W // 2 + 300, 295), 2)

    sub = fnt_sub.render("There is no escape. There is only dark.", True, (70, 50, 55))
    surface.blit(sub, (GV.SCREEN_W // 2 - sub.get_width() // 2, 315))

    steuerung = [
        ("WASD / Pfeiltasten",  "Bewegen"),
        ("Maus",                "Taschenlampe richten"),
        ("F",                   "Taschenlampe ein/aus"),
        ("SPACE",               "Dash (betäubt Monster, 60s CD)"),
        ("SHIFT",               "Schleichen"),
        ("E",                   "Interagieren"),
        ("P / ESC",             "Pause & Einstellungen"),
        ("F11",                 "Vollbild"),
    ]
    col_taste = (80, 60, 70)
    col_wert  = (55, 45, 60)
    ctrl_y    = 360
    for taste, erklaerung in steuerung:
        kt = fnt_sm.render(taste,      True, col_taste)
        vt = fnt_sm.render(erklaerung, True, col_wert)
        surface.blit(kt, (GV.SCREEN_W // 2 - 220, ctrl_y))
        surface.blit(vt, (GV.SCREEN_W // 2 -  10, ctrl_y))
        ctrl_y += 20

    if (clock_ms // 700) % 2 == 0:
        hint = fnt_sub.render(
            "[ ENTER ] Spielen          [ H ] Highscores",
            True, (120, 30, 30)
        )
        surface.blit(hint, (GV.SCREEN_W // 2 - hint.get_width() // 2, 540))

    team = fnt_sm.render(
        "Onur Gündüz & Fabi  |  HTL Rankweil 1AHIF  |  2025/26",
        True, (35, 28, 35)
    )
    surface.blit(team, (GV.SCREEN_W // 2 - team.get_width() // 2, GV.SCREEN_H - 28))

    vig = pygame.Surface((GV.SCREEN_W, GV.SCREEN_H), pygame.SRCALPHA)
    for i in range(0, 300, 20):
        a = int(180 * (1 - i / 300) ** 2)
        pygame.draw.rect(vig, (0, 0, 0, a), (i, i, GV.SCREEN_W - 2*i, GV.SCREEN_H - 2*i), 20)
    surface.blit(vig, (0, 0))


def _gefangen_screen_zeichnen(surface: pygame.Surface,
                               clock_ms: int, alpha: int) -> None:
    # roter fade-in + "erwischt!" text wenn das monster den spieler kriegt
    ov = pygame.Surface((GV.SCREEN_W, GV.SCREEN_H))
    ov.fill((15, 0, 0))
    ov.set_alpha(alpha)
    surface.blit(ov, (0, 0))

    if alpha < 190:
        return

    fnt_gr = pygame.font.SysFont("monospace", 68, bold=True)
    fnt_sm = pygame.font.SysFont("monospace", 17)

    puls = abs(math.sin(clock_ms / 450)) * 55
    col  = (int(170 + puls), 15, 15)

    for off in range(4, 0, -1):
        sh = fnt_gr.render("ERWISCHT!", True, (off * 8, 0, 0))
        surface.blit(sh, (GV.SCREEN_W // 2 - sh.get_width() // 2 + off,
                          GV.SCREEN_H // 2 - 60 + off))

    txt = fnt_gr.render("ERWISCHT!", True, col)
    surface.blit(txt, (GV.SCREEN_W // 2 - txt.get_width() // 2, GV.SCREEN_H // 2 - 60))

    sub = fnt_sm.render("ENTER – Nochmal     ESC – Menü", True, (100, 40, 40))
    surface.blit(sub, (GV.SCREEN_W // 2 - sub.get_width() // 2, GV.SCREEN_H // 2 + 40))


def _gewonnen_screen_zeichnen(surface: pygame.Surface,
                               vergangen: float,
                               clock_ms: int,
                               schwierigkeit: str) -> None:
    # grüner "entkommen!" screen mit zeit und schwierigkeitsgrad
    surface.fill((3, 10, 5))

    fnt_gr  = pygame.font.SysFont("monospace", 58, bold=True)
    fnt_med = pygame.font.SysFont("monospace", 22)
    fnt_sm  = pygame.font.SysFont("monospace", 15)

    puls = abs(math.sin(clock_ms / 900)) * 25
    col  = (int(30 + puls), int(180 + puls // 2), int(60 + puls // 2))

    txt = fnt_gr.render("ENTKOMMEN!", True, col)
    surface.blit(txt, (GV.SCREEN_W // 2 - txt.get_width() // 2, 200))

    mins  = int(vergangen // 60)
    sek   = int(vergangen % 60)
    ms100 = int((vergangen % 1) * 100)
    zeit_t = fnt_med.render(f"Zeit: {mins:02d}:{sek:02d}.{ms100:02d}", True, (100, 160, 100))
    surface.blit(zeit_t, (GV.SCREEN_W // 2 - zeit_t.get_width() // 2, 295))

    diff = GV.SCHWIERIGKEITEN[schwierigkeit]
    diff_t = fnt_sm.render(f"Schwierigkeitsgrad: {diff['label']}",
                            True, diff["color"])
    surface.blit(diff_t, (GV.SCREEN_W // 2 - diff_t.get_width() // 2, 335))

    sub = fnt_sm.render("ENTER – Highscore     ESC – Menü", True, (60, 100, 60))
    surface.blit(sub, (GV.SCREEN_W // 2 - sub.get_width() // 2, 380))


def _namens_eingabe_zeichnen(surface: pygame.Surface,
                              name_puffer: str,
                              vergangen: float) -> None:
    # namen eintippen bevor der highscore gespeichert wird
    surface.fill((3, 2, 5))

    fnt_gr  = pygame.font.SysFont("monospace", 34, bold=True)
    fnt_med = pygame.font.SysFont("monospace", 20)
    fnt_sm  = pygame.font.SysFont("monospace", 14)

    titel = fnt_gr.render("Namen eingeben:", True, (160, 130, 140))
    surface.blit(titel, (GV.SCREEN_W // 2 - titel.get_width() // 2, 210))

    bw, bh = 320, 48
    bx = GV.SCREEN_W // 2 - bw // 2
    by = 275
    pygame.draw.rect(surface, (20, 15, 22), (bx, by, bw, bh), border_radius=6)
    pygame.draw.rect(surface, (80, 40, 50), (bx, by, bw, bh), 2, border_radius=6)

    cursor = "_" if (pygame.time.get_ticks() // 550) % 2 == 0 else " "
    name_t = fnt_med.render(name_puffer + cursor, True, (200, 180, 190))
    surface.blit(name_t, (bx + 14, by + 12))

    mins = int(vergangen // 60)
    sek  = int(vergangen % 60)
    zeit = fnt_sm.render(f"Zeit: {mins:02d}:{sek:02d}", True, (90, 100, 90))
    surface.blit(zeit, (GV.SCREEN_W // 2 - zeit.get_width() // 2, 348))

    hint = fnt_sm.render("ENTER – Bestätigen     ESC – Überspringen", True, (60, 55, 65))
    surface.blit(hint, (GV.SCREEN_W // 2 - hint.get_width() // 2, 400))


class Game:
    """eine komplette spielsitzung - spieler, monster, items, kamera."""

    def __init__(self, schwierigkeit: str = "Normal"):
        self.difficulty = schwierigkeit
        self.sounds     = SoundManager()

        self.player    = Player(*PLAYER_START)
        self.monster   = Monster(*MONSTER_START)
        self.items     = ItemManager(self.sounds)
        self.lighting  = Lighting()
        self.jumpscare = JumpscareManager(self.sounds)

        self._kamera = ZoomCamera()

        self.monster.apply_difficulty(GV.SCHWIERIGKEITEN[schwierigkeit])

        self._start_ticks: int   = pygame.time.get_ticks()
        self._vergangen:   float = 0.0

        self._hinweis_text:  str   = ""
        self._hinweis_timer: float = 0.0

        self._hb_timer:     int = 0
        self._hb_intervall: int = 0

        self._r3_js_fertig: bool  = False
        self._kette_schwing: float = 0.0
        self._tropf_aktiv:  bool  = False

        master = _cfg.get("master_vol", 80)
        musik  = _cfg.get("music_vol",  55)
        sfx    = _cfg.get("sfx_vol",    80)
        self.sounds.apply_volume_settings(master, musik, sfx)

        self.sounds.start_ambient()
        self.sounds.start_monster_breathing()
        self.sounds.start_bg_music(master, musik)

    def hinweis_zeigen(self, text: str, dauer: float = 3.0) -> None:
        # kurze nachricht oben einblenden (z.b. "monster betäubt!")
        self._hinweis_text  = text
        self._hinweis_timer = dauer

    def update(self, events: list,
               keys: pygame.key.ScancodeWrapper,
               mx: int, my: int) -> GameState | None:
        """spiellogik einmal pro frame - gibt neuen zustand zurück wenn nötig."""
        from game.level import R3, R5

        aktueller_raum = get_room_at(self.player.x, self.player.y)
        self._kamera.update(self.player.x, self.player.y, aktueller_raum)
        cam_x = self._kamera.cam_x
        cam_y = self._kamera.cam_y
        zoom  = self._kamera.zoom

        adj_mx = int(mx / zoom)
        adj_my = int(my / zoom)

        self.player.update(keys, events, adj_mx, adj_my, cam_x, cam_y, self.sounds)

        if self.player.dash_just_activated:
            d = dist(self.monster.x, self.monster.y,
                     self.player.x, self.player.y)
            if d <= GV.DASH_STUN_BEREICH:
                self.monster.stun(GV.DASH_STUN_DAUER)
                self.hinweis_zeigen("Monster betäubt!", 2.0)
                self.sounds.play("alert")
            else:
                self.hinweis_zeigen("Dash! (Monster zu weit weg)", 1.5)

        akku_gewinn = self.items.update(
            self.player.x, self.player.y, events, set(), self.player.battery
        )
        if akku_gewinn > 0:
            self.player.battery = min(GV.LAMPE_AKKU_MAX,
                                      self.player.battery + akku_gewinn)
            self.hinweis_zeigen("Akku aufgeladen! +40%", 2.5)
            # lampe wieder anschalten wenn sie vorher ausgegangen ist
            if not self.player.torch_on:
                self.player.torch_on = True

        self.monster.update(
            self.player.x, self.player.y,
            self.player.noise_level, self.player.battery,
            self.sounds
        )

        if self.monster.just_triggered_jumpscare:
            sx = int((self.player.x - cam_x) * zoom)
            sy = int((self.player.y - cam_y) * zoom)
            self.jumpscare.trigger(JumpscareEffect.TYP_HUNT, sx, sy)
            self.hinweis_zeigen("SCHLEICHEN! [SHIFT halten]", 4.0)

        if not self._r3_js_fertig:
            if (R3.rect.collidepoint(self.player.x, self.player.y) and
                    self.monster.state in (MonsterState.ALERT, MonsterState.HUNT)):
                sx3 = int((self.player.x - cam_x) * zoom)
                sy3 = int((self.player.y - cam_y) * zoom)
                self.jumpscare.trigger(JumpscareEffect.TYP_RAUM_R3, sx3, sy3)
                self._r3_js_fertig = True

        self.jumpscare.update(spiel_laeuft=True)
        self.lighting.update()
        self._kette_schwing += 0.02

        if (not self.monster.is_stunned and
                self.monster.catches_player(self.player.x, self.player.y)):
            sx = int((self.player.x - cam_x) * zoom)
            sy = int((self.player.y - cam_y) * zoom)
            self.jumpscare.trigger(JumpscareEffect.TYP_GEFANGEN, sx, sy)
            return GameState.CAUGHT

        if self.player.reached_exit and self.items.all_tasks_done:
            self._vergangen = (pygame.time.get_ticks() - self._start_ticks) / 1000.0
            return GameState.WIN

        d = dist(self.monster.x, self.monster.y, self.player.x, self.player.y)
        if self.monster.state == MonsterState.HUNT and not self.monster.is_stunned:
            self._hb_intervall = max(12, int(55 - (1 - d / 600) * 43))
            self.sounds.set_breath_volume(max(0.0, 0.55 - d / 800))
        elif self.monster.state == MonsterState.ALERT:
            self._hb_intervall = 44
            self.sounds.set_breath_volume(0.18)
        else:
            self._hb_intervall = 0
            self.sounds.set_breath_volume(0.0)

        im_keller = R5.rect.collidepoint(self.player.x, self.player.y)
        if im_keller and not self._tropf_aktiv:
            self.sounds.start_dripping()
            self._tropf_aktiv = True
        elif not im_keller and self._tropf_aktiv:
            self.sounds.stop_dripping()
            self._tropf_aktiv = False

        if self._hinweis_timer > 0:
            self._hinweis_timer -= 1 / GV.FPS

        self._vergangen = (pygame.time.get_ticks() - self._start_ticks) / 1000.0
        return None

    def draw(self, surface: pygame.Surface) -> None:
        # render-reihenfolge: welt → zoom-skalierung → dunkelheit → hud → jumpscares
        shake_x, shake_y = self.jumpscare.shake_offset
        cam_x = self._kamera.cam_x
        cam_y = self._kamera.cam_y
        zoom  = self._kamera.zoom
        vb, vh = self._kamera.view_size

        kette_schwing = math.sin(self._kette_schwing) * 0.6

        view_surf = pygame.Surface((vb, vh))
        draw_level(view_surf, cam_x, cam_y, kette_schwing)
        self.items.draw(view_surf, cam_x, cam_y,
                        self.player.x, self.player.y, self.player.battery)
        self.monster.draw(view_surf, cam_x, cam_y)
        self.player.draw(view_surf, cam_x, cam_y)

        akt_raum = get_room_at(self.player.x, self.player.y)
        v_sx = self.player.x - cam_x
        v_sy = self.player.y - cam_y
        self.lighting.draw_world(
            view_surf, v_sx, v_sy,
            self.player.facing,
            self.player.battery,
            self.player.torch_on,
            akt_raum,
            self.items.lit_candle_positions,
            cam_x, cam_y
        )

        render_surf = pygame.Surface((GV.SCREEN_W, GV.SCREEN_H))
        if abs(zoom - 1.0) > 0.01:
            skaliert = pygame.transform.smoothscale(view_surf, (GV.SCREEN_W, GV.SCREEN_H))
        else:
            skaliert = pygame.transform.scale(view_surf, (GV.SCREEN_W, GV.SCREEN_H))
        render_surf.blit(skaliert, (0, 0))

        self.lighting.draw_overlay(render_surf)

        aufgaben_fertig = [t.completed for t in self.items._tasks]
        d = dist(self.monster.x, self.monster.y, self.player.x, self.player.y)
        puls = 0.0
        if self.monster.state == MonsterState.HUNT and not self.monster.is_stunned:
            puls = clamp(1.0 - d / 500, 0.0, 1.0)
        elif self.monster.state == MonsterState.ALERT:
            puls = 0.22

        draw_hud(
            render_surf,
            self.player.battery,
            self.items.keys_collected,
            aufgaben_fertig,
            puls,
            self._hinweis_text if self._hinweis_timer > 0 else "",
            self._hinweis_timer / 4.0,
            dash_cooldown=self.player._dash_cooldown,
            is_dashing=self.player.is_dashing,
        )

        self.monster.draw_state_indicator(render_surf)

        fnt_zeit = pygame.font.SysFont("monospace", 12)
        mins   = int(self._vergangen // 60)
        sek    = int(self._vergangen % 60)
        diff_col = GV.SCHWIERIGKEITEN[self.difficulty]["color"]
        diff_lbl = GV.SCHWIERIGKEITEN[self.difficulty]["label"]
        zeit_str = f"{mins:02d}:{sek:02d}  |  {diff_lbl}"
        zeit_t   = fnt_zeit.render(zeit_str, True, tuple(c // 2 for c in diff_col))
        render_surf.blit(zeit_t, (GV.SCREEN_W // 2 - zeit_t.get_width() // 2, 6))

        if not self.player.torch_on:
            fnt_f = pygame.font.SysFont("monospace", 13)
            ft = fnt_f.render("[F] Lampe ein", True, (100, 80, 80))
            render_surf.blit(ft, (GV.SCREEN_W // 2 - ft.get_width() // 2, GV.SCREEN_H - 80))

        # exit-hinweis wenn man nah an der tür ist
        if self.player.near_exit:
            fnt_exit = pygame.font.SysFont("monospace", 15, bold=True)
            if self.items.all_tasks_done:
                et = fnt_exit.render("[E] Türe öffnen – Entkommen!", True, (80, 220, 80))
            else:
                offen = sum(1 for t in self.items._tasks if not t.completed)
                et = fnt_exit.render(f"Noch {offen} Aufgabe(n) zu erledigen!", True, (200, 130, 50))
            render_surf.blit(et, (GV.SCREEN_W // 2 - et.get_width() // 2, GV.SCREEN_H - 100))

        if shake_x != 0 or shake_y != 0:
            geschuettelt = pygame.Surface((GV.SCREEN_W, GV.SCREEN_H))
            geschuettelt.fill((0, 0, 0))
            geschuettelt.blit(render_surf, (shake_x, shake_y))
            surface.blit(geschuettelt, (0, 0))
        else:
            surface.blit(render_surf, (0, 0))

        self.jumpscare.draw(surface)

    @property
    def elapsed(self) -> float:
        # vergangene spielzeit in sekunden
        return self._vergangen


def main() -> None:
    # alles initialisieren und hauptloop starten
    GameVariables.init()
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=256)
    pygame.display.set_caption(GV.TITEL)
    pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_CROSSHAIR)

    fs_manager = FullscreenManager()
    screen     = fs_manager.get_screen()
    uhr        = pygame.time.Clock()

    zustand: GameState        = GameState.MENU
    spiel:   Game | None      = None
    pause:   PauseMenu | None = None

    diff_keys     = list(GV.SCHWIERIGKEITEN.keys())
    diff_auswahl  = 2
    gew_diff: str = "Normal"
    _diff_karten: list = []

    name_puffer:    str   = ""
    vergangen_win:  float = 0.0
    gefangen_alpha: int   = 0

    laeuft = True
    while laeuft:
        clock_ms = pygame.time.get_ticks()
        events   = pygame.event.get()

        for event in events:
            if event.type == pygame.QUIT:
                laeuft = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    screen = fs_manager.toggle()
                elif event.key == pygame.K_ESCAPE:
                    if zustand == GameState.CAUGHT:
                        if spiel: spiel.sounds.stop_all()
                        spiel = None; zustand = GameState.MENU
                    elif zustand == GameState.WIN:
                        if spiel: spiel.sounds.stop_all()
                        spiel = None; zustand = GameState.MENU
                    elif zustand == GameState.DIFFICULTY:
                        zustand = GameState.MENU
                    elif zustand == GameState.NAME_INPUT:
                        zustand = GameState.HIGHSCORE
                    elif zustand == GameState.HIGHSCORE:
                        zustand = GameState.MENU
                    elif zustand == GameState.MENU:
                        laeuft = False

        keys = pygame.key.get_pressed()
        mx, my = pygame.mouse.get_pos()

        _sw, _sh = screen.get_size()
        rmx = mx * GV.SCREEN_W // _sw if _sw > 0 else mx
        rmy = my * GV.SCREEN_H // _sh if _sh > 0 else my
        klick = any(e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 for e in events)

        render = pygame.Surface((GV.SCREEN_W, GV.SCREEN_H))

        if zustand == GameState.MENU:
            _menu_zeichnen(render, clock_ms)
            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        zustand = GameState.DIFFICULTY
                    elif event.key == pygame.K_h:
                        zustand = GameState.HIGHSCORE

        elif zustand == GameState.DIFFICULTY:
            _hover = -1
            for _i, _r in enumerate(_diff_karten):
                if _r.collidepoint(rmx, rmy):
                    _hover = _i
                    break
            _diff_karten = _schwierigkeitsscreen_zeichnen(
                render, diff_auswahl, clock_ms, _hover)

            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        diff_auswahl = (diff_auswahl - 1) % len(diff_keys)
                    elif event.key == pygame.K_RIGHT:
                        diff_auswahl = (diff_auswahl + 1) % len(diff_keys)
                    elif event.key == pygame.K_RETURN:
                        gew_diff       = diff_keys[diff_auswahl]
                        spiel          = Game(schwierigkeit=gew_diff)
                        gefangen_alpha = 0
                        zustand        = GameState.PLAYING
                        _diff_karten   = []
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for _i, _r in enumerate(_diff_karten):
                        if _r.collidepoint(rmx, rmy):
                            if _i == diff_auswahl:
                                gew_diff       = diff_keys[diff_auswahl]
                                spiel          = Game(schwierigkeit=gew_diff)
                                gefangen_alpha = 0
                                zustand        = GameState.PLAYING
                                _diff_karten   = []
                            else:
                                diff_auswahl = _i
                            break

        elif zustand == GameState.PLAYING:
            for event in events:
                if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_p):
                    zustand = GameState.PAUSED
                    pause   = PauseMenu(spiel.sounds if spiel else None,
                                        fs_manager.fullscreen)
                    break

            if spiel and zustand == GameState.PLAYING:
                # rmx/rmy statt mx/my - sonst stimmt die taschenlampenrichtung nicht
                neuer_z = spiel.update(events, keys, rmx, rmy)
                spiel.draw(render)
                if neuer_z == GameState.CAUGHT:
                    gefangen_alpha = 0
                    zustand = GameState.CAUGHT
                elif neuer_z == GameState.WIN:
                    vergangen_win = spiel.elapsed
                    zustand = GameState.WIN

        elif zustand == GameState.PAUSED:
            if spiel:
                spiel.draw(render)
            if pause is None:
                pause = PauseMenu(spiel.sounds if spiel else None,
                                  fs_manager.fullscreen)
            pause.draw(render)

            if pause is not None:
                maus_aktion = pause.handle_mouse(rmx, rmy, klick)
                if maus_aktion:
                    art, nutzlast = maus_aktion
                    if art == "resume":
                        zustand = GameState.PLAYING
                        pause   = None
                    elif art == "menu":
                        if spiel: spiel.sounds.stop_all()
                        spiel = None; pause = None
                        zustand = GameState.MENU
                    elif art == "toggle_fullscreen":
                        screen = fs_manager.toggle()
                        if pause is not None:
                            pause._vollbild = fs_manager.fullscreen

            for event in events:
                if pause is None:
                    break
                if event.type == pygame.KEYDOWN and event.key == pygame.K_m:
                    if spiel: spiel.sounds.stop_all()
                    spiel = None; pause = None
                    zustand = GameState.MENU
                    break
                aktion = pause.handle_event(event)
                if aktion:
                    art, nutzlast = aktion
                    if art == "resume":
                        zustand = GameState.PLAYING
                        pause   = None
                        break
                    elif art == "toggle_fullscreen":
                        screen = fs_manager.toggle()
                        if pause is not None:
                            pause._vollbild = fs_manager.fullscreen

        elif zustand == GameState.CAUGHT:
            if spiel:
                spiel.draw(render)
                spiel.jumpscare.update(spiel_laeuft=False)
                spiel.jumpscare.draw(render)

            gefangen_alpha = min(255, gefangen_alpha + 2)
            _gefangen_screen_zeichnen(render, clock_ms, gefangen_alpha)

            for event in events:
                if event.type == pygame.KEYDOWN and gefangen_alpha >= 190:
                    if event.key == pygame.K_RETURN:
                        if spiel: spiel.sounds.stop_all()
                        spiel          = Game(schwierigkeit=gew_diff)
                        gefangen_alpha = 0
                        zustand        = GameState.PLAYING
                    elif event.key == pygame.K_ESCAPE:
                        if spiel: spiel.sounds.stop_all()
                        spiel   = None
                        zustand = GameState.MENU

        elif zustand == GameState.WIN:
            render.fill((3, 10, 5))
            _gewonnen_screen_zeichnen(render, vergangen_win, clock_ms, gew_diff)

            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        name_puffer = ""
                        zustand     = GameState.NAME_INPUT
                    elif event.key == pygame.K_ESCAPE:
                        if spiel: spiel.sounds.stop_all()
                        spiel   = None
                        zustand = GameState.MENU

        elif zustand == GameState.NAME_INPUT:
            _namens_eingabe_zeichnen(render, name_puffer, vergangen_win)

            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        if name_puffer.strip():
                            save_highscore(name_puffer.strip(), vergangen_win)
                        if spiel: spiel.sounds.stop_all()
                        spiel   = None
                        zustand = GameState.HIGHSCORE
                    elif event.key == pygame.K_BACKSPACE:
                        name_puffer = name_puffer[:-1]
                    elif event.key == pygame.K_ESCAPE:
                        zustand = GameState.HIGHSCORE
                    elif len(name_puffer) < 12:
                        zeichen = event.unicode
                        if zeichen.isprintable() and zeichen not in ('\n', '\r'):
                            name_puffer += zeichen

        elif zustand == GameState.HIGHSCORE:
            render.fill((3, 2, 5))
            draw_highscore_screen(render, clock_ms)

        screen.blit(pygame.transform.scale(render, screen.get_size()), (0, 0))
        pygame.display.flip()
        uhr.tick(GV.FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
