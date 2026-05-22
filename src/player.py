import pygame
from game.game_variables import GameVariables

class Player:
    SIZE = 32
    COLOR = (220, 180, 100)

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def update(self, keys):
        speed = GameVariables.PLAYER_SPEED
        if keys[pygame.K_w] or keys[pygame.K_UP]:    self.y -= speed
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:  self.y += speed
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:  self.x -= speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: self.x += speed

    def draw(self, screen):
        pygame.draw.rect(screen, self.COLOR,
                         (self.x, self.y, self.SIZE, self.SIZE),
                         border_radius=8)