import pygame
from game.game_variables import GameVariables, GameScreens

TILE_SIZE = 48

# Tile-Typen
WALL  = 0
FLOOR = 1

# Einfaches Raum-Layout (0 = Wand, 1 = Boden)
ROOM_MAP = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 1, 1, 1, 1, 1, 1, 1, 1, 0],
    [0, 1, 1, 1, 1, 1, 1, 1, 1, 0],
    [0, 1, 1, 1, 1, 1, 1, 1, 1, 0],
    [0, 1, 1, 1, 1, 1, 1, 1, 1, 0],
    [0, 1, 1, 1, 1, 1, 1, 1, 1, 0],
    [0, 1, 1, 1, 1, 1, 1, 1, 1, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
]

WALL_COLOR  = (120, 60, 20)   # Braun/Ziegel
FLOOR_COLOR = (200, 180, 150) # Heller Boden

def draw_room(screen):
    for row_i, row in enumerate(ROOM_MAP):
        for col_i, tile in enumerate(row):
            x = col_i * TILE_SIZE
            y = row_i * TILE_SIZE
            rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)

            if tile == WALL:
                pygame.draw.rect(screen, WALL_COLOR, rect)
                pygame.draw.rect(screen, (80, 40, 10), rect, 2)  # Rand
            else:
                pygame.draw.rect(screen, FLOOR_COLOR, rect)
                pygame.draw.rect(screen, (180, 160, 130), rect, 1)  # Gitter