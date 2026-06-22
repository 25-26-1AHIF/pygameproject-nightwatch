import math
import random
from enum import Enum, auto

import pygame

from game_variables.game_variables import GameVariables
from game.level import is_walkable, get_floor_at
from game.utils import dist, next_waypoint, nearest_node, bfs_path
from game.sprites import MonsterSprite

GV = GameVariables


class MonsterState(Enum):
    # drei zustände - patrouille ist normal, alert wenn es was gehört hat, hunt wenn es den spieler sieht
    PATROL = auto()
    ALERT  = auto()
    HUNT   = auto()


# das monster läuft diese routen im patrouillemodus ab
PATROL_ROUTEN: list[list[int]] = [
    [0, 1, 2, 3, 4, 5, 6, 13, 12, 11, 10, 9, 8, 7, 0],
    [3, 4, 5, 6, 13, 12, 5, 4, 3],
]

# geschwindigkeiten - werden beim spielstart mit apply_difficulty überschrieben
_speed_patrol = GV.MONSTER_RADIUS * 0 + 1.2
_speed_alert  = 1.8
_speed_hunt   = 3.4
_sight_range  = GV.MONSTER_SICHT
_dark_sight   = GV.MONSTER_DUNKEL
_hear_parkett = GV.MONSTER_HOER_PARKETT
_hear_fliesen = GV.MONSTER_HOER_FLIESEN
_hear_teppich = GV.MONSTER_HOER_TEPPICH
_hear_base    = GV.MONSTER_HOER


