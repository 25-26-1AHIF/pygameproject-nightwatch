import pygame
import math
from game_variables.game_variables import GameVariables as GV


class Monster:
    def __init__(self, screen: pygame.Surface, x: int, y: int):
        self.screen = screen
        self.xpos = x
        self.ypos = y
        self.groesse = GV.SQUARE_SIZE
        self.speed = 1.5

    # KI CODE ANFANG
    # Bewegung zum Spieler hin berechnen mit Vektorrechnung
    def move(self, player_x: int, player_y: int):
        dx = player_x - self.xpos
        dy = player_y - self.ypos
        distanz = math.sqrt(dx * dx + dy * dy)

        if distanz == 0:
            return

        self.xpos += (dx / distanz) * self.speed
        self.ypos += (dy / distanz) * self.speed
    # KI CODE ENDE

    def zeichnen(self):
        pygame.draw.rect(
            surface=self.screen,
            rect=(self.xpos, self.ypos, self.groesse, self.groesse),
            color=(180, 30, 30)
        )
        # Augen damit man sieht wo das Monster ist
        pygame.draw.circle(self.screen, (255, 200, 0),
                           (int(self.xpos) + 8,  int(self.ypos) + 10), 4)
        pygame.draw.circle(self.screen, (255, 200, 0),
                           (int(self.xpos) + 24, int(self.ypos) + 10), 4)

    def update_and_draw(self, player_x: int, player_y: int):
        self.move(player_x, player_y)
        self.zeichnen()

    def trifft_spieler(self, player_x: int, player_y: int) -> bool:
        monster_rect = pygame.Rect(self.xpos, self.ypos, self.groesse, self.groesse)
        spieler_rect = pygame.Rect(player_x, player_y, GV.SQUARE_SIZE, GV.SQUARE_SIZE)
        return monster_rect.colliderect(spieler_rect)
