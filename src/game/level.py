import random
import pygame
from game_variables.game_variables import GameVariables

GV = GameVariables

PARQUET_FARBE = (28, 18, 10)
TEPPICH_FARBE = (18, 14, 22)
KACHEL_FARBE  = (20, 22, 28)
WAND_FARBE    = ( 8,  6, 10)
TUER_FARBE    = (22, 14,  8)


class Room:
    # ein raum oder gang im level

    def __init__(self, rect: pygame.Rect, floor: str, name: str = ""):
        self.rect  = rect
        self.floor = floor
        self.name  = name

    def color(self) -> tuple:
        # bodenfarbe je nach bodentyp
        if self.floor == GV.BODEN_PARKETT: return PARQUET_FARBE
        if self.floor == GV.BODEN_TEPPICH: return TEPPICH_FARBE
        return KACHEL_FARBE


# die 6 haupträume des hauses
R1  = Room(pygame.Rect(100,   80, 480, 340), GV.BODEN_PARKETT, "R1_Wohnzimmer")
R2  = Room(pygame.Rect(680,   80, 480, 340), GV.BODEN_PARKETT, "R2_Küche")
R3  = Room(pygame.Rect(1260,  80, 480, 340), GV.BODEN_TEPPICH, "R3_Schlafzimmer")
R4  = Room(pygame.Rect(1840,  80, 480, 340), GV.BODEN_TEPPICH, "R4_Büro")
R5  = Room(pygame.Rect(100,  700, 480, 340), GV.BODEN_PARKETT, "R5_Keller")
ENT = Room(pygame.Rect(680,  700, 1640, 340), GV.BODEN_FLIESEN, "Eingangsbereich")

# verbindungsgänge zwischen den räumen
CR12  = Room(pygame.Rect(580,  196, 100, 108), GV.BODEN_PARKETT, "Gang_12")
CR23  = Room(pygame.Rect(1160, 196, 100, 108), GV.BODEN_TEPPICH, "Gang_23")
CR34  = Room(pygame.Rect(1740, 196, 100, 108), GV.BODEN_TEPPICH, "Gang_34")
CR1R5 = Room(pygame.Rect(290,  420, 100, 280), GV.BODEN_PARKETT, "Gang_1R5")
CR4EN = Room(pygame.Rect(2030, 420, 100, 280), GV.BODEN_TEPPICH, "Gang_4EN")
CR5EN = Room(pygame.Rect(580,  800, 100, 100), GV.BODEN_FLIESEN, "Gang_5EN")

ALL_ROOMS: list[Room] = [
    R1, R2, R3, R4, R5, ENT,
    CR12, CR23, CR34, CR1R5, CR4EN, CR5EN,
]

DOORS: list[pygame.Rect] = [
    pygame.Rect(580,  230, 16, 40),
    pygame.Rect(1160, 230, 16, 40),
    pygame.Rect(1740, 230, 16, 40),
    pygame.Rect(318,  418, 40, 16),
    pygame.Rect(2058, 418, 40, 16),
    pygame.Rect(578,  830, 40, 16),
]

EXIT_RECT     = pygame.Rect(2260, 760, 60, 260)  # innerhalb ENT (endet bei x=2320)
EXIT_POS      = (2285, 870)                        # mittelpunkt der exit-tuer
PLAYER_START  = (340, 250)
MONSTER_START = (1500, 250)


def get_floor_at(wx: float, wy: float) -> str | None:
    # welcher bodentyp liegt an dieser weltposition
    pt = pygame.Vector2(wx, wy)
    for room in ALL_ROOMS:
        if room.rect.collidepoint(pt):
            return room.floor
    return None


def is_walkable(wx: float, wy: float) -> bool:
    # true wenn der punkt innerhalb eines raums liegt
    return get_floor_at(wx, wy) is not None


def get_room_at(wx: float, wy: float) -> Room | None:
    # gibt den raum zurueck in dem sich diese position befindet
    pt = pygame.Vector2(wx, wy)
    for room in ALL_ROOMS:
        if room.rect.collidepoint(pt):
            return room
    return None


def draw(surface: pygame.Surface, cam_x: int, cam_y: int,
         ketten_schwingung: float = 0.0) -> None:
    # zeichnet alle raeume, boeden, tueren und die exit-tuer
    surface.fill(WAND_FARBE)

    for room in ALL_ROOMS:
        r   = room.rect.move(-cam_x, -cam_y)
        col = room.color()

        pygame.draw.rect(surface, col, r)

        # bodentextur abhaengig vom bodentyp
        if room.floor == GV.BODEN_PARKETT:
            for lx in range(r.left + 12, r.right, 24):
                pygame.draw.line(surface,
                                 (col[0] + 6, col[1] + 3, col[2] + 2),
                                 (lx, r.top + 4), (lx, r.bottom - 4), 1)

        elif room.floor == GV.BODEN_TEPPICH:
            rng = random.Random(room.rect.x)
            for _ in range(12):
                px = r.left + rng.randint(4, r.width  - 4)
                py = r.top  + rng.randint(4, r.height - 4)
                pygame.draw.circle(surface,
                                   (col[0] + 4, col[1] + 2, col[2] + 6),
                                   (px, py), 2)

        elif room.floor == GV.BODEN_FLIESEN:
            for tx in range(r.left, r.right, 20):
                pygame.draw.line(surface,
                                 (col[0] + 5, col[1] + 5, col[2] + 8),
                                 (tx, r.top), (tx, r.bottom), 1)
            for ty in range(r.top, r.bottom, 20):
                pygame.draw.line(surface,
                                 (col[0] + 5, col[1] + 5, col[2] + 8),
                                 (r.left, ty), (r.right, ty), 1)

        # raumrand
        pygame.draw.rect(surface, (4, 3, 6), r, 3)

    for door in DOORS:
        dr = door.move(-cam_x, -cam_y)
        pygame.draw.rect(surface, TUER_FARBE, dr)
        pygame.draw.rect(surface, (10, 6, 4), dr, 1)

    # exit-tuer gruen markieren
    ex = EXIT_RECT.move(-cam_x, -cam_y)
    pygame.draw.rect(surface, (8, 30, 12), ex)
    pygame.draw.rect(surface, (15, 60, 20), ex, 2)
    try:
        font = pygame.font.SysFont("monospace", 11, bold=True)
        txt  = font.render("EXIT", True, (20, 100, 35))
        surface.blit(txt, (ex.x + 3, ex.y + ex.height // 2 - 7))
    except Exception:
        pass
