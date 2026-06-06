import pygame
from game_variables.game_variables import GameVariables as GV
from game.sprite import Sprite


class Player:
    def __init__(self, screen: pygame.Surface, x: int, y: int):
        self.screen  = screen
        self.xpos    = x
        self.ypos    = y
        self.groesse = GV.SQUARE_SIZE
        self.speed   = 3
        self.frame_counter = 0

        # KI CODE ANFANG
        # Spritesheet laden - 5 Frames, jeder Frame 38x38px (190x38 gesamt)
        self.animation = Sprite(
            filepath       = "assets/images/player_sheet.png",
            image_count    = 5,
            image_rect     = pygame.Rect(0, 0, 38, 38),
            animation_speed= 8
        )
        self.animation.load_spritesheet()
        # KI CODE ENDE

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
        # Sprite auf SQUARE_SIZE skaliert zeichnen
        self.animation.draw(
            screen        = self.screen,
            xpos          = self.xpos,
            ypos          = self.ypos,
            frame_counter = self.frame_counter,
            scale         = (self.groesse, self.groesse)
        )
        self.frame_counter += 1

    def update_and_draw(self):
        self.move()
        self.zeichnen()
