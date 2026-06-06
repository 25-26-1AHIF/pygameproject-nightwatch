import pygame
from game_variables.game_variables import GameVariables as GV


class Player:
    def __init__(self, screen: pygame.Surface, x: int, y: int):
        self.screen = screen
        self.xpos = x
        self.ypos = y
        self.groesse = GV.SQUARE_SIZE
        self.speed = 3

    def move(self):
        keys = pygame.key.get_pressed()

        if keys[pygame.K_w] or keys[pygame.K_UP]:
            self.ypos -= self.speed
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            self.ypos += self.speed
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.xpos -= self.speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.xpos += self.speed

        # Spieler soll nicht aus dem Fenster rausgehen
        if self.xpos < 0:
            self.xpos = 0
        if self.xpos > GV.SCREEN_WIDTH - self.groesse:
            self.xpos = GV.SCREEN_WIDTH - self.groesse
        if self.ypos < 0:
            self.ypos = 0
        if self.ypos > GV.SCREEN_HEIGHT - self.groesse:
            self.ypos = GV.SCREEN_HEIGHT - self.groesse

    def zeichnen(self):
        pygame.draw.rect(
            surface=self.screen,
            rect=(self.xpos, self.ypos, self.groesse, self.groesse),
            color=(210, 190, 120)
        )

    def update_and_draw(self):
        self.move()
        self.zeichnen()
