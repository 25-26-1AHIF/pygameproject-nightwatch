import pygame
import sys
from game.game_variables import GameVariables, GameScreens

GameVariables.init()

screen = pygame.display.set_mode((GameVariables.SCREEN_WIDTH, GameVariables.SCREEN_HEIGHT))
pygame.display.set_caption(GameVariables.TITLE)
clock = pygame.time.Clock()

# Spieler-Position
player_x = GameVariables.SCREEN_WIDTH  // 2
player_y = GameVariables.SCREEN_HEIGHT // 2


def draw_main_screen():
    screen.fill((10, 10, 20))

    title = GameVariables.FONT_BIG.render("NIGHTWATCH", True, (200, 40, 40))
    screen.blit(title, (GameVariables.SCREEN_WIDTH  // 2 - title.get_width()  // 2, 260))

    hint = GameVariables.FONT_MIDDLE.render("[ ENTER ] Starten", True, (120, 120, 140))
    screen.blit(hint, (GameVariables.SCREEN_WIDTH // 2 - hint.get_width() // 2, 370))


def draw_play_screen():
    screen.fill((5, 5, 15))

    # Player
    pygame.draw.rect(screen, (180, 180, 255),
                     (player_x, player_y,
                      GameVariables.PLAYER_SIZE, GameVariables.PLAYER_SIZE))

    hint = GameVariables.FONT_SMALL.render("WASD bewegen  |  ESC = Game Over", True, (80, 80, 100))
    screen.blit(hint, (10, GameVariables.SCREEN_HEIGHT - 30))


def draw_game_over_screen():
    screen.fill((15, 0, 0))

    txt = GameVariables.FONT_BIG.render("GAME OVER", True, (220, 30, 30))
    screen.blit(txt, (GameVariables.SCREEN_WIDTH  // 2 - txt.get_width()  // 2, 260))

    hint = GameVariables.FONT_MIDDLE.render("[ R ] Nochmal   [ ESC ] Menu", True, (140, 100, 100))
    screen.blit(hint, (GameVariables.SCREEN_WIDTH // 2 - hint.get_width() // 2, 370))


if __name__ == '__main__':
    running = True
    while running:
        events = pygame.event.get()

        for event in events:
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()

        # MAIN SCREEN
        if GameScreens.actual_screen == GameScreens.MAIN:
            draw_main_screen()
            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        player_x = GameVariables.SCREEN_WIDTH  // 2
                        player_y = GameVariables.SCREEN_HEIGHT // 2
                        GameScreens.actual_screen = GameScreens.PLAY
                    elif event.key == pygame.K_ESCAPE:
                        running = False

        # PLAY SCREEN
        elif GameScreens.actual_screen == GameScreens.PLAY:
            # Bewegung
            if keys[pygame.K_w] or keys[pygame.K_UP]:    player_y -= GameVariables.PLAYER_SPEED
            if keys[pygame.K_s] or keys[pygame.K_DOWN]:  player_y += GameVariables.PLAYER_SPEED
            if keys[pygame.K_a] or keys[pygame.K_LEFT]:  player_x -= GameVariables.PLAYER_SPEED
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]: player_x += GameVariables.PLAYER_SPEED

            draw_play_screen()

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