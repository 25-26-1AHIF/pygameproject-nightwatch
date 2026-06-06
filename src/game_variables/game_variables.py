import pygame


class GameVariables:
    SCREEN_WIDTH = 1280
    SCREEN_HEIGHT = 720
    SQUARE_SIZE = 32
    FPS = 60

    FONT_BIG = None
    FONT_MIDDLE = None
    FONT_SMALL = None

    @staticmethod
    def init():
        pygame.init()
        GameVariables.FONT_BIG    = pygame.font.SysFont("calibri", 64, bold=True)
        GameVariables.FONT_MIDDLE = pygame.font.SysFont("calibri", 30, bold=True)
        GameVariables.FONT_SMALL  = pygame.font.SysFont("calibri", 14, bold=True)


class GameScreens:
    MAIN      = "main"
    PLAY      = "play"
    GAME_OVER = "game_over"
    EXIT      = "exit"
    actual_screen = MAIN
