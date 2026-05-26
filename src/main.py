import pygame
import sys
from game.game_variables import GameVariables, GameScreens
from room import draw_room
from player import Player
from assets import images
GameVariables.init()

screen = pygame.display.set_mode((GameVariables.SCREEN_WIDTH, GameVariables.SCREEN_HEIGHT))
pygame.display.set_caption(GameVariables.TITLE)
clock = pygame.time.Clock()

player = Player(200, 200)



background_main = pygame.image.load("assets/images/main_screen_background.png").convert()
# pygame.transform.scale KI CODE
background_main = pygame.transform.scale(background_main, (GameVariables.SCREEN_WIDTH, GameVariables.SCREEN_HEIGHT))


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
    screen.blit(background_main, (0, 0))

    #title = GameVariables.FONT_BIG.render("NIGHTWATCH", True, (200, 40, 40))
    #screen.blit(title, (GameVariables.SCREEN_WIDTH  // 2 - title.get_width()  // 2, 80))

    #by = GameVariables.FONT_SMALL.render("by Fabian & Onur", True,(200,40,40))
    #screen.blit(by,(GameVariables.SCREEN_WIDTH // 2 - by.get_width() // 2, 190))

    start = GameVariables.FONT_MIDDLE.render("Starten", True, (255, 255, 255))
    starten_rect = start.get_rect(center=(GameVariables.SCREEN_WIDTH // 2, 320))
    screen.blit(start, starten_rect)

    score_board = GameVariables.FONT_MIDDLE.render("Erklärung", True, (255, 255, 255))
    scoreboard_rect = score_board.get_rect(center=(GameVariables.SCREEN_WIDTH // 2, 380))
    screen.blit(score_board,scoreboard_rect)

    leave = GameVariables.FONT_MIDDLE.render("Beenden", True, (255, 255, 255))
    leave_rect = leave.get_rect(center=(GameVariables.SCREEN_WIDTH // 2, 440))
    screen.blit(leave,leave_rect)

    return start, starten_rect, score_board, scoreboard_rect, leave_rect

def erklärung_screen():
    screen.fill((0, 0, 0))

    # KI CODE
    panel = pygame.Surface((900, 420), pygame.SRCALPHA)
    panel.fill((0, 0, 0, 160))
    screen.blit(panel, (GameVariables.SCREEN_WIDTH // 2 - 450, 120))
    # KI CODE

    titel = GameVariables.FONT_BIG.render("NIGHTWATCH", True, (200, 40, 40))
    screen.blit(titel, (GameVariables.SCREEN_WIDTH // 2 - titel.get_width() // 2, 40))

    # KI CODE
    zeilen = [
        "Du bist ein Nachtwächter in einem verlassenen Museum.",
        "Löse in 5 Räumen je eine Aufgabe und sammle alle 5 Schlüssel.",
        "Fliehe durch die Fluchttür — ohne vom Monster erwischt zu werden.",
        "",
        "Deine Taschenlampe ist dein einziges Licht,",
        "aber sie lockt das Monster an.",
        "",
        "Schleich dich durch, behalte deine Batterie im Blick",
        "und entkome so schnell wie möglich.",
    ]
    y = 160
    for zeile in zeilen:
        txt = GameVariables.FONT_SMALL.render(zeile, True, (220, 220, 220))
        screen.blit(txt, (GameVariables.SCREEN_WIDTH // 2 - txt.get_width() // 2, y))
        y += 35
    # KI CODE

    hinweis = GameVariables.FONT_SMALL.render("[ESC] Zurück", True, (150, 150, 160))
    screen.blit(hinweis, (GameVariables.SCREEN_WIDTH // 2 - hinweis.get_width() // 2, 560))
def draw_game_over_screen():
    screen.fill((15, 0, 0))

    txt = GameVariables.FONT_BIG.render("GAME OVER", True, (220, 30, 30))
    screen.blit(txt, (GameVariables.SCREEN_WIDTH  // 2 - txt.get_width()  // 2, 260))

    ESC = GameVariables.FONT_MIDDLE.render("[ESC] Menü",True,(220,30,30))
    screen.blit(ESC,(GameVariables.SCREEN_WIDTH// 2 - ESC.get_width() // 2, 400))


if __name__ == "__main__":
    running = True
    while running:
        events = pygame.event.get()
        keys = pygame.key.get_pressed()

        for event in events:
            if event.type == pygame.QUIT:
                running = False

        # MAIN SCREEN
        if GameScreens.actual_screen == GameScreens.MAIN:
            start, starten_rect, score_board, scoreboard_rect, leave_rect = draw_main_screen()

            maus_x, maus_y = pygame.mouse.get_pos()
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if starten_rect.collidepoint(maus_x, maus_y):
                        player = Player(200, 200)   # Spieler zuruecksetzen
                        GameScreens.actual_screen = GameScreens.PLAY
                    elif leave_rect.collidepoint(maus_x, maus_y):
                        running = False
                    elif scoreboard_rect.collidepoint(maus_x,maus_y):
                        GameScreens.actual_screen = GameScreens.TUT




        # SCOREBOARD SCREEN
        elif GameScreens.actual_screen == GameScreens.TUT:
            erklärung_screen()
            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        GameScreens.actual_screen = GameScreens.MAIN


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