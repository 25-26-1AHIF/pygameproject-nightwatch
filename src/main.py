import pygame
from game_variables.game_variables import GameVariables as GV
from game_variables.game_variables import GameScreens
from game.player  import Player
from game.monster import Monster
from game import room


def main_screen(screen: pygame.Surface, clock: pygame.time.Clock) -> str:
    pygame.display.set_caption("Nightwatch - Menü")

    titel_text   = GV.FONT_BIG.render("NIGHTWATCH", True, (200, 30, 30))
    starten_text = GV.FONT_MIDDLE.render("Spiel starten", True, (200, 200, 200))

    titel_rect   = titel_text.get_rect(center=(GV.SCREEN_WIDTH / 2, 280))
    starten_rect = starten_text.get_rect(center=(GV.SCREEN_WIDTH / 2, 380))

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return GameScreens.EXIT
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return GameScreens.EXIT
            if event.type == pygame.MOUSEBUTTONDOWN:
                if starten_rect.collidepoint(event.pos):
                    return GameScreens.PLAY

        screen.fill((8, 8, 15))
        screen.blit(source=titel_text,   dest=titel_rect)
        screen.blit(source=starten_text, dest=starten_rect)

        # roter Rahmen um den Startknopf
        pygame.draw.rect(surface=screen, rect=starten_rect, color="red", width=1)

        hint = GV.FONT_SMALL.render("Klick auf \"Spiel starten\" oder ESC zum Beenden",
                                    True, (80, 70, 80))
        hint_rect = hint.get_rect(center=(GV.SCREEN_WIDTH / 2, GV.SCREEN_HEIGHT - 30))
        screen.blit(hint, hint_rect)

        pygame.display.flip()
        clock.tick(GV.FPS)


def play_screen(screen: pygame.Surface, clock: pygame.time.Clock) -> str:
    pygame.display.set_caption("Nightwatch - Spiel")

    player  = Player(screen=screen, x=100, y=100)
    monster = Monster(screen=screen, x=900, y=550)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return GameScreens.EXIT
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return GameScreens.MAIN

        # Zeichnen
        screen.fill((0, 0, 0))
        room.zeichnen(screen)

        player.update_and_draw()
        monster.update_and_draw(player.xpos, player.ypos)

        # Dunkelheits-Overlay drüber
        dunkelheit_zeichnen(screen, player.xpos + GV.SQUARE_SIZE // 2,
                                    player.ypos + GV.SQUARE_SIZE // 2)

        # Prüfe ob Monster Spieler erwischt hat
        if monster.trifft_spieler(player.xpos, player.ypos):
            return GameScreens.GAME_OVER

        pygame.display.flip()
        clock.tick(GV.FPS)


def game_over_screen(screen: pygame.Surface, clock: pygame.time.Clock) -> str:
    pygame.display.set_caption("Nightwatch - Game Over")

    go_text     = GV.FONT_BIG.render("ERWISCHT!", True, (220, 30, 30))
    wieder_text = GV.FONT_MIDDLE.render("Nochmal Spielen", True, (200, 200, 200))
    menu_text   = GV.FONT_MIDDLE.render("Hauptmenü", True, (200, 200, 200))

    go_rect     = go_text.get_rect(center=(GV.SCREEN_WIDTH / 2, 260))
    wieder_rect = wieder_text.get_rect(center=(GV.SCREEN_WIDTH / 2 - 120, 380))
    menu_rect   = menu_text.get_rect(center=(GV.SCREEN_WIDTH / 2 + 120, 380))

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return GameScreens.EXIT
            if event.type == pygame.MOUSEBUTTONDOWN:
                if wieder_rect.collidepoint(event.pos):
                    return GameScreens.PLAY
                if menu_rect.collidepoint(event.pos):
                    return GameScreens.MAIN
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    return GameScreens.PLAY
                if event.key == pygame.K_ESCAPE:
                    return GameScreens.MAIN

        screen.fill((12, 0, 0))
        screen.blit(go_text,     go_rect)
        screen.blit(wieder_text, wieder_rect)
        screen.blit(menu_text,   menu_rect)

        pygame.draw.rect(surface=screen, rect=wieder_rect, color="red",  width=1)
        pygame.draw.rect(surface=screen, rect=menu_rect,   color="gray", width=1)

        pygame.display.flip()
        clock.tick(GV.FPS)


# KI CODE ANFANG
# Dunkelheits-Overlay mit transparentem Kreis (Sichtbereich um den Spieler)
def dunkelheit_zeichnen(screen: pygame.Surface, cx: int, cy: int):
    dark = pygame.Surface((GV.SCREEN_WIDTH, GV.SCREEN_HEIGHT), pygame.SRCALPHA)
    dark.fill((0, 0, 0, 255))

    pygame.draw.circle(dark, (0, 0, 0, 0),   (cx, cy), 150)
    pygame.draw.circle(dark, (0, 0, 0, 80),  (cx, cy), 190)
    pygame.draw.circle(dark, (0, 0, 0, 150), (cx, cy), 230)
    pygame.draw.circle(dark, (0, 0, 0, 210), (cx, cy), 270)

    screen.blit(dark, (0, 0))
# KI CODE ENDE


def main():
    GV.init()
    screen = pygame.display.set_mode((GV.SCREEN_WIDTH, GV.SCREEN_HEIGHT))
    clock  = pygame.time.Clock()

    while True:
        if GameScreens.actual_screen == GameScreens.MAIN:
            GameScreens.actual_screen = main_screen(screen, clock)

        elif GameScreens.actual_screen == GameScreens.PLAY:
            GameScreens.actual_screen = play_screen(screen, clock)

        elif GameScreens.actual_screen == GameScreens.GAME_OVER:
            GameScreens.actual_screen = game_over_screen(screen, clock)

        elif GameScreens.actual_screen == GameScreens.EXIT:
            break

    pygame.quit()


if __name__ == "__main__":
    main()
