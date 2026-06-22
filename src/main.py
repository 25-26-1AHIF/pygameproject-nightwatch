import math
import os
import sys
import random
import pygame
from enum import Enum, auto

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

GV = GameVariables


class GameState(Enum):
    # alle möglichen spielzustände
    MENU       = auto()
    STEUERUNG  = auto()
    PLAYING    = auto()
    PAUSED     = auto()
    CAUGHT     = auto()
    WIN        = auto()
    NAME_INPUT = auto()
    HIGHSCORE  = auto()


# KI CODE ANFANG
# Claude Opus 4.8
# Prompt: "Implementiere ZoomCamera mit Lerp-Zoom fuer pygame."
class ZoomCamera:
    # kamera die sanft in den aktuellen raum hineinzoomt

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
        # zoom und kameraposition einmal pro frame aktualisieren
        if aktueller_raum is not None:
            # ENT-Raum ist sehr breit (1640px) - spieler direkt verfolgen
            if aktueller_raum.name == "Eingangsbereich":
                ziel_zoom = 1.30
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

        # zoom langsam angleichen (lerp)
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
        # groesse der view-surface in weltpixeln
        return (max(1, int(GV.SCREEN_W / self._zoom)),
                max(1, int(GV.SCREEN_H / self._zoom)))
# KI CODE ENDE


class FullscreenManager:
    # vollbild/fenster umschalten und aufloesung verwalten

    def __init__(self):
        self.fullscreen: bool = False
        self._screen: pygame.Surface | None = None
        self._res_key: str = _cfg.get("resolution", "1080p")

    def get_screen(self) -> pygame.Surface:
        # startet im vollbild mit pygame.SCALED
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
        # F11: zwischen vollbild und fenster wechseln
        self.fullscreen = not self.fullscreen
        w, h = GV.AUFLÖSUNGEN.get(self._res_key, (1920, 1080))
        if self.fullscreen:
            self._screen = pygame.display.set_mode(
                (0, 0), pygame.FULLSCREEN | pygame.SCALED
            )
        else:
            self._screen = pygame.display.set_mode((w, h), pygame.RESIZABLE)
        return self._screen


# gecachtes pause-hintergrundbild
_pause_bg: pygame.Surface | None = None


def _lade_pause_bg() -> pygame.Surface | None:
    # pause-hintergrundbild laden (einmalig)
    global _pause_bg
    if _pause_bg is not None:
        return _pause_bg
    import os
    pfad = os.path.join(os.path.dirname(__file__), "assets", "pause_bg.png")
    try:
        img = pygame.image.load(pfad).convert()
        _pause_bg = pygame.transform.scale(img, (GV.SCREEN_W, GV.SCREEN_H))
    except Exception:
        _pause_bg = None
    return _pause_bg


