import random
import pygame
from game_variables.game_variables import GameVariables

GV = GameVariables

SW = GV.SCREEN_W
SH = GV.SCREEN_H

# wie stark und wie lang der bildschirm wackelt
SHAKE_AMP  = 6    # maximale verschiebung in pixeln (war 18)
SHAKE_DAUER = 25  # frames lang wackeln (war 60)


class JumpscareEffect:
    # ein jumpscare-ablauf: kurzer blitz + dunkles overlay + minimal shake

    TYP_HUNT     = "hunt"
    TYP_GEFANGEN = "caught"
    TYP_RAUM_R3  = "room_r3"

    def __init__(self, typ: str = "hunt",
                 spieler_sx: int = SW // 2,
                 spieler_sy: int = SH // 2):
        self.effect_type = typ
        self.timer:  int  = 0
        self.active: bool = True

        self._shake_x: int = 0
        self._shake_y: int = 0

        # caught laeuft etwas laenger damit der uebergang funktioniert
        self.duration = 55 if typ == "caught" else 38

    @property
    def shake_offset(self) -> tuple[int, int]:
        return (self._shake_x, self._shake_y)

    def update(self) -> None:
        if not self.active:
            return
        self.timer += 1

        # shake nur in den ersten frames, dann abklingen
        if self.timer < SHAKE_DAUER:
            abklingen = 1.0 - self.timer / SHAKE_DAUER
            amp = int(SHAKE_AMP * abklingen)
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

        # erster teil: weisser blitz
        if self.timer < 8:
            alpha = int(220 * (1.0 - self.timer / 8))
            fs = pygame.Surface((SW, SH))
            fs.fill((255, 255, 255))
            fs.set_alpha(alpha)
            surface.blit(fs, (0, 0))
            return

        # zweiter teil: dunkles rotes overlay das langsam verblasst
        abklingen = max(0.0, 1.0 - phase)
        ov = pygame.Surface((SW, SH))
        ov.fill((20, 0, 0))
        ov.set_alpha(int(160 * abklingen))
        surface.blit(ov, (0, 0))

        # dezente rote vignette an den raendern
        if phase < 0.6:
            vig = pygame.Surface((SW, SH), pygame.SRCALPHA)
            a   = int(80 * (1 - phase / 0.6))
            for i in range(0, 80, 16):
                ia = max(0, int(a * (1 - i / 80)))
                pygame.draw.rect(vig, (180, 0, 0, ia),
                                 (i, i, SW - 2*i, SH - 2*i), 16)
            surface.blit(vig, (0, 0))


class JumpscareManager:
    # startet und verwaltet jumpscares

    def __init__(self, sounds):
        self._sounds   = sounds
        self._aktuell: JumpscareEffect | None = None
        self._cooldown: int = 0

    @property
    def active(self) -> bool:
        return self._aktuell is not None and self._aktuell.active

    @property
    def shake_offset(self) -> tuple[int, int]:
        if self._aktuell and self._aktuell.active:
            return self._aktuell.shake_offset
        return (0, 0)

    @property
    def is_blackout(self) -> bool:
        return False  # blackout gibt es nicht mehr

    def trigger(self, typ: str,
                spieler_sx: int = SW // 2,
                spieler_sy: int = SH // 2) -> None:
        # jumpscare starten (nur wenn cooldown abgelaufen)
        if self._cooldown > 0:
            return
        if self._aktuell and self._aktuell.active:
            if typ != JumpscareEffect.TYP_GEFANGEN:
                return

        self._aktuell  = JumpscareEffect(typ, spieler_sx, spieler_sy)
        self._cooldown = 200

        if self._sounds:
            self._sounds.play("jumpscare")

    def update(self, spiel_laeuft: bool = True) -> None:
        # cooldown und aktiven jumpscare aktualisieren
        if self._cooldown > 0:
            self._cooldown -= 1
        if self._aktuell:
            self._aktuell.update()

    def draw(self, surface: pygame.Surface) -> None:
        if self._aktuell and self._aktuell.active:
            self._aktuell.draw(surface)
