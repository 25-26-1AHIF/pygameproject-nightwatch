import math
import pygame
from game_variables.game_variables import GameVariables
from game.level import is_walkable, get_floor_at, EXIT_RECT, EXIT_POS
from game.utils import vec_norm, dist
from game.sprites import PlayerSprite

GV = GameVariables


class Player:
    """Der Spieler-Charakter mit Bewegung, Dash, Taschenlampe und Geräuschpegel."""

    # wie oft pro frame ein schritt-sound abgespielt wird
    _SCHRITT_HART:  int = 22
    _SCHRITT_WEICH: int = 30

    def __init__(self, x: float, y: float):
        self.x: float = x
        self.y: float = y

        self.facing: float      = 0.0
        self.battery: float     = GV.LAMPE_AKKU_MAX
        self.torch_on: bool     = True
        self.is_sneaking: bool  = False
        self.alive: bool        = True
        self.reached_exit: bool = False
        self.near_exit: bool    = False   # für den "[E] ausgang"-hinweis

        self._schritt_timer: int = 0
        self._bewegt: bool       = False
        self._anim_frame: int    = 0
        self._anim_timer: int    = 0

        self.noise_level: float  = 0.0

        # dash-zustand
        self.is_dashing: bool          = False
        self._dash_timer: int          = 0
        self._dash_cooldown: int       = 0
        self._dash_dir: tuple          = (1.0, 0.0)
        self.dash_just_activated: bool = False

        self._sprite = PlayerSprite()

    def _versuche_bewegen(self, dx: float, dy: float) -> None:
        # erst diagonal probieren, dann nur x, dann nur y
        # so bleibt man nicht an ecken hängen
        nx, ny = self.x + dx, self.y + dy
        if is_walkable(nx, ny):
            self.x, self.y = nx, ny
        elif is_walkable(nx, self.y):
            self.x = nx
        elif is_walkable(self.x, ny):
            self.y = ny
        # nicht aus der welt rauslaufen
        self.x = max(GV.SPIELER_RADIUS, min(GV.WORLD_W - GV.SPIELER_RADIUS, self.x))
        self.y = max(GV.SPIELER_RADIUS, min(GV.WORLD_H - GV.SPIELER_RADIUS, self.y))

    def update(self, keys: pygame.key.ScancodeWrapper,
               events: list,
               mx: int, my: int,
               cam_x: int, cam_y: int,
               sounds) -> None:
        """Einmal pro frame aufgerufen – verarbeitet eingaben und aktualisiert zustand."""
        self.dash_just_activated = False

        for ev in events:
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_f:
                # taschenlampe umschalten
                self.torch_on = not self.torch_on
                if sounds:
                    sounds.play("torch_click")
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_SPACE:
                # dash nur wenn cooldown abgelaufen
                if self._dash_cooldown <= 0 and not self.is_dashing:
                    self.is_dashing          = True
                    self._dash_timer         = GV.DASH_DAUER
                    self._dash_cooldown      = GV.DASH_COOLDOWN
                    self.dash_just_activated = True
                    if sounds:
                        sounds.play("dash")

        self.is_sneaking = keys[pygame.K_LSHIFT]
        boden = get_floor_at(self.x, self.y)
        tempo = GV.SPIELER_SCHLEICH_GESCHW if self.is_sneaking else GV.SPIELER_GESCHWINDIGKEIT
        if boden == GV.BODEN_TEPPICH and not self.is_sneaking:
            # teppich bremst ein bisschen ab
            tempo *= 0.85

        dx, dy = 0.0, 0.0
        if keys[pygame.K_w] or keys[pygame.K_UP]:    dy -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:  dy += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:  dx -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx += 1
        self._bewegt = dx != 0 or dy != 0

        if self._bewegt:
            ndx, ndy = vec_norm(dx, dy)
            self._dash_dir = (ndx, ndy)  # richtung für den dash merken
        else:
            ndx, ndy = self._dash_dir

        # dash timer runterzählen
        if self.is_dashing:
            self._dash_timer -= 1
            if self._dash_timer <= 0:
                self.is_dashing = False
        if self._dash_cooldown > 0:
            self._dash_cooldown -= 1

        if self.is_dashing:
            self._versuche_bewegen(ndx * GV.DASH_GESCHWINDIGKEIT,
                                   ndy * GV.DASH_GESCHWINDIGKEIT)
        elif self._bewegt:
            self._versuche_bewegen(ndx * tempo, ndy * tempo)

        # mauszeiger gibt die blickrichtung vor
        welt_mx = mx + cam_x
        welt_my = my + cam_y
        self.facing = math.degrees(math.atan2(welt_my - self.y, welt_mx - self.x))

        # akku leert sich wenn lampe an
        if self.torch_on:
            self.battery = max(0.0, self.battery - GV.LAMPE_VERBRAUCH)
            if self.battery <= 0:
                self.torch_on = False

        # animationsframe wechseln
        self._anim_timer += 1
        intervall = 8 if self._bewegt else 20
        if self._anim_timer >= intervall:
            self._anim_timer = 0
            self._anim_frame = (self._anim_frame + 1) % 4

        # schritt-sounds abhängig vom bodentyp
        if self._bewegt:
            self._schritt_timer += 1
            schritt_int = (self._SCHRITT_WEICH
                           if boden == GV.BODEN_TEPPICH
                           else self._SCHRITT_HART)
            if self.is_sneaking:
                schritt_int = int(schritt_int * 2.0)
            if self._schritt_timer >= schritt_int:
                self._schritt_timer = 0
                if sounds:
                    klan = "step_soft" if boden == GV.BODEN_TEPPICH else "step_hard"
                    sounds.play(klan)
        else:
            self._schritt_timer = 0

        # lärmpegel bestimmt wie gut das monster den spieler hört
        if not self._bewegt:
            self.noise_level = 0.0
        elif self.is_sneaking:
            self.noise_level = 0.25 if boden != GV.BODEN_TEPPICH else 0.08
        elif boden == GV.BODEN_TEPPICH:
            self.noise_level = 0.38
        else:
            self.noise_level = 1.0

        # exit-tür: nur mit [E] wenn man nah genug dran ist
        self.near_exit = dist(self.x, self.y, EXIT_POS[0], EXIT_POS[1]) < 65
        if self.near_exit and not self.reached_exit:
            for ev in events:
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_e:
                    self.reached_exit = True

    def draw(self, surface: pygame.Surface, cam_x: int, cam_y: int) -> None:
        """Spieler und dash-effekt auf die view-surface zeichnen."""
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)

        # leuchtspur beim dashen
        if self.is_dashing:
            fortschr = 1.0 - self._dash_timer / GV.DASH_DAUER
            glow_r   = int(16 + fortschr * 24)
            glow_a   = int(180 * (1 - fortschr))
            gs = pygame.Surface((glow_r * 2 + 4, glow_r * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(gs, (160, 200, 255, glow_a),
                               (glow_r + 2, glow_r + 2), glow_r, 4)
            surface.blit(gs, (sx - glow_r - 2, sy - glow_r - 2))

        self._sprite.draw(surface, sx, sy,
                          self._bewegt or self.is_dashing, self._anim_frame)

        # kleiner strich zeigt die blickrichtung an
        if self.torch_on and self.battery > 0:
            richtung_rad = math.radians(self.facing)
            ex = sx + int(math.cos(richtung_rad) * 20)
            ey = sy + int(math.sin(richtung_rad) * 20)
            pygame.draw.line(surface, (200, 190, 140, 120), (sx, sy), (ex, ey), 2)

    @property
    def dash_cooldown(self) -> int:
        return self._dash_cooldown