def _pause_zeichnen(surface: pygame.Surface, hover: int = -1) -> list:
    # pause-bildschirm zeichnen - gibt liste der 3 button-rects zurueck
    # index: 0=weiter, 1=hauptmenue, 2=beenden

    bg = _lade_pause_bg()
    if bg:
        surface.blit(bg, (0, 0))
    else:
        surface.fill((3, 2, 5))

    # dunkles overlay damit man noch sieht dass pause aktiv ist
    ov = pygame.Surface((GV.SCREEN_W, GV.SCREEN_H), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 120))
    surface.blit(ov, (0, 0))

    bw   = 300
    bh   = 48
    gap  = 14
    cx   = GV.SCREEN_W // 2
    start_y = 310

    beschriftungen = ["WEITER", "ZURÜCK ZUM HAUPTMENÜ", "SPIEL BEENDEN"]
    rects = []
    for i, lbl in enumerate(beschriftungen):
        by = start_y + i * (bh + gap)
        r  = _menu_button(surface, lbl, cx, by, bw, bh, hover == i)
        rects.append(r)

    fnt_sm = pygame.font.SysFont("monospace", 12)
    hint   = fnt_sm.render("[ ESC / P ]  Weiterspielen", True, (55, 48, 62))
    surface.blit(hint, (cx - hint.get_width() // 2, GV.SCREEN_H - 22))

    return rects



def _text_umbrechen(text: str, font: pygame.font.Font, max_b: int) -> list:
    # text in zeilen umbrechen die nicht breiter als max_b sind
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


# gecachtes hintergrundbild für das hauptmenü
_menu_bg: pygame.Surface | None = None


def _lade_menu_bg() -> pygame.Surface | None:
    # hintergrundbild laden und auf bildschirmgröße skalieren (einmalig)
    global _menu_bg
    if _menu_bg is not None:
        return _menu_bg
    import os
    pfad = os.path.join(os.path.dirname(__file__), "assets", "menu_bg.png")
    try:
        img = pygame.image.load(pfad).convert()
        _menu_bg = pygame.transform.scale(img, (GV.SCREEN_W, GV.SCREEN_H))
    except Exception:
        _menu_bg = None
    return _menu_bg


def _menu_button(surface: pygame.Surface, text: str, cx: int, cy: int,
                 w: int, h: int, hover: bool) -> pygame.Rect:
    # einen einzelnen menue-button zeichnen und sein rect zurueckgeben
    rect = pygame.Rect(cx - w // 2, cy - h // 2, w, h)

    # hintergrund: dunkles halb-transparentes rechteck
    bg = pygame.Surface((w, h), pygame.SRCALPHA)
    if hover:
        bg.fill((18, 14, 28, 220))
    else:
        bg.fill((8, 6, 16, 200))
    surface.blit(bg, rect.topleft)

    # rahmen: hell wenn hover
    brd_col = (200, 195, 210) if hover else (90, 85, 100)
    pygame.draw.rect(surface, brd_col, rect, 2)

    # pfeil links vom text wenn hover
    fnt = pygame.font.SysFont("monospace", 18, bold=True)
    if hover:
        pfeil = fnt.render(">", True, (220, 210, 230))
        surface.blit(pfeil, (rect.left + 14, cy - pfeil.get_height() // 2))

    txt_col = (230, 225, 240) if hover else (160, 155, 175)
    label   = fnt.render(text, True, txt_col)
    surface.blit(label, (cx - label.get_width() // 2, cy - label.get_height() // 2))

    return rect


def _menu_zeichnen(surface: pygame.Surface, clock_ms: int,
                   hover: int = -1) -> list[pygame.Rect]:
    # hauptmenue mit hintergrundbild und 4 buttons zeichnen
    # gibt liste der button-rects zurueck (index: 0=starten, 1=steuerung, 2=optionen, 3=beenden)

    bg = _lade_menu_bg()
    if bg:
        surface.blit(bg, (0, 0))
    else:
        surface.fill((3, 2, 5))

    # buttons zentriert im mittleren bereich des bildes
    bw   = 300   # button breite
    bh   = 48    # button hoehe
    gap  = 14    # abstand zwischen buttons
    cx   = GV.SCREEN_W // 2
    # startposition: etwas unterhalb der bildmitte (wo das bild frei ist)
    start_y = 295

    beschriftungen = ["SPIEL STARTEN", "STEUERUNG", "HIGHSCORES", "BEENDEN"]
    rects = []
    for i, lbl in enumerate(beschriftungen):
        by = start_y + i * (bh + gap)
        r  = _menu_button(surface, lbl, cx, by, bw, bh, hover == i)
        rects.append(r)

    # team-text unten
    fnt_sm = pygame.font.SysFont("monospace", 12)
    team   = fnt_sm.render(
        "Onur Guenduz & Fabian Bechter  |  HTL Rankweil 1AHIF  |  2025/26",
        True, (55, 48, 62)
    )
    surface.blit(team, (cx - team.get_width() // 2, GV.SCREEN_H - 22))

    return rects


def _steuerung_zeichnen(surface: pygame.Surface) -> None:
    # steuerungsseite als overlay ueber dem menue-hintergrund
    bg = _lade_menu_bg()
    if bg:
        surface.blit(bg, (0, 0))
    else:
        surface.fill((3, 2, 5))

    # dunkles panel in der mitte
    pw, ph = 540, 400
    px     = GV.SCREEN_W // 2 - pw // 2
    py     = GV.SCREEN_H // 2 - ph // 2

    panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
    panel.fill((6, 4, 12, 220))
    surface.blit(panel, (px, py))
    pygame.draw.rect(surface, (90, 85, 100), (px, py, pw, ph), 2)

    fnt_h  = pygame.font.SysFont("monospace", 20, bold=True)
    fnt_b  = pygame.font.SysFont("monospace", 14)
    fnt_sm = pygame.font.SysFont("monospace", 12)

    titel = fnt_h.render("STEUERUNG", True, (200, 190, 215))
    surface.blit(titel, (GV.SCREEN_W // 2 - titel.get_width() // 2, py + 18))
    pygame.draw.line(surface, (70, 65, 85),
                     (px + 24, py + 46), (px + pw - 24, py + 46), 1)

    tasten = [
        ("W / A / S / D  oder  Pfeiltasten", "Bewegen"),
        ("Maus",                              "Taschenlampe ausrichten"),
        ("F",                                 "Taschenlampe ein / aus"),
        ("SPACE",                             "Dash  (betaeubt Monster kurz)"),
        ("SHIFT  halten",                     "Schleichen"),
        ("E",                                 "Interagieren / Tür öffnen"),
        ("P  oder  ESC",                      "Pause-Menue"),
        ("F11",                               "Vollbild umschalten"),
    ]

    ty = py + 62
    for taste, erkl in tasten:
        kt = fnt_b.render(taste, True, (140, 130, 155))
        et = fnt_b.render(erkl,  True, (90, 85, 105))
        surface.blit(kt, (px + 28, ty))
        surface.blit(et, (px + 260, ty))
        ty += 28

    pygame.draw.line(surface, (70, 65, 85),
                     (px + 24, ty + 4), (px + pw - 24, ty + 4), 1)
    hint = fnt_sm.render("[ ESC ]  Zurück zum Menü", True, (70, 65, 85))
    surface.blit(hint, (GV.SCREEN_W // 2 - hint.get_width() // 2, ty + 12))


def _gefangen_screen_zeichnen(surface: pygame.Surface,
                               clock_ms: int, alpha: int) -> None:
    # roter fade-in wenn das monster den spieler kriegt
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

    sub = fnt_sm.render("ENTER - Nochmal     ESC - Menü", True, (100, 40, 40))
    surface.blit(sub, (GV.SCREEN_W // 2 - sub.get_width() // 2, GV.SCREEN_H // 2 + 40))


def _gewonnen_screen_zeichnen(surface: pygame.Surface,
                               vergangen: float,
                               clock_ms: int) -> None:
    # gewonnen-bildschirm mit zeit
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

    sub = fnt_sm.render("ENTER - Highscore     ESC - Menü", True, (60, 100, 60))
    surface.blit(sub, (GV.SCREEN_W // 2 - sub.get_width() // 2, 345))


def _namens_eingabe_zeichnen(surface: pygame.Surface,
                              name_puffer: str,
                              vergangen: float) -> None:
    # namen eingeben bevor der highscore gespeichert wird
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

    hint = fnt_sm.render("ENTER - Bestätigen     ESC - Überspringen", True, (60, 55, 65))
    surface.blit(hint, (GV.SCREEN_W // 2 - hint.get_width() // 2, 400))


class Game:
    # eine komplette spielsitzung - spieler, monster, items, kamera

    def __init__(self, schwierigkeit: str = "Einfach"):
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
        self._tropf_aktiv:  bool  = False

        master = _cfg.get("master_vol", 80)
        musik  = _cfg.get("music_vol",  55)
        sfx    = _cfg.get("sfx_vol",    80)
        self.sounds.apply_volume_settings(master, musik, sfx)

        self.sounds.start_ambient()
        self.sounds.start_monster_breathing()
        self.sounds.start_bg_music(master, musik)

    def hinweis_zeigen(self, text: str, dauer: float = 3.0) -> None:
        # kurze nachricht oben einblenden
        self._hinweis_text  = text
        self._hinweis_timer = dauer

    def update(self, events: list,
               keys: pygame.key.ScancodeWrapper,
               mx: int, my: int) -> GameState | None:
        # spiellogik einmal pro frame - gibt neuen zustand zurueck wenn noetig
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
                self.hinweis_zeigen("Monster betaeubt!", 2.0)
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
        # render-reihenfolge: welt -> zoom-skalierung -> dunkelheit -> hud -> jumpscares
        shake_x, shake_y = self.jumpscare.shake_offset
        cam_x = self._kamera.cam_x
        cam_y = self._kamera.cam_y
        zoom  = self._kamera.zoom
        vb, vh = self._kamera.view_size

        view_surf = pygame.Surface((vb, vh))
        draw_level(view_surf, cam_x, cam_y)
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

        # timer oben in der mitte
        fnt_zeit = pygame.font.SysFont("monospace", 12)
        mins     = int(self._vergangen // 60)
        sek      = int(self._vergangen % 60)
        zeit_t   = fnt_zeit.render(f"{mins:02d}:{sek:02d}", True, (80, 70, 80))
        render_surf.blit(zeit_t, (GV.SCREEN_W // 2 - zeit_t.get_width() // 2, 6))

        if not self.player.torch_on:
            fnt_f = pygame.font.SysFont("monospace", 13)
            ft = fnt_f.render("[F] Lampe ein", True, (100, 80, 80))
            render_surf.blit(ft, (GV.SCREEN_W // 2 - ft.get_width() // 2, GV.SCREEN_H - 80))

        # hinweis wenn man an der exit-tuer ist
        if self.player.near_exit:
            fnt_exit = pygame.font.SysFont("monospace", 15, bold=True)
            if self.items.all_tasks_done:
                et = fnt_exit.render("[E] Tür öffnen - Entkommen!", True, (80, 220, 80))
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

    # schwierigkeit ist fix auf "Einfach"
    gew_diff: str = "Einfach"

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
                    elif zustand == GameState.NAME_INPUT:
                        zustand = GameState.HIGHSCORE
                    elif zustand == GameState.HIGHSCORE:
                        zustand = GameState.MENU
                    elif zustand == GameState.STEUERUNG:
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
            # welchen button wird gerade gehovert? (index 0-3, -1 = keiner)
            # button-rects berechnen ohne zu zeichnen, dann einmal zeichnen
            bw, bh, gap = 300, 48, 14
            cx_m = GV.SCREEN_W // 2
            start_y_m = 295
            menu_hover = -1
            for i in range(4):
                by = start_y_m + i * (bh + gap)
                r  = pygame.Rect(cx_m - bw // 2, by - bh // 2, bw, bh)
                if r.collidepoint(rmx, rmy):
                    menu_hover = i
                    break

            btn_rects = _menu_zeichnen(render, clock_ms, menu_hover)

            # klick auswerten
            if klick and menu_hover >= 0:
                if menu_hover == 0:               # Spiel Starten
                    spiel          = Game(schwierigkeit=gew_diff)
                    gefangen_alpha = 0
                    zustand        = GameState.PLAYING
                elif menu_hover == 1:             # Steuerung
                    zustand = GameState.STEUERUNG
                elif menu_hover == 2:             # Highscores
                    zustand = GameState.HIGHSCORE
                elif menu_hover == 3:             # Beenden
                    laeuft = False

            # enter startet das spiel weiterhin (fuer tastatur-nutzer)
            for event in events:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    spiel          = Game(schwierigkeit=gew_diff)
                    gefangen_alpha = 0
                    zustand        = GameState.PLAYING

        elif zustand == GameState.STEUERUNG:
            _steuerung_zeichnen(render)
            for event in events:
                if event.type == pygame.KEYDOWN and event.key in (
                        pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
                    zustand = GameState.MENU
            if klick:
                zustand = GameState.MENU

        elif zustand == GameState.PLAYING:
            for event in events:
                if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_p):
                    zustand = GameState.PAUSED
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
            # pause-hover berechnen (0=weiter, 1=hauptmenue, 2=beenden)
            p_bw, p_bh, p_gap = 300, 48, 14
            p_cx   = GV.SCREEN_W // 2
            p_start = 310
            pause_hover = -1
            for i in range(3):
                p_by = p_start + i * (p_bh + p_gap)
                p_r  = pygame.Rect(p_cx - p_bw // 2, p_by - p_bh // 2, p_bw, p_bh)
                if p_r.collidepoint(rmx, rmy):
                    pause_hover = i
                    break

            _pause_zeichnen(render, pause_hover)

            # klick auswerten
            if klick and pause_hover >= 0:
                if pause_hover == 0:      # Weiter
                    zustand = GameState.PLAYING
                elif pause_hover == 1:    # Zurueck zum Hauptmenue
                    if spiel: spiel.sounds.stop_all()
                    spiel = None
                    zustand = GameState.MENU
                elif pause_hover == 2:    # Spiel Beenden
                    laeuft = False

            # ESC / P setzt spiel fort
            for event in events:
                if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_p):
                    zustand = GameState.PLAYING
                    break

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
            _gewonnen_screen_zeichnen(render, vergangen_win, clock_ms)

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
