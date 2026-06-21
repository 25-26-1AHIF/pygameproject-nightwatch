import math
import random
import pygame
from game_variables.game_variables import GameVariables

SW    = GameVariables.SCREEN_W
SH    = GameVariables.SCREEN_H
TL    = GameVariables.LAMPE_LAENGE
TA    = GameVariables.LAMPE_WINKEL

DUNKEL_AUSSEN = 252
DUNKEL_INNEN  = 215
DUNKEL_GANG   = 240


class Lighting:
    """Beleuchtungs-system: taschenlampe, kerzen, filmkorn, vignette."""

    def __init__(self):
        self._dark = pygame.Surface((SW, SH), pygame.SRCALPHA)
        self._dark_size = (SW, SH)

        # filmkorn-frames vorberechnen damit es schnell geht
        self._grain_frames: list[pygame.Surface] = []
        self._grain_idx: int = 0
        self._filmkorn_erstellen()

        # taschenlampe flackert manchmal kurz aus
        self._flicker_timer: int  = 0
        self._flicker_aus:   bool = False
        self._flicker_next:  int  = random.randint(180, 600)

        self._kerzen_radius: int = 65

    # KI CODE ANFANG
    # Claude Opus 4.8
    # Prompt: "Erstelle 8 vorberechnete Film-Grain-Surfaces mit numpy für pygame.
    # Jeder Frame soll zufällige RGB-Werte (0-20) und zufällige Alpha-Werte (0-26)
    # haben. Nutze pygame.surfarray.blit_array und transponiere das Array korrekt
    # (Spalten/Zeilen-Reihenfolge). Bei Import-Fehler Fallback ohne Grain."
    def _filmkorn_erstellen(self) -> None:
        """Generiert 8 Filmkorn-Surfaces via numpy (Fallback: leere Surfaces)."""
        try:
            import numpy as np
            for _ in range(8):
                s   = pygame.Surface((SW, SH), pygame.SRCALPHA)
                arr = np.random.randint(0, 20, (SH, SW, 1), dtype=np.uint8)
                rgba = np.concatenate(
                    [arr, arr, arr,
                     np.random.randint(0, 26, (SH, SW, 1), dtype=np.uint8)],
                    axis=2
                )
                pygame.surfarray.blit_array(s, rgba.transpose(1, 0, 2))
                self._grain_frames.append(s)
        except Exception:
            for _ in range(2):
                s = pygame.Surface((SW, SH), pygame.SRCALPHA)
                s.fill((0, 0, 0, 0))
                self._grain_frames.append(s)
    # KI CODE ENDE

    def update(self) -> None:
        """Aktualisiert Flackerstatus und Filmkorn-Index einmal pro Frame."""
        self._grain_idx = (self._grain_idx + 1) % len(self._grain_frames)

        self._flicker_timer += 1
        if self._flicker_timer >= self._flicker_next:
            self._flicker_aus   = True
            self._flicker_timer = 0
            self._flicker_next  = random.randint(300, 900)
        elif self._flicker_aus and self._flicker_timer >= random.randint(3, 8):
            self._flicker_aus = False

    def draw_world(self,
                   surface: pygame.Surface,
                   player_sx: float, player_sy: float,
                   torch_angle: float,
                   battery: float,
                   torch_on: bool,
                   current_room,
                   candle_positions: list[tuple[float, float]],
                   cam_x: int, cam_y: int) -> None:
        """Zeichnet die Dunkelheitsmaske auf die View-Surface."""
        sw, sh = surface.get_size()

        if self._dark_size != (sw, sh):
            self._dark = pygame.Surface((sw, sh), pygame.SRCALPHA)
            self._dark_size = (sw, sh)

        self._dark.fill((0, 0, 0, 255))

        zoom     = SW / sw
        fackel_l = int(TL / zoom)

        if current_room is not None:
            raum_r    = current_room.rect.move(-cam_x, -cam_y)
            erweitert = raum_r.inflate(22, 22)
            pygame.draw.rect(self._dark, (0, 0, 0, DUNKEL_INNEN), erweitert, border_radius=6)
            pygame.draw.rect(self._dark, (0, 0, 0, DUNKEL_INNEN - 22), raum_r, border_radius=4)

        for wx, wy in candle_positions:
            sx = wx - cam_x
            sy = wy - cam_y
            r_scaled = int(self._kerzen_radius / zoom)
            self._kerzenlicht_zeichnen(sx, sy, r_scaled)

        fackel_aktiv = torch_on and not self._flicker_aus and battery > 0
        if fackel_aktiv:
            akku_ratio = battery / 100.0
            laenge     = int(fackel_l * akku_ratio)
            flicker_a  = random.randint(0, 8)
            self._lichtkegel_zeichnen(player_sx, player_sy, torch_angle, laenge, flicker_a)
        else:
            pygame.draw.circle(self._dark, (0, 0, 0, 180),
                               (int(player_sx), int(player_sy)), 18)

        surface.blit(self._dark, (0, 0))

    def draw_overlay(self, surface: pygame.Surface) -> None:
        """Zeichnet Filmkorn und Vignette auf den fertigen Frame."""
        if self._grain_frames:
            surface.blit(self._grain_frames[self._grain_idx], (0, 0))
        self._vignette_zeichnen(surface)

    def draw(self, surface, player_sx, player_sy, torch_angle,
             battery, torch_on, current_room, candle_positions, cam_x, cam_y):
        """Kombinations-Methode für Abwärtskompatibilität."""
        self.draw_world(surface, player_sx, player_sy, torch_angle, battery,
                        torch_on, current_room, candle_positions, cam_x, cam_y)
        self.draw_overlay(surface)

    # KI CODE ANFANG
    # Claude Opus 4.8
    # Prompt: "Berechne die Eckpunkte eines Taschenlampen-Lichtkegels als Polygon
    # für pygame. Der Kegel geht vom Mittelpunkt (cx,cy) aus, zeigt in Richtung
    # angle_deg und hat den halben Öffnungswinkel TORCH_ANGLE. Teile den Bogen
    # in 30 Segmente auf. Zeichne das Polygon auf eine SRCALPHA-Surface mit
    # Alpha=0 (transparent = beleuchtet)."
    def _lichtkegel_zeichnen(self, cx: float, cy: float,
                              angle_deg: float, laenge: int,
                              extra_alpha: int = 0) -> None:
        """Zeichnet den Lichtkegel der Taschenlampe als Polygon."""
        halb     = TA
        segmente = 30
        start    = math.radians(angle_deg - halb)
        ende     = math.radians(angle_deg + halb)
        schritt  = (ende - start) / segmente

        punkte = [(cx, cy)]
        for i in range(segmente + 1):
            a  = start + i * schritt
            px = cx + math.cos(a) * laenge
            py = cy + math.sin(a) * laenge
            punkte.append((px, py))

        alpha = max(0, extra_alpha)
        pygame.draw.polygon(self._dark, (0, 0, 0, alpha), punkte)
        pygame.draw.circle(self._dark, (0, 0, 0, 0), (int(cx), int(cy)), 24)
    # KI CODE ENDE

    def _kerzenlicht_zeichnen(self, sx: float, sy: float, radius: int | None = None) -> None:
        """Zeichnet einen weichen Kerzen-Lichthof durch mehrere überlagerte Kreise."""
        r = radius if radius is not None else self._kerzen_radius
        for ring in range(r, 0, -6):
            alpha = max(0, DUNKEL_INNEN - int(
                (DUNKEL_INNEN + 10) * (1 - ring / r) ** 1.4
            ))
            pygame.draw.circle(self._dark, (0, 0, 0, alpha), (int(sx), int(sy)), ring)

    def _vignette_zeichnen(self, surface: pygame.Surface) -> None:
        """Dunkle Horror-Vignette an den Bildschirmrändern."""
        sw, sh = surface.get_size()
        vig    = pygame.Surface((sw, sh), pygame.SRCALPHA)
        rand   = 200
        for i in range(0, rand, 18):
            alpha = int(145 * (1 - i / rand) ** 2.2)
            if alpha > 0:
                pygame.draw.rect(vig, (0, 0, 0, alpha),
                                 (i, i, sw - 2 * i, sh - 2 * i), 18)
        surface.blit(vig, (0, 0))
