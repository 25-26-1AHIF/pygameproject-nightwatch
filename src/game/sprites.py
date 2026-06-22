import math
import os
import pygame

_ASSETS_PFAD = os.path.join(os.path.dirname(__file__), "..", "assets")


def _make_surf(w: int, h: int) -> pygame.Surface:
    # leere transparente surface erstellen
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    s.fill((0, 0, 0, 0))
    return s


def _glow_circle(surf: pygame.Surface, cx: int, cy: int,
                 radius: int, color: tuple, schichten: int = 6) -> None:
    # leuchtkreis aus mehreren transparenten schichten zeichnen
    r, g, b = color[:3]
    for i in range(schichten, 0, -1):
        a   = int(200 * (i / schichten) ** 1.6)
        rad = int(radius * i / schichten)
        tmp = _make_surf(rad * 2 + 2, rad * 2 + 2)
        pygame.draw.circle(tmp, (r, g, b, a), (rad + 1, rad + 1), rad)
        surf.blit(tmp, (cx - rad - 1, cy - rad - 1))


def _lade_sheet(dateiname: str) -> pygame.Surface | None:
    # sprite-sheet aus dem assets-ordner laden (generiert es wenn noetig)
    pfad = os.path.join(_ASSETS_PFAD, dateiname)
    if not os.path.exists(pfad):
        try:
            from game.gen_sprites import generate
            generate()
        except Exception:
            pass
    try:
        return pygame.image.load(pfad).convert_alpha()
    except Exception:
        return None


