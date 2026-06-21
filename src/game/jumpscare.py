import math
import random
import pygame
from game_variables.game_variables import GameVariables

GV = GameVariables

SW = GV.SCREEN_W
SH = GV.SCREEN_H


def _leuchtendes_auge(surface: pygame.Surface, cx: int, cy: int, r: int) -> None:
    """Zeichnet ein einzelnes glühend-rotes Auge mit Glow-Effekt."""
    for ring in range(r + 6, 0, -2):
        a = int(180 * (1 - ring / (r + 6)) ** 1.5)
        s = pygame.Surface((ring * 2 + 2, ring * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (255, 20, 0, a), (ring + 1, ring + 1), ring)
        surface.blit(s, (cx - ring - 1, cy - ring - 1))
    pygame.draw.circle(surface, (255, 80, 0), (cx, cy), r)
    pygame.draw.circle(surface, (5, 0, 0),   (cx, cy), max(1, r - 3))


def _monster_gesicht_zeichnen(surface: pygame.Surface,
                               cx: int, cy: int, groesse: int,
                               phase: float, seed: int = 0) -> None:
    """Zeichnet das Horror-Monster-Gesicht (Hauptelement aller Jumpscares)."""
    rng  = random.Random(seed)
    rng2 = random.Random(seed + 1)

    hg_farbe = (int(40 + phase * 60), 0, 0)
    pygame.draw.circle(surface, hg_farbe, (cx, cy), groesse)

    puls = int(groesse * (1.04 + 0.09 * math.sin(phase * math.pi * 8)))
    pygame.draw.circle(surface, (160, 8, 8),  (cx, cy), puls, 5)
    pygame.draw.circle(surface, (220, 20, 20), (cx, cy), max(1, puls - 10), 2)

    for i in range(5):
        winkel = math.radians(-80 + i * 40 + phase * 20)
        x1 = cx + int(math.cos(winkel) * groesse * 0.42)
        y1 = cy - int(groesse * 0.52)
        x2 = x1 + rng2.randint(-14, 14)
        y2 = y1 - rng2.randint(8, 22)
        pygame.draw.line(surface, (180, 30, 30), (x1, y1), (x2, y2), 2)

    auge_off_x = int(groesse * 0.30)
    auge_off_y = int(groesse * 0.12)
    auge_r     = int(groesse * 0.21)
    pupille_r  = int(groesse * 0.09 * (1.0 + phase * 1.0))

    for v in (-1, 1):
        ex = cx + v * auge_off_x
        ey = cy - auge_off_y

        pygame.draw.ellipse(surface, (220, 210, 195),
                            (ex - auge_r, ey - int(auge_r * 0.9),
                             auge_r * 2, int(auge_r * 1.6)))
        for _ in range(3):
            vx = ex + rng2.randint(-auge_r // 2, auge_r // 2)
            vy = ey + rng2.randint(-auge_r // 2, auge_r // 2)
            pygame.draw.line(surface, (200, 50, 50), (ex, ey), (vx, vy), 1)

        p_farbe = (int(200 + phase * 55), 0, 0)
        pygame.draw.circle(surface, p_farbe,   (ex, ey), pupille_r)
        pygame.draw.circle(surface, (5, 0, 0), (ex, ey), max(1, pupille_r - 2))

        tropfen = int(groesse * 0.20 * phase)
        if tropfen > 2:
            dx = rng2.randint(-4, 4)
            pygame.draw.line(surface, (160, 0, 0),
                             (ex, ey + int(auge_r * 0.7)),
                             (ex + dx, ey + int(auge_r * 0.7) + tropfen), 3)

    nasen_y = cy + int(groesse * 0.08)
    for v in (-1, 1):
        nx = cx + v * int(groesse * 0.09)
        pygame.draw.ellipse(surface, (15, 0, 0), (nx - 8, nasen_y - 6, 16, 11))

    mund_y = cy + int(groesse * 0.36)
    mw     = int(groesse * 0.72)
    th     = int(groesse * 0.13)
    tn     = 8
    tw     = mw // tn

    pygame.draw.arc(surface, (80, 8, 8),
                    (cx - mw // 2, mund_y - th, mw, th * 2),
                    math.pi, 2 * math.pi, 5)

    for i in range(tn):
        tx = cx - mw // 2 + i * tw
        ty = mund_y
        if i % 2 == 0:
            pts = [(tx, ty), (tx + tw, ty), (tx + tw // 2, ty + th)]
        else:
            pts = [(tx, ty), (tx + tw, ty), (tx + tw // 2, ty - th + 5)]
        pygame.draw.polygon(surface, (215, 205, 185), pts)
        pygame.draw.polygon(surface, (70, 0, 0), pts, 1)

    if phase > 0.4:
        for _ in range(3):
            bx   = cx + rng2.randint(-mw // 3, mw // 3)
            by   = mund_y + int(th * 0.5)
            blen = int(rng2.randint(15, 40) * phase)
            pygame.draw.line(surface, (140, 0, 0),
                             (bx, by), (bx + rng2.randint(-6, 6), by + blen), 3)


def _wand_gesicht_zeichnen(surface: pygame.Surface,
                            cx: int, cy: int,
                            phase: float, seite: str = "left") -> None:
    """Gesicht erscheint langsam aus einem Wandriss."""
    if phase <= 0.5:
        enthuellung = phase / 0.5
    else:
        enthuellung = 1.0 - (phase - 0.5) / 0.5

    groesse = int(50 * enthuellung)
    if groesse < 5:
        return

    riss_farbe = (40, 5, 5)

    if seite == "left":
        riss_x = cx - int(60 * enthuellung)
        for i in range(8):
            rx = riss_x - i * 4
            ry = cy + (i % 2) * 6 - 3
            pygame.draw.line(surface, riss_farbe, (rx, ry - 30), (rx, ry + 30), 3)
        pygame.draw.circle(surface, (18, 8, 20),
                           (cx - int(groesse * 0.3), cy), groesse,
                           draw_top_right=True, draw_bottom_right=True)
        _leuchtendes_auge(surface, cx - int(groesse * 0.1), cy - groesse // 5, 6)

    elif seite == "right":
        riss_x = cx + int(60 * enthuellung)
        for i in range(8):
            rx = riss_x + i * 4
            ry = cy + (i % 2) * 6 - 3
            pygame.draw.line(surface, riss_farbe, (rx, ry - 30), (rx, ry + 30), 3)
        pygame.draw.circle(surface, (18, 8, 20),
                           (cx + int(groesse * 0.3), cy), groesse,
                           draw_top_left=True, draw_bottom_left=True)
        _leuchtendes_auge(surface, cx + int(groesse * 0.1), cy - groesse // 5, 6)

    else:
        for i in range(8):
            ry = cy - int(60 * enthuellung) - i * 4
            rx = cx + (i % 2) * 6 - 3
            pygame.draw.line(surface, riss_farbe, (rx - 30, ry), (rx + 30, ry), 3)
        pygame.draw.circle(surface, (18, 8, 20),
                           (cx, cy - int(groesse * 0.3)), groesse,
                           draw_bottom_left=True, draw_bottom_right=True)
        _leuchtendes_auge(surface, cx, cy - int(groesse * 0.5), 6)


def _haengende_figur_zeichnen(surface: pygame.Surface,
                               cx: int, phase: float) -> None:
    """Figur fällt von der Decke ins Bild."""
    if phase < 0.2:
        fall_y = int(-80 + (phase / 0.2) * 180)
    else:
        fall_y = 100

    kopf_y = fall_y + 10

    pygame.draw.line(surface, (50, 40, 30), (cx, 0), (cx, kopf_y - 10), 3)

    pygame.draw.circle(surface, (15, 10, 18), (cx, kopf_y), 20)
    for v in (-1, 1):
        ex = cx + v * 7
        pygame.draw.ellipse(surface, (220, 200, 180), (ex - 6, kopf_y - 6, 12, 10))
        pygame.draw.circle(surface, (0, 0, 0), (ex, kopf_y - 1), 4)
        pygame.draw.ellipse(surface, (180, 0, 0), (ex - 6, kopf_y - 6, 12, 10), 1)

    pygame.draw.rect(surface, (12, 8, 15), (cx - 10, kopf_y + 18, 20, 80))

    for v in (-1, 1):
        ax = cx + v * 10
        ay = kopf_y + 28
        pygame.draw.line(surface, (10, 6, 12),
                         (ax, ay), (ax + v * 20, ay + 50), 5)
        for fi in range(3):
            fa = math.radians(60 * fi + 30 * v)
            fx = ax + v * 20 + int(math.cos(fa) * 12)
            fy = ay + 50 + int(math.sin(fa) * 8)
            pygame.draw.line(surface, (8, 4, 10),
                             (ax + v * 20, ay + 50), (fx, fy), 2)


def _schatten_rush_zeichnen(surface: pygame.Surface,
                              phase: float, richtung: int = 1) -> None:
    """Dunkle Schattenfigur rast horizontal durchs Bild."""
    if richtung == 1:
        x = int(-120 + phase * (SW + 240))
    else:
        x = int(SW + 120 - phase * (SW + 240))

    w = 90

    schatten = pygame.Surface((w + 80, SH), pygame.SRCALPHA)
    fcx = w // 2
    fcy = SH // 2

    pygame.draw.ellipse(schatten, (5, 3, 7, 200), (fcx - 20, fcy - 60, 40, 120))
    pygame.draw.circle(schatten, (5, 3, 7, 200), (fcx, fcy - 70), 28)

    off_dir = -30 * richtung
    pygame.draw.line(schatten, (5, 3, 7, 160),
                     (fcx, fcy - 30), (fcx + off_dir - 30, fcy + 20), 8)
    pygame.draw.line(schatten, (5, 3, 7, 160),
                     (fcx, fcy - 30), (fcx + off_dir + 30, fcy + 20), 8)

    for blur in range(1, 6):
        bx    = blur * 18 * (-richtung)
        geist = schatten.copy()
        geist.set_alpha(max(0, 80 - blur * 15))
        surface.blit(geist, (x + bx, 0))

    surface.blit(schatten, (x, 0))


class JumpscareEffect:
    """Ein einzelner Jumpscare-Ablauf (12 Typen verfügbar)."""

    TYP_HUNT        = "hunt"
    TYP_GEFANGEN    = "caught"
    TYP_RAUM_R3     = "room_r3"
    TYP_WANDGESICHT = "wall_face"
    TYP_HAENGEND    = "hanging"
    TYP_SCHATTEN    = "shadow"
    TYP_BLACKOUT    = "blackout"
    TYP_ECKE        = "corner_peek"
    TYP_GLITCH      = "glitch"
    TYP_STROBE      = "strobe"
    TYP_HINTER_DIR  = "behind_you"
    TYP_STATIC      = "static_face"

    def __init__(self, typ: str = "hunt",
                 spieler_sx: int = SW // 2,
                 spieler_sy: int = SH // 2):
        self.effect_type = typ
        self.player_sx   = spieler_sx
        self.player_sy   = spieler_sy
        self.timer: int  = 0
        self.active: bool = True

        self._shake_x: int = 0
        self._shake_y: int = 0

        self._schatten_richtung = random.choice((-1, 1))
        self._wand_seite        = random.choice(("left", "right", "top"))
        self._gesicht_seed      = random.randint(0, 999)

        dauer_map = {
            "hunt":        GV.JUMPSCARE_DAUER,
            "caught":      GV.JUMPSCARE_DAUER + 40,
            "room_r3":     GV.JUMPSCARE_DAUER - 10,
            "wall_face":   50,
            "hanging":     70,
            "shadow":      35,
            "blackout":    200,
            "corner_peek": 45,
            "glitch":      80,
            "strobe":      60,
            "behind_you":  120,
            "static_face": 90,
        }
        self.duration = dauer_map.get(typ, GV.JUMPSCARE_DAUER)

    @property
    def shake_offset(self) -> tuple[int, int]:
        """Aktueller Screenshake-Versatz in Pixeln."""
        return (self._shake_x, self._shake_y)

    def update(self) -> None:
        """Aktualisiert den Timer und den Screenshake."""
        if not self.active:
            return
        self.timer += 1

        shake_typen = {"hunt", "caught", "room_r3", "wall_face"}
        if self.effect_type in shake_typen and self.timer < GV.SHAKE_DAUER:
            abklingen = 1.0 - self.timer / GV.SHAKE_DAUER
            amp = int(GV.SHAKE_AMPLITUDE * abklingen)
            self._shake_x = random.randint(-amp, amp)
            self._shake_y = random.randint(-amp, amp)
        else:
            self._shake_x = 0
            self._shake_y = 0

        if self.timer >= self.duration:
            self.active = False

    def draw(self, surface: pygame.Surface) -> None:
        if not self.active:
            return

        phase = self.timer / self.duration

        if self.effect_type in ("hunt", "caught", "room_r3"):
            self._gesicht_jumpscare(surface, phase)
        elif self.effect_type == "wall_face":
            self._wand_jumpscare(surface, phase)
        elif self.effect_type == "hanging":
            self._haengen_jumpscare(surface, phase)
        elif self.effect_type == "shadow":
            _schatten_rush_zeichnen(surface, phase, self._schatten_richtung)
        elif self.effect_type == "blackout":
            self._blackout_jumpscare(surface, phase)
        elif self.effect_type == "corner_peek":
            self._ecken_jumpscare(surface, phase)
        elif self.effect_type == "glitch":
            self._glitch_jumpscare(surface, phase)
        elif self.effect_type == "strobe":
            self._strobe_jumpscare(surface, phase)
        elif self.effect_type == "behind_you":
            self._hinter_dir_jumpscare(surface, phase)
        elif self.effect_type == "static_face":
            self._static_face_jumpscare(surface, phase)

    def _gesicht_jumpscare(self, surface: pygame.Surface, phase: float) -> None:
        """Klassischer Gesichts-Jumpscare mit Blitz und Screenshake."""
        if self.timer < GV.BLITZ_DAUER:
            alpha = int(255 * (1.0 - self.timer / GV.BLITZ_DAUER))
            farbe = (255, 255, 255) if self.timer < GV.BLITZ_DAUER // 2 else (255, 30, 30)
            fs = pygame.Surface((SW, SH))
            fs.fill(farbe)
            fs.set_alpha(alpha)
            surface.blit(fs, (0, 0))
            return

        fp = (phase - GV.BLITZ_DAUER / self.duration) / \
             max(0.001, 1.0 - GV.BLITZ_DAUER / self.duration)
        fp = max(0.0, min(1.0, fp))

        ov = pygame.Surface((SW, SH))
        ov.fill((0, 0, 0))
        ov.set_alpha(int(min(230, 100 + fp * 130)))
        surface.blit(ov, (0, 0))

        if fp < 0.55:
            groesse = int(30 + fp / 0.55 * 240)
        else:
            groesse = int(270 - (fp - 0.55) / 0.45 * 70)
        groesse = max(8, groesse)

        cx = SW // 2
        cy = SH // 2
        if self.effect_type != "caught":
            jitter = int(18 * (1 - fp))
            cx += random.randint(-jitter, jitter)
            cy += random.randint(-jitter, jitter)

        _monster_gesicht_zeichnen(surface, cx, cy, groesse, fp, self._gesicht_seed)

        if self.effect_type == "caught" and fp > 0.3:
            self._blut_raender(surface, fp)
        self._rote_vignette(surface, fp)

    def _wand_jumpscare(self, surface: pygame.Surface, phase: float) -> None:
        """Gesicht erscheint aus einem Wandriss."""
        if self.timer < 6:
            fs = pygame.Surface((SW, SH))
            fs.fill((255, 255, 255))
            fs.set_alpha(int(200 * (1 - self.timer / 6)))
            surface.blit(fs, (0, 0))

        wand_x = random.Random(self._gesicht_seed).randint(80, SW - 80)
        wand_y = random.Random(self._gesicht_seed + 1).randint(80, SH - 80)

        _wand_gesicht_zeichnen(surface, wand_x, wand_y, phase, self._wand_seite)
        self._rote_vignette(surface, min(1.0, phase * 3))

    def _haengen_jumpscare(self, surface: pygame.Surface, phase: float) -> None:
        """Hängende Figur fällt von der Decke."""
        ov = pygame.Surface((SW, SH))
        ov.fill((0, 0, 0))
        ov.set_alpha(140)
        surface.blit(ov, (0, 0))

        cx = random.Random(self._gesicht_seed).randint(SW // 4, 3 * SW // 4)
        _haengende_figur_zeichnen(surface, cx, phase)

        if phase < 0.15:
            fs = pygame.Surface((SW, SH))
            fs.fill((255, 255, 255))
            fs.set_alpha(int(180 * (1 - phase / 0.15)))
            surface.blit(fs, (0, 0))
        self._rote_vignette(surface, phase * 0.7)

    def _blackout_jumpscare(self, surface: pygame.Surface, phase: float) -> None:
        """Komplettes Schwarzbild mit kurzem Aufflackern in der Mitte."""
        if phase < 0.1 or phase > 0.9:
            alpha = int(255 * (1 - abs(phase - 0.5) * 2))
        else:
            alpha = 255

        ov = pygame.Surface((SW, SH))
        ov.fill((0, 0, 0))
        ov.set_alpha(max(0, alpha))
        surface.blit(ov, (0, 0))

        if 0.45 < phase < 0.55:
            sub_phase = (phase - 0.45) / 0.10
            groesse   = int(80 * math.sin(sub_phase * math.pi))
            if groesse > 5:
                cx = SW // 2 + random.randint(-30, 30)
                cy = SH // 2 + random.randint(-30, 30)
                _monster_gesicht_zeichnen(surface, cx, cy, groesse, sub_phase)

    def _ecken_jumpscare(self, surface: pygame.Surface, phase: float) -> None:
        """Kreatur lugt kurz um eine Bildschirmecke."""
        ecken_x = (0 if random.Random(self._gesicht_seed).random() > 0.5
                   else SW)
        ecken_y = SH // 2

        enthuellung = (phase / 0.5
                       if phase < 0.5
                       else 1.0 - (phase - 0.5) / 0.5)

        groesse = int(40 * enthuellung)
        if groesse < 4:
            return

        seite = "right" if ecken_x == 0 else "left"
        _wand_gesicht_zeichnen(surface, ecken_x, ecken_y, phase, seite)

    def _glitch_jumpscare(self, surface: pygame.Surface, phase: float) -> None:
        """Bildschirm-Glitch bricht auf, danach Gesicht."""
        rng = random.Random(self._gesicht_seed + int(self.timer))

        if phase < 0.65:
            n_streifen = 12
            for i in range(n_streifen):
                y1  = i * (SH // n_streifen)
                y2  = y1 + SH // n_streifen
                dx  = rng.randint(-60, 60)
                col = (rng.randint(0, 30), rng.randint(0, 5), rng.randint(0, 8))
                bar = pygame.Surface((SW, y2 - y1), pygame.SRCALPHA)
                bar.fill((*col, rng.randint(80, 180)))
                surface.blit(bar, (dx, y1))

            for _ in range(rng.randint(3, 8)):
                ly = rng.randint(0, SH)
                pygame.draw.line(surface, (200, 0, 0, 120),
                                 (0, ly), (SW, ly), rng.randint(1, 4))

        if 0.30 < phase < 0.85:
            sub     = (phase - 0.30) / 0.55
            groesse = int(20 + sub * 240)
            cx = SW // 2 + rng.randint(-20, 20)
            cy = SH // 2 + rng.randint(-15, 15)
            _monster_gesicht_zeichnen(surface, cx, cy,
                                      max(8, groesse), sub, self._gesicht_seed)

        self._rote_vignette(surface, min(1.0, phase * 2))

    def _strobe_jumpscare(self, surface: pygame.Surface, phase: float) -> None:
        """Stroboskop-Blitze mit Monster-Gesicht in Dunkelphasen."""
        strobe_an = (self.timer // 5) % 2 == 0

        if strobe_an and phase < 0.8:
            abklingen = int(255 * (1 - phase / 0.8) * 0.85)
            fs = pygame.Surface((SW, SH))
            fs.fill((255, 255, 255))
            fs.set_alpha(abklingen)
            surface.blit(fs, (0, 0))
        else:
            ov = pygame.Surface((SW, SH))
            ov.fill((0, 0, 0))
            ov.set_alpha(140)
            surface.blit(ov, (0, 0))

            if 0.15 < phase < 0.85:
                cx      = SW // 2
                cy      = SH // 2
                groesse = int(60 + phase * 200)
                _monster_gesicht_zeichnen(surface, cx, cy,
                                          max(8, groesse), phase, self._gesicht_seed)

        self._rote_vignette(surface, phase * 0.6)

    def _hinter_dir_jumpscare(self, surface: pygame.Surface, phase: float) -> None:
        """„HINTER DIR"-Text, dann Gesicht direkt hinter dem Spieler."""
        if phase < 0.40:
            sub = phase / 0.40
            ov  = pygame.Surface((SW, SH))
            ov.fill((0, 0, 0))
            ov.set_alpha(int(200 * sub))
            surface.blit(ov, (0, 0))

            if sub > 0.1:
                font_gr   = pygame.font.SysFont("monospace", 72, bold=True)
                jitter    = int(8 * (1 - sub))
                txt_farbe = (int(200 + sub * 55), 0, 0)
                for off in range(5, 0, -1):
                    schatten = font_gr.render("HINTER DIR!", True, (off * 8, 0, 0))
                    surface.blit(schatten,
                                 (SW // 2 - schatten.get_width() // 2 + off,
                                  SH // 2 - 50 + off))
                txt = font_gr.render("HINTER DIR!", True, txt_farbe)
                dx  = random.randint(-jitter, jitter)
                dy  = random.randint(-jitter, jitter)
                surface.blit(txt, (SW // 2 - txt.get_width() // 2 + dx,
                                   SH // 2 - 50 + dy))
        else:
            sub     = (phase - 0.40) / 0.60
            groesse = int(10 + sub * 280)
            ov = pygame.Surface((SW, SH))
            ov.fill((0, 0, 0))
            ov.set_alpha(int(min(220, 120 + sub * 100)))
            surface.blit(ov, (0, 0))

            cx = self.player_sx
            cy = self.player_sy
            _monster_gesicht_zeichnen(surface, cx, cy,
                                      max(8, groesse), sub, self._gesicht_seed)

        self._rote_vignette(surface, min(1.0, phase * 1.8))

    def _static_face_jumpscare(self, surface: pygame.Surface, phase: float) -> None:
        """TV-Rauschen mit Monster-Gesicht das durchschimmert."""
        rng = random.Random(self._gesicht_seed + self.timer)

        rauschen = pygame.Surface((SW, SH), pygame.SRCALPHA)
        block = 4
        for bx in range(0, SW, block):
            for by in range(0, SH, block):
                v = rng.randint(0, 120)
                a = rng.randint(40, 160)
                rauschen.fill((v, v, v, a), (bx, by, block, block))

        fade_ein = min(1.0, phase * 3)
        fade_aus = (max(0.0, 1.0 - (phase - 0.7) / 0.3)
                    if phase > 0.7 else 1.0)
        gesicht_alpha = int(fade_ein * fade_aus * 255)

        if gesicht_alpha > 10:
            gesicht_surf = pygame.Surface((SW, SH), pygame.SRCALPHA)
            groesse = int(60 + phase * 200)
            cx      = SW // 2
            cy      = SH // 2
            _monster_gesicht_zeichnen(gesicht_surf, cx, cy,
                                      max(8, groesse), phase, self._gesicht_seed)
            gesicht_surf.set_alpha(gesicht_alpha)
            surface.blit(gesicht_surf, (0, 0))

        rauschen_alpha = int(180 * (1 - max(0.0, phase - 0.6) / 0.4))
        rauschen.set_alpha(max(0, rauschen_alpha))
        surface.blit(rauschen, (0, 0))

        self._rote_vignette(surface, phase * 0.8)

    def _rote_vignette(self, surface: pygame.Surface, intensitaet: float) -> None:
        """Rote Horror-Vignette an den Bildrändern."""
        if intensitaet <= 0:
            return
        vig   = pygame.Surface((SW, SH), pygame.SRCALPHA)
        alpha = int(60 + intensitaet * 120)
        puls  = int(20 * math.sin(self.timer / 8))
        rand  = int(100 + puls)
        for i in range(0, rand, 14):
            a = max(0, int(alpha * (1 - i / rand) ** 1.3))
            pygame.draw.rect(vig, (200, 0, 0, a),
                             (i, i, SW - 2 * i, SH - 2 * i), 14)
        surface.blit(vig, (0, 0))

    def _blut_raender(self, surface: pygame.Surface, phase: float) -> None:
        """Blutspritzer an den Bildschirmrändern (für CAUGHT-Zustand)."""
        random.seed(42)
        for _ in range(20):
            seite = random.randint(0, 3)
            if   seite == 0: x, y = random.randint(0, SW),         random.randint(0, 90)
            elif seite == 1: x, y = random.randint(0, SW),         random.randint(SH - 90, SH)
            elif seite == 2: x, y = random.randint(0, 90),          random.randint(0, SH)
            else:             x, y = random.randint(SW - 90, SW),   random.randint(0, SH)
            r    = int(random.randint(8, 30) * phase)
            tlen = int(random.randint(10, 45) * phase)
            pygame.draw.circle(surface, (140, 0, 0), (x, y), max(1, r))
            pygame.draw.line(surface, (110, 0, 0),
                             (x, y), (x + random.randint(-6, 6), y + tlen), 3)
        random.seed()


class JumpscareManager:
    """Verwaltet alle Jumpscares – Monster-getriggert und zufällige Horrorevents."""

    def __init__(self, sounds):
        self._sounds   = sounds
        self._aktuell: JumpscareEffect | None = None
        self._cooldown: int = 0

        self._zufalls_timer: int = random.randint(600, 1800)

        self._typen_pool = [
            JumpscareEffect.TYP_WANDGESICHT,
            JumpscareEffect.TYP_HAENGEND,
            JumpscareEffect.TYP_SCHATTEN,
            JumpscareEffect.TYP_BLACKOUT,
            JumpscareEffect.TYP_ECKE,
            JumpscareEffect.TYP_GLITCH,
            JumpscareEffect.TYP_STROBE,
            JumpscareEffect.TYP_HINTER_DIR,
            JumpscareEffect.TYP_STATIC,
            JumpscareEffect.TYP_SCHATTEN,
            JumpscareEffect.TYP_WANDGESICHT,
            JumpscareEffect.TYP_GLITCH,
            JumpscareEffect.TYP_STROBE,
        ]

    @property
    def active(self) -> bool:
        """True wenn ein Jumpscare gerade läuft."""
        return self._aktuell is not None and self._aktuell.active

    @property
    def shake_offset(self) -> tuple[int, int]:
        """Aktueller Screenshake-Versatz."""
        if self._aktuell and self._aktuell.active:
            return self._aktuell.shake_offset
        return (0, 0)

    @property
    def is_blackout(self) -> bool:
        """True wenn gerade Blackout-Jumpscare läuft."""
        return (self._aktuell is not None
                and self._aktuell.active
                and self._aktuell.effect_type == JumpscareEffect.TYP_BLACKOUT)

    def trigger(self, typ: str,
                spieler_sx: int = SW // 2,
                spieler_sy: int = SH // 2) -> None:
        """Startet einen Jumpscare des angegebenen Typs."""
        if self._cooldown > 0:
            return
        if self._aktuell and self._aktuell.active:
            if typ not in (JumpscareEffect.TYP_HUNT, JumpscareEffect.TYP_GEFANGEN):
                return

        self._aktuell  = JumpscareEffect(typ, spieler_sx, spieler_sy)
        self._cooldown = 240

        if self._sounds:
            sound_map = {
                JumpscareEffect.TYP_HUNT:        "jumpscare",
                JumpscareEffect.TYP_GEFANGEN:    "jumpscare",
                JumpscareEffect.TYP_RAUM_R3:     "jumpscare",
                JumpscareEffect.TYP_WANDGESICHT: "wall_creak",
                JumpscareEffect.TYP_HAENGEND:    "hanging_drop",
                JumpscareEffect.TYP_SCHATTEN:    "shadow_rush",
                JumpscareEffect.TYP_BLACKOUT:    "blackout_sound",
                JumpscareEffect.TYP_ECKE:        "wall_creak",
                JumpscareEffect.TYP_GLITCH:      "jumpscare",
                JumpscareEffect.TYP_STROBE:      "jumpscare",
                JumpscareEffect.TYP_HINTER_DIR:  "jumpscare",
                JumpscareEffect.TYP_STATIC:      "blackout_sound",
            }
            snd = sound_map.get(typ, "jumpscare")
            self._sounds.play(snd)

    def update(self, spiel_laeuft: bool = True) -> None:
        """Aktualisiert Cooldown, aktiven Jumpscare und zufällige Events."""
        if self._cooldown > 0:
            self._cooldown -= 1
        if self._aktuell:
            self._aktuell.update()

        if not spiel_laeuft:
            return

        self._zufalls_timer -= 1
        if self._zufalls_timer <= 0:
            self._zufalls_timer = random.randint(480, 1440)
            if not self.active:
                typ = random.choice(self._typen_pool)
                self.trigger(typ)

    def draw(self, surface: pygame.Surface) -> None:
        """Zeichnet den aktuellen Jumpscare."""
        if self._aktuell and self._aktuell.active:
            self._aktuell.draw(surface)
