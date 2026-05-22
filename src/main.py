import pygame
import sys
from game.game_variables import GameVariables, GameScreens
from room import draw_room
from player import Player

GameVariables.init()

screen = pygame.display.set_mode((GameVariables.SCREEN_WIDTH, GameVariables.SCREEN_HEIGHT))
pygame.display.set_caption(GameVariables.TITLE)
clock = pygame.time.Clock()

player = Player(200, 200)


def draw_darkness(player_x, player_y):
    dark = pygame.Surface((GameVariables.SCREEN_WIDTH, GameVariables.SCREEN_HEIGHT),
                           pygame.SRCALPHA)
    dark.fill((0, 0, 0, 255))   # komplett schwarz + alpha

    cx = player_x + 16
    cy = player_y + 16

    # Sichtkreis ausschneiden (transparent machen)
    for radius, alpha in [(220, 180), (180, 100), (130, 40), (80, 0)]:
        pygame.draw.circle(dark, (0, 0, 0, alpha), (cx, cy), radius)

    screen.blit(dark, (0, 0))


def draw_main_screen():
    screen.fill((10, 10, 20))

    title = GameVariables.FONT_BIG.render("NIGHTWATCH", True, (200, 40, 40))
    screen.blit(title, (GameVariables.SCREEN_WIDTH  // 2 - title.get_width()  // 2, 260))

    hint = GameVariables.FONT_MIDDLE.render("[ ENTER ] Starten", True, (120, 120, 140))
    screen.blit(hint, (GameVariables.SCREEN_WIDTH // 2 - hint.get_width() // 2, 370))

    esc = GameVariables.FONT_SMALL.render("[ ESC ] Beenden", True, (70, 70, 80))
    screen.blit(esc, (GameVariables.SCREEN_WIDTH // 2 - esc.get_width() // 2, 430))


def draw_game_over_screen():
    screen.fill((15, 0, 0))

    txt = GameVariables.FONT_BIG.render("GAME OVER", True, (220, 30, 30))
    screen.blit(txt, (GameVariables.SCREEN_WIDTH  // 2 - txt.get_width()  // 2, 260))

    hint = GameVariables.FONT_MIDDLE.render("[ R ] Nochmal   [ ESC ] Menu", True, (140, 100, 100))
    screen.blit(hint, (GameVariables.SCREEN_WIDTH // 2 - hint.get_width() // 2, 370))


if "__main__" == __name__:
    running = True
    while running:
        events = pygame.event.get()
        keys   = pygame.key.get_pressed()

        for event in events:
            if event.type == pygame.QUIT:
                running = False

        # MAIN SCREEN
        if GameScreens.actual_screen == GameScreens.MAIN:
            draw_main_screen()

            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        player = Player(200, 200)   # Spieler zuruecksetzen
                        GameScreens.actual_screen = GameScreens.PLAY
                    elif event.key == pygame.K_ESCAPE:
                        running = False

        # PLAY SCREEN
        elif GameScreens.actual_screen == GameScreens.PLAY:
            screen.fill((0, 0, 0))
            draw_room(screen)
            player.update(keys)
            player.draw(screen)
            draw_darkness(player.x, player.y)

            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        GameScreens.actual_screen = GameScreens.GAME_OVER

        # GAME OVER SCREEN
        elif GameScreens.actual_screen == GameScreens.GAME_OVER:
            draw_game_over_screen()

            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        GameScreens.actual_screen = GameScreens.MAIN
                    elif event.key == pygame.K_ESCAPE:
                        GameScreens.actual_screen = GameScreens.MAIN

        pygame.display.flip()
        clock.tick(GameVariables.FPS)

    pygame.quit()
    sys.exit()