class MonsterSprite:
    # laedt monster-frames aus monster_sheet.png (6 frames x 3 zustaende)
    # falls kein png vorhanden: fallback auf pygame.draw

    W      = 80
    H      = 110
    FRAMES = 6
    STATES = ["patrol", "alert", "hunt"]

    def __init__(self):
        self._frames: dict[str, list[pygame.Surface]] = {}
        self._laden_oder_bauen()

    def _laden_oder_bauen(self) -> None:
        sheet = _lade_sheet("monster_sheet.png")
        if sheet is not None:
            self._aus_sheet_extrahieren(sheet)
        else:
            self._fallback_bauen()

    def _aus_sheet_extrahieren(self, sheet: pygame.Surface) -> None:
        # alle frames aus dem sprite-sheet ausschneiden
        for si, state in enumerate(self.STATES):
            frames = []
            for fi in range(self.FRAMES):
                rect  = pygame.Rect(fi * self.W, si * self.H, self.W, self.H)
                frame = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
                frame.blit(sheet, (0, 0), rect)
                frames.append(frame)
            self._frames[state] = frames

    def _fallback_bauen(self) -> None:
        # monster-sprites mit pygame.draw zeichnen wenn kein png da ist
        for state in self.STATES:
            frames = []
            for fi in range(self.FRAMES):
                s = _make_surf(self.W, self.H)
                self._koerper_zeichnen(s, fi, state)
                frames.append(s)
            self._frames[state] = frames

    def _koerper_zeichnen(self, surf: pygame.Surface, frame: int, state: str) -> None:
        # einen einzelnen monster-frame zeichnen
        cx   = self.W // 2
        t    = frame / self.FRAMES
        wipp = math.sin(t * 2 * math.pi) * 2.5

        if state == "patrol":
            koerper_f = (16, 9, 24)
            auge_f    = (210, 30, 15)
            arm_f     = (12, 7, 18)
        elif state == "alert":
            koerper_f = (34, 14, 10)
            auge_f    = (240, 130, 15)
            arm_f     = (26, 10, 8)
        else:
            koerper_f = (55, 8, 8)
            auge_f    = (255, 50, 10)
            arm_f     = (42, 6, 6)

        shd = _make_surf(self.W, 14)
        pygame.draw.ellipse(shd, (0, 0, 0, 70), (4, 0, self.W - 8, 14))
        surf.blit(shd, (0, self.H - 14))

        bein_phase = math.sin(t * 2 * math.pi)
        for v in (-1, 1):
            lx   = cx + v * 11
            step = int(bein_phase * 9 * v)
            pygame.draw.line(surf, (*koerper_f, 220),
                             (lx, 78), (lx + step // 2, 94), 9)
            pygame.draw.line(surf, (*arm_f, 200),
                             (lx + step // 2, 94),
                             (lx + step, self.H - 4), 6)
            pygame.draw.ellipse(surf, (*arm_f, 180),
                                (lx + step - 9, self.H - 8, 18, 8))

        pygame.draw.ellipse(surf, (*koerper_f, 235), (cx - 16, 36, 32, 42))
        pygame.draw.ellipse(surf, (koerper_f[0]+12, koerper_f[1]+5, koerper_f[2]+8, 230),
                            (cx - 20, 26, 40, 29))

        arm_schw = math.sin(t * 2 * math.pi) * 18
        for v in (-1, 1):
            ax = cx + v * 20
            ay = 38
            if state == "hunt":
                ex = ax + v * 22 + int(arm_schw * v * 0.3)
                ey = 90
            else:
                ex = ax + v * 12 + int(arm_schw * v * 0.5)
                ey = 95
            mx2 = (ax * 2 + ex) // 3
            my2 = 64
            pygame.draw.line(surf, (*arm_f, 220), (ax, ay), (mx2, my2), 8)
            pygame.draw.line(surf, (*arm_f, 200), (mx2, my2), (ex, ey), 6)
            for fi in range(4):
                fa   = math.radians(-30 + fi * 20 + v * 12)
                flen = 14 if fi == 1 else 11
                fx   = int(ex + math.cos(fa) * flen)
                fy   = int(ey + math.sin(fa) * flen)
                pygame.draw.line(surf, (*arm_f, 180), (ex, ey), (fx, fy), 2)

        pygame.draw.rect(surf, (*koerper_f, 220), (cx - 5, 18, 10, 14))

        kopf_y = int(15 + wipp)
        pygame.draw.ellipse(surf, (*koerper_f, 240), (cx - 15, kopf_y - 16, 30, 32))
        pygame.draw.ellipse(surf, (*koerper_f, 230), (cx - 10, kopf_y - 22, 20, 14))

        for v in (-1, 1):
            ex = cx + v * 6
            ey = kopf_y - 3
            _glow_circle(surf, ex, ey, 5, auge_f, 6)
            pygame.draw.circle(surf, auge_f, (ex, ey), 4)
            pygame.draw.circle(surf, (5, 0, 0), (ex, ey), 2)

        if state in ("hunt", "alert"):
            mund_y = kopf_y + 8
            for ti in range(5):
                tx = cx - 9 + ti * 5
                if state == "hunt":
                    pts = [(tx, mund_y), (tx + 3, mund_y), (tx + 1, mund_y + 6)]
                    pygame.draw.polygon(surf, (215, 205, 185, 230), pts)
            pygame.draw.arc(surf, (100, 5, 5, 200),
                            (cx - 11, mund_y - 3, 22, 10),
                            math.pi * 0.1, math.pi * 0.9, 2)

        if state == "hunt":
            pr  = 32 + int(math.sin(t * math.pi * 2) * 4)
            aur = _make_surf(pr * 2 + 4, pr * 2 + 4)
            pygame.draw.circle(aur, (130, 0, 0, 38), (pr + 2, pr + 2), pr)
            surf.blit(aur, (cx - pr - 2, self.H // 2 - pr - 2))

    def draw(self, surface: pygame.Surface,
             sx: int, sy: int,
             zustand: str, frame: int, skalierung: float = 1.0) -> None:
        # monster an bildschirmposition zeichnen
        frames = self._frames.get(zustand, self._frames.get("patrol", []))
        if not frames:
            return

        bild = frames[frame % len(frames)]

        if abs(skalierung - 1.0) > 0.01:
            nw = max(1, int(self.W * skalierung))
            nh = max(1, int(self.H * skalierung))
            bild = pygame.transform.smoothscale(bild, (nw, nh))
            surface.blit(bild, (sx - nw // 2, sy - nh // 2))
        else:
            surface.blit(bild, (sx - self.W // 2, sy - self.H // 2))


class PlayerSprite:
    # laedt spieler-frames aus player_sheet.png (4 lauf + 1 idle)

    W      = 38
    H      = 38
    FRAMES = 4

    def __init__(self):
        self._lauf_frames: list[pygame.Surface] = []
        self._idle: pygame.Surface | None       = None
        self._laden_oder_bauen()

    def _laden_oder_bauen(self) -> None:
        sheet = _lade_sheet("player_sheet.png")
        if sheet is not None:
            self._aus_sheet_extrahieren(sheet)
        else:
            self._fallback_bauen()

    def _aus_sheet_extrahieren(self, sheet: pygame.Surface) -> None:
        for fi in range(self.FRAMES):
            rect  = pygame.Rect(fi * self.W, 0, self.W, self.H)
            frame = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
            frame.blit(sheet, (0, 0), rect)
            self._lauf_frames.append(frame)

        idle_rect = pygame.Rect(self.FRAMES * self.W, 0, self.W, self.H)
        idle      = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        idle.blit(sheet, (0, 0), idle_rect)
        self._idle = idle

    def _fallback_bauen(self) -> None:
        # spieler-sprites mit pygame.draw zeichnen wenn kein png da ist
        for fi in range(self.FRAMES):
            self._lauf_frames.append(self._frame_bauen(fi, True))
        self._idle = self._frame_bauen(0, False)

    def _frame_bauen(self, frame: int, bewegt: bool) -> pygame.Surface:
        s   = _make_surf(self.W, self.H)
        cx  = self.W // 2
        cy  = self.H // 2
        t   = frame / self.FRAMES if bewegt else 0
        bob = int(math.sin(t * 2 * math.pi) * 1.5) if bewegt else 0

        shd = _make_surf(self.W, 10)
        pygame.draw.ellipse(shd, (0, 0, 0, 50), (cx - 10, 0, 20, 10))
        s.blit(shd, (0, cy + 12))

        bein_schw = math.sin(t * 2 * math.pi) * 6 if bewegt else 0
        for v in (-1, 1):
            lx  = cx + v * 5
            ly  = cy + 5 + bob
            ldx = int(bein_schw * v)
            pygame.draw.line(s, (30, 28, 42, 230), (lx, ly), (lx + ldx, ly + 10), 5)
            pygame.draw.ellipse(s, (20, 18, 30, 210), (lx + ldx - 5, ly + 8, 10, 5))

        pygame.draw.ellipse(s, (38, 33, 50, 240), (cx - 10, cy - 6 + bob, 20, 14))
        pygame.draw.line(s, (25, 22, 36, 120),
                         (cx, cy - 4 + bob), (cx, cy + 5 + bob), 1)

        arm_schw = math.sin(t * 2 * math.pi) * 5 if bewegt else 0
        for v in (-1, 1):
            ax  = cx + v * 10
            ay  = cy - 1 + bob
            adx = int(arm_schw * v)
            pygame.draw.line(s, (33, 28, 44, 230),
                             (ax, ay), (ax + v * 2 + adx, ay + 8), 4)

        pygame.draw.circle(s, (195, 165, 135, 255), (cx, cy - 11 + bob), 7)
        pygame.draw.ellipse(s, (55, 38, 26, 255), (cx - 7, cy - 18 + bob, 14, 8))
        pygame.draw.ellipse(s, (220, 210, 180, 160), (cx + 4, cy - 13 + bob, 4, 3))

        return s

    def draw(self, surface: pygame.Surface,
             sx: int, sy: int, bewegt: bool, frame: int) -> None:
        # spieler an bildschirmposition zeichnen
        bild = self._lauf_frames[frame % self.FRAMES] if bewegt else self._idle
        if bild:
            surface.blit(bild, (sx - self.W // 2, sy - self.H // 2))