class Monster:
    # das monster – verfolgt und fängt den spieler

    def __init__(self, x: float, y: float):
        self.x: float = x
        self.y: float = y

        self.state: MonsterState = MonsterState.PATROL
        self._vorher_state       = MonsterState.PATROL

        self._routen_idx: int  = 0
        self._route: list[int] = PATROL_ROUTEN[0][:]
        self._wegpunkt: tuple  = GV.NAV_NODES[self._route[0]]

        self._alert_timer: int      = 0
        self._zuletzt_gesehen_x: float = 0.0
        self._zuletzt_gesehen_y: float = 0.0

        self._flash_timer: int = 0
        self._anim_frame:  int = 0
        self._anim_timer:  int = 0
        self._scale: float     = 1.0

        self.just_triggered_jumpscare: bool = False

        self._stun_timer: int = 0
        self.is_stunned: bool = False

        self._sprite = MonsterSprite()

    def update(self, player_x: float, player_y: float,
               player_noise: float, player_battery: float,
               sounds) -> None:
        # ki-update einmal pro frame – zustandsübergänge und bewegung

        self.just_triggered_jumpscare = False
        self._vorher_state = self.state

        # betäubt durch dash - nichts tun außer animation
        if self._stun_timer > 0:
            self._stun_timer -= 1
            self.is_stunned = True
            self._anim_timer += 1
            if self._anim_timer >= 18:
                self._anim_timer = 0
                self._anim_frame = (self._anim_frame + 1) % 6
            return
        self.is_stunned = False

        kann_sehen  = self._pruefe_sicht(player_x, player_y, player_battery)
        kann_hoeren = self._pruefe_geraeusch(player_x, player_y, player_noise)

        if self.state == MonsterState.PATROL:
            if kann_sehen or kann_hoeren:
                self._starte_alert(player_x, player_y)

        elif self.state == MonsterState.ALERT:
            if kann_sehen:
                self._starte_hunt(player_x, player_y, sounds)
            else:
                self._alert_timer -= 1
                if kann_hoeren:
                    self._alert_timer = GV.ALERT_DAUER
                    self._zuletzt_gesehen_x = player_x
                    self._zuletzt_gesehen_y = player_y
                if self._alert_timer <= 0:
                    self._starte_patrol()

        elif self.state == MonsterState.HUNT:
            if kann_sehen:
                self._zuletzt_gesehen_x = player_x
                self._zuletzt_gesehen_y = player_y
            else:
                d = dist(self.x, self.y, player_x, player_y)
                if d > GV.JAGD_VERLIER_DIST:
                    self._starte_alert(self._zuletzt_gesehen_x,
                                       self._zuletzt_gesehen_y)

        speed = {
            MonsterState.PATROL: _speed_patrol,
            MonsterState.ALERT:  _speed_alert,
            MonsterState.HUNT:   _speed_hunt,
        }[self.state]

        self._bewege(speed, player_x, player_y)

        self._anim_timer += 1
        anim_speed = 6 if self.state == MonsterState.HUNT else 10
        if self._anim_timer >= anim_speed:
            self._anim_timer = 0
            self._anim_frame = (self._anim_frame + 1) % 6

        if self.state == MonsterState.HUNT:
            self._flash_timer = (self._flash_timer + 1) % 20
            self._scale = 1.0 + abs(math.sin(self._flash_timer / 20 * math.pi)) * 0.15
        else:
            self._flash_timer = 0
            self._scale = 1.0

        if sounds:
            d = dist(self.x, self.y, player_x, player_y)
            if self.state == MonsterState.HUNT:
                sounds.set_heartbeat_volume(max(0.0, 1.0 - d / 600))
            elif self.state == MonsterState.ALERT:
                sounds.set_heartbeat_volume(0.25)
            else:
                sounds.set_heartbeat_volume(0.0)

    def _starte_patrol(self) -> None:
        self.state       = MonsterState.PATROL
        self._routen_idx = 0
        self._route      = random.choice(PATROL_ROUTEN)[:]
        self._wegpunkt   = GV.NAV_NODES[self._route[0]]

    def _starte_alert(self, tx: float, ty: float) -> None:
        self.state               = MonsterState.ALERT
        self._alert_timer        = GV.ALERT_DAUER
        self._zuletzt_gesehen_x  = tx
        self._zuletzt_gesehen_y  = ty

    def _starte_hunt(self, tx: float, ty: float, sounds) -> None:
        if self.state != MonsterState.HUNT:
            self.just_triggered_jumpscare = True
            if sounds:
                sounds.play("alert")
        self.state               = MonsterState.HUNT
        self._zuletzt_gesehen_x  = tx
        self._zuletzt_gesehen_y  = ty

    def _pruefe_sicht(self, px: float, py: float, battery: float) -> bool:
        # wenn lampe aus sieht das monster schlechter
        d     = dist(self.x, self.y, px, py)
        sicht = _sight_range if battery > 5 else _dark_sight
        return d <= sicht

    def _pruefe_geraeusch(self, px: float, py: float, noise: float) -> bool:
        # teppich schluckt geräusche, fliesen leiten sie weiter
        if noise <= 0:
            return False
        boden = get_floor_at(px, py)
        if boden == GV.BODEN_PARKETT:   basis = _hear_parkett
        elif boden == GV.BODEN_FLIESEN: basis = _hear_fliesen
        elif boden == GV.BODEN_TEPPICH: basis = _hear_teppich
        else:                            basis = _hear_base
        return dist(self.x, self.y, px, py) <= basis * noise

    # KI CODE ANFANG
    # Claude Opus 4.8
    # Prompt: "Implementiere die _bewege()-Methode für ein Horrorspiel-Monster mit
    # drei Zuständen: PATROL (folgt vordefinierten Wegpunkten), ALERT (geht zur
    # letzten bekannten Spielerposition via BFS-Pathfinding) und HUNT (verfolgt
    # Spieler direkt via BFS). Vektornormalisierung für konstante Geschwindigkeit,
    # Wandkollision durch axis-separierte Bewegung."
    def _bewege(self, speed: float, px: float, py: float) -> None:
        # bewegt das monster je nach zustand zum richtigen ziel

        if self.state == MonsterState.HUNT:
            ziel_x, ziel_y = next_waypoint(self.x, self.y, px, py)
            if dist(self.x, self.y, ziel_x, ziel_y) < 40:
                ziel_x, ziel_y = px, py
        elif self.state == MonsterState.ALERT:
            ziel_x, ziel_y = next_waypoint(self.x, self.y,
                                            self._zuletzt_gesehen_x,
                                            self._zuletzt_gesehen_y)
        else:
            ziel_x, ziel_y = self._wegpunkt

        dx = ziel_x - self.x
        dy = ziel_y - self.y
        d  = math.sqrt(dx * dx + dy * dy)

        if d < speed:
            self.x, self.y = ziel_x, ziel_y
            self._naechster_wegpunkt(px, py)
            return

        ndx, ndy = dx / d, dy / d
        nx = self.x + ndx * speed
        ny = self.y + ndy * speed

        if is_walkable(nx, ny):
            self.x, self.y = nx, ny
        elif is_walkable(nx, self.y):
            self.x = nx
        elif is_walkable(self.x, ny):
            self.y = ny
    # KI CODE ENDE

    def _naechster_wegpunkt(self, px: float, py: float) -> None:
        # wählt den nächsten wegpunkt je nach zustand

        if self.state == MonsterState.PATROL:
            self._routen_idx = (self._routen_idx + 1) % len(self._route)
            self._wegpunkt   = GV.NAV_NODES[self._route[self._routen_idx]]
        elif self.state == MonsterState.ALERT:
            nahe = nearest_node(self._zuletzt_gesehen_x, self._zuletzt_gesehen_y)
            pfad = bfs_path(nearest_node(self.x, self.y), nahe)
            if len(pfad) > 1:
                self._wegpunkt = GV.NAV_NODES[pfad[1]]
            else:
                self._wegpunkt = GV.NAV_NODES[nahe]

    def stun(self, dauer: int) -> None:
        # betäubt das monster für eine bestimmte anzahl frames

        self._stun_timer = dauer
        self.is_stunned  = True

    def apply_difficulty(self, diff: dict) -> None:
        # wendet schwierigkeitsgrad-einstellungen auf die monster-werte an

        global _speed_patrol, _speed_alert, _speed_hunt
        global _sight_range, _hear_parkett, _hear_fliesen, _hear_teppich, _hear_base
        _speed_patrol = diff["patrol"]
        _speed_alert  = diff["alert"]
        _speed_hunt   = diff["hunt"]
        _sight_range  = diff["sight"]
        hf = diff["hear_factor"]
        _hear_parkett = int(240 * hf)
        _hear_fliesen = int(200 * hf)
        _hear_teppich = int(80  * hf)
        _hear_base    = int(180 * hf)

    def catches_player(self, px: float, py: float) -> bool:
        # true wenn das monster nah genug am spieler ist um zu fangen

        return dist(self.x, self.y, px, py) <= GV.MONSTER_RADIUS + 14

    def draw(self, surface: pygame.Surface, cam_x: int, cam_y: int) -> None:
        # zeichnet das monster auf die view-surface

        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)

        sw = GV.SCREEN_W
        sh = GV.SCREEN_H
        if sx < -80 or sx > sw + 80 or sy < -100 or sy > sh + 100:
            return

        zustand_name = {
            MonsterState.PATROL: "patrol",
            MonsterState.ALERT:  "alert",
            MonsterState.HUNT:   "hunt",
        }[self.state]

        self._sprite.draw(surface, sx, sy, zustand_name, self._anim_frame, self._scale)

        if self.is_stunned:
            t = pygame.time.get_ticks() / 200
            for i in range(4):
                winkel  = t + i * (math.pi / 2)
                stern_x = sx + int(math.cos(winkel) * 28)
                stern_y = sy + int(math.sin(winkel) * 18) - 30
                pygame.draw.circle(surface, (255, 220, 60), (stern_x, stern_y), 4)
                pygame.draw.circle(surface, (255, 255, 150), (stern_x, stern_y), 2)
            font_stun = pygame.font.SysFont("monospace", 13, bold=True)
            txt_stun  = font_stun.render("BETÄUBT", True, (255, 220, 60))
            surface.blit(txt_stun, (sx - txt_stun.get_width() // 2, sy - 58))

        if self.state == MonsterState.ALERT:
            font = pygame.font.SysFont("monospace", 20, bold=True)
            txt  = font.render("!", True, (255, 180, 0))
            surface.blit(txt, (sx - 5, sy - 48))

    def draw_state_indicator(self, surface: pygame.Surface) -> None:
        # kleiner zustandsindikator oben links

        farb_map = {
            MonsterState.PATROL: (40, 160, 60),
            MonsterState.ALERT:  (200, 150, 20),
            MonsterState.HUNT:   (200, 20, 20),
        }
        name_map = {
            MonsterState.PATROL: "PATROL",
            MonsterState.ALERT:  "ALERT !",
            MonsterState.HUNT:   "HUNT !!!",
        }
        font = pygame.font.SysFont("monospace", 13)
        col  = farb_map[self.state]
        txt  = font.render(f"Monster: {name_map[self.state]}", True, col)
        surface.blit(txt, (10, 10))
