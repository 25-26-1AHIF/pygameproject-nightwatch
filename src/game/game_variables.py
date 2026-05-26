import pygame

class GameVariables:
    SCREEN_WIDTH  = 1280
    SCREEN_HEIGHT = 720
    FPS           = 60
    TITLE         = "Nightwatch"

    PLAYER_SPEED  = 4
    PLAYER_SIZE   = 32

    FONT_BIG    = None
    FONT_MIDDLE = None
    FONT_SMALL  = None

    @staticmethod
    def init():
        pygame.init()
        GameVariables.FONT_BIG    = pygame.font.SysFont("monospace", 100, bold=True)
        GameVariables.FONT_MIDDLE = pygame.font.SysFont("monospace", 30, bold=True)
        GameVariables.FONT_SMALL  = pygame.font.SysFont("monospace", 16, bold=True)


class GameScreens:
    MAIN      = "main"
    PLAY      = "play"
    GAME_OVER = "game_over"
    SCOREBOARD = "scoreboard"
    TUT = "TUT"

    actual_screen = MAIN