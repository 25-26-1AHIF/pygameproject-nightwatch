import math
import random
import pygame
from game_variables.game_variables import GameVariables
from game.utils import dist

GV = GameVariables


class Key:
    # ein aufsammelbarer schlüssel mit bob-animation

    def __init__(self, x: float, y: float, key_id: int):
        self.x         = x
        self.y         = y
        self.key_id    = key_id
        self.collected = False
        self._bob_timer = random.uniform(0, math.pi * 2)

    def update(self) -> None:
        # aktualisiert die bob-animation einmal pro frame

        self._bob_timer += 0.07

    def try_collect(self, player_x: float, player_y: float) -> bool:
        # gibt true zurück wenn der spieler nah genug ist und eingesammelt wurde

        if self.collected:
            return False
        if dist(self.x, self.y, player_x, player_y) < 30:
            self.collected = True
            return True
        return False

    def draw(self, surface: pygame.Surface, cam_x: int, cam_y: int) -> None:
        if self.collected:
            return

        bob = int(math.sin(self._bob_timer) * 4)
        sx  = int(self.x - cam_x)
        sy  = int(self.y - cam_y + bob)

        # Goldener Leuchtschein
        r = GV.SCHLUESSEL_RADIUS
        glow = pygame.Surface((r * 4, r * 4), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*GV.SCHLUESSEL_FARBE, 60), (r * 2, r * 2), r * 2)
        surface.blit(glow, (sx - r * 2, sy - r * 2))

        # Schlüsselkopf
        pygame.draw.circle(surface, GV.SCHLUESSEL_FARBE, (sx, sy), r)
        pygame.draw.circle(surface, (200, 160, 20), (sx, sy), r, 2)

        # Schlüsselbart
        pygame.draw.rect(surface, GV.SCHLUESSEL_FARBE, (sx + r - 2, sy - 3, 12, 4))
        pygame.draw.rect(surface, GV.SCHLUESSEL_FARBE, (sx + r + 4, sy - 3,  3, 7))
        pygame.draw.rect(surface, GV.SCHLUESSEL_FARBE, (sx + r + 8, sy - 3,  3, 5))


class Task:
    # abstrakte basis für alle fünf spielaufgaben

    def __init__(self, room_name: str, x: float, y: float):
        self.room_name = room_name
        self.x         = x
        self.y         = y
        self.completed = False
        self._key: Key | None = None

    @property
    def key(self) -> "Key | None":
        # der gespawnte schlüssel nach aufgabenabschluss

        return self._key

    def interact(self, player_x: float, player_y: float,
                 keys_pressed: set, events: list) -> bool:
        return False

    def draw(self, surface: pygame.Surface, cam_x: int, cam_y: int) -> None:
        pass


class CandleTask(Task):
    # alle 5 kerzen im wohnzimmer müssen mit [e] angezündet werden

    def __init__(self):
        super().__init__("R1_Wohnzimmer", 300, 228)
        self._kerzen: list[dict] = [
            {"x": 160, "y": 150, "lit": False},
            {"x": 220, "y": 120, "lit": False},
            {"x": 300, "y": 145, "lit": False},
            {"x": 400, "y": 120, "lit": False},
            {"x": 450, "y": 155, "lit": False},
        ]
        self._angezuendet: int = 0

    @property
    def lit_positions(self) -> list[tuple[float, float]]:
        # liste der weltkoordinaten bereits brennender kerzen

        return [(k["x"], k["y"]) for k in self._kerzen if k["lit"]]

    def interact(self, player_x, player_y, keys_pressed, events) -> bool:
        if self.completed:
            return False
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
                for kerze in self._kerzen:
                    if (not kerze["lit"]
                            and dist(player_x, player_y, kerze["x"], kerze["y"]) < 40):
                        kerze["lit"] = True
                        self._angezuendet += 1
                        if self._angezuendet >= GV.KERZEN_ANZAHL:
                            return True
        return False

    def draw_with_player(self, surface: pygame.Surface,
                          cam_x: int, cam_y: int,
                          player_x: float, player_y: float) -> None:
        for kerze in self._kerzen:
            sx = int(kerze["x"] - cam_x)
            sy = int(kerze["y"] - cam_y)

            kerzen_f = (220, 200, 150) if kerze["lit"] else (180, 170, 140)
            pygame.draw.rect(surface, kerzen_f, (sx - 4, sy - 10, 8, 18))

            if kerze["lit"]:
                t     = pygame.time.get_ticks() / 200
                flick = int(math.sin(t + kerze["x"]) * 2)
                aeuss = [(sx + flick, sy - 16),
                         (sx - 5 + flick, sy - 10),
                         (sx + 5 + flick, sy - 10)]
                inner = [(sx + flick, sy - 14),
                         (sx - 2 + flick, sy - 10),
                         (sx + 2 + flick, sy - 10)]
                pygame.draw.polygon(surface, (240, 150, 30), aeuss)
                pygame.draw.polygon(surface, (255, 220, 80), inner)
            else:
                pygame.draw.line(surface, (60, 40, 20),
                                 (sx, sy - 10), (sx, sy - 14), 2)
                if dist(player_x, player_y, kerze["x"], kerze["y"]) < 40:
                    font = pygame.font.SysFont("monospace", 13)
                    hint = font.render("[E] anzünden", True, (255, 240, 120))
                    surface.blit(hint, (sx - 40, sy - 30))

    def draw(self, surface, cam_x, cam_y) -> None:
        self.draw_with_player(surface, cam_x, cam_y, -9999, -9999)


class SwitchTask(Task):
    # alle 3 schalter in der küche müssen umgelegt werden

    def __init__(self):
        super().__init__("R2_Küche", 756, 228)
        self._schalter: list[dict] = [
            {"x": 620, "y": 160, "on": False},
            {"x": 756, "y": 145, "on": False},
            {"x": 900, "y": 160, "on": False},
        ]
        self._aktiviert: int = 0

    def interact(self, player_x, player_y, keys_pressed, events) -> bool:
        if self.completed:
            return False
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
                for schalter in self._schalter:
                    if (not schalter["on"]
                            and dist(player_x, player_y,
                                     schalter["x"], schalter["y"]) < 40):
                        schalter["on"] = True
                        self._aktiviert += 1
                        if self._aktiviert >= GV.SCHALTER_ANZAHL:
                            return True
        return False

    def draw_with_player(self, surface: pygame.Surface,
                          cam_x: int, cam_y: int,
                          player_x: float, player_y: float) -> None:
        for schalter in self._schalter:
            sx = int(schalter["x"] - cam_x)
            sy = int(schalter["y"] - cam_y)

            pygame.draw.rect(surface, (60, 60, 70),
                             (sx - 10, sy - 14, 20, 28), border_radius=3)
            hebel_f = (80, 220, 80) if schalter["on"] else (220, 80, 80)
            rect    = ((sx - 5, sy - 10, 10, 10)
                       if schalter["on"]
                       else (sx - 5, sy, 10, 10))
            pygame.draw.rect(surface, hebel_f, rect, border_radius=2)

            if (not schalter["on"]
                    and dist(player_x, player_y,
                             schalter["x"], schalter["y"]) < 40):
                font = pygame.font.SysFont("monospace", 13)
                hint = font.render("[E] umlegen", True, (255, 240, 120))
                surface.blit(hint, (sx - 35, sy - 28))


class BoxTask(Task):
    # eine kiste muss im schlafzimmer zur zielmarkierung getragen werden

    def __init__(self):
        super().__init__("R3_Schlafzimmer", 1100, 150)
        self._kiste_x: float = 1100.0
        self._kiste_y: float = 150.0
        self._ziel_x:  float = 1340.0
        self._ziel_y:  float = 300.0
        self._traegt:  bool  = False

    def interact(self, player_x, player_y, keys_pressed, events) -> bool:
        if self.completed:
            return False
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
                if not self._traegt:
                    if dist(player_x, player_y, self._kiste_x, self._kiste_y) < 40:
                        self._traegt = True
                else:
                    self._traegt = False
                    if dist(self._kiste_x, self._kiste_y,
                            self._ziel_x, self._ziel_y) < 50:
                        return True
        return False

    def update_carry(self, player_x: float, player_y: float) -> None:
        # bewegt die kiste mit dem spieler wenn sie getragen wird

        if self._traegt:
            self._kiste_x = player_x + 20
            self._kiste_y = player_y + 20

    def draw_with_player(self, surface: pygame.Surface,
                          cam_x: int, cam_y: int,
                          player_x: float, player_y: float) -> None:
        tx = int(self._ziel_x - cam_x)
        ty = int(self._ziel_y - cam_y)
        pygame.draw.rect(surface, (40, 80, 40), (tx - 25, ty - 25, 50, 50), 2)
        font_sm = pygame.font.SysFont("monospace", 11)
        lbl     = font_sm.render("Ziel", True, (80, 180, 80))
        surface.blit(lbl, (tx - 12, ty - 10))

        bx  = int(self._kiste_x - cam_x)
        by  = int(self._kiste_y - cam_y)
        col = (200, 150, 80) if self._traegt else (160, 110, 60)
        pygame.draw.rect(surface, col, (bx - 20, by - 20, 40, 40))
        pygame.draw.rect(surface, (100, 70, 30), (bx - 20, by - 20, 40, 40), 2)
        pygame.draw.line(surface, (100, 70, 30), (bx - 20, by - 20), (bx + 20, by + 20), 2)
        pygame.draw.line(surface, (100, 70, 30), (bx + 20, by - 20), (bx - 20, by + 20), 2)

        hint_font = pygame.font.SysFont("monospace", 13)
        if not self._traegt and dist(player_x, player_y, self._kiste_x, self._kiste_y) < 40:
            hint = hint_font.render("[E] aufnehmen", True, (255, 240, 120))
            surface.blit(hint, (bx - 45, by - 38))
        elif self._traegt:
            hint = hint_font.render("[E] ablegen", True, (255, 240, 120))
            surface.blit(hint, (bx - 35, by - 38))


class MemoryTask(Task):
    # zufällige symbolsequenz merken und korrekt eingeben (tasten 1-6)

    SYMBOLE = ["★", "♦", "▲", "●", "◆", "■"]

    def __init__(self):
        super().__init__("R4_Büro", 1668, 228)
        self._sequenz: list[int] = [
            random.randint(0, len(self.SYMBOLE) - 1)
            for _ in range(GV.MEMORY_GROESSE)
        ]
        self._zeige_phase: bool = True
        self._zeige_timer: int  = 180
        self._eingabe:     list[int] = []
        self._buttons:     list[dict] = []
        self._init_buttons()
        self._fehler:       bool = False
        self._fehler_timer: int  = 0
        self._nahe:         bool = False

    def _init_buttons(self) -> None:
        n      = len(self.SYMBOLE)
        bw     = 36
        luecke = 8
        gesamt = n * bw + (n - 1) * luecke
        sx     = self.x - gesamt // 2
        for i in range(n):
            bx = sx + i * (bw + luecke)
            self._buttons.append({
                "x": bx, "y": self.y + 30, "sym": i, "w": bw, "h": 36
            })

    def interact(self, player_x, player_y, keys_pressed, events) -> bool:
        if self.completed:
            return False

        self._nahe = dist(player_x, player_y, self.x, self.y) < 80
        if not self._nahe:
            return False

        if self._zeige_phase:
            self._zeige_timer -= 1
            if self._zeige_timer <= 0:
                self._zeige_phase = False
            return False

        if self._fehler:
            self._fehler_timer -= 1
            if self._fehler_timer <= 0:
                self._fehler  = False
                self._eingabe = []
            return False

        for event in events:
            if event.type == pygame.KEYDOWN:
                if pygame.K_1 <= event.key <= pygame.K_6:
                    sym_idx = event.key - pygame.K_1
                    if sym_idx < len(self.SYMBOLE):
                        self._eingabe.append(sym_idx)
                        idx = len(self._eingabe) - 1
                        if self._eingabe[idx] != self._sequenz[idx]:
                            self._fehler       = True
                            self._fehler_timer = 90
                            return False
                        if len(self._eingabe) == len(self._sequenz):
                            return True
        return False

    def draw_with_player(self, surface: pygame.Surface,
                          cam_x: int, cam_y: int,
                          player_x: float, player_y: float) -> None:
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)

        pygame.draw.rect(surface, (80, 55, 30), (sx - 50, sy - 10, 100, 60))
        pygame.draw.rect(surface, (60, 40, 20), (sx - 50, sy - 10, 100, 60), 2)

        nahe = dist(player_x, player_y, self.x, self.y) < 80
        if not nahe:
            font_sm = pygame.font.SysFont("monospace", 12)
            lbl = font_sm.render("Schreibtisch", True, (160, 140, 100))
            surface.blit(lbl, (sx - 38, sy + 5))
            return

        font_gr = pygame.font.SysFont("monospace", 20, bold=True)
        font_sm = pygame.font.SysFont("monospace", 13)

        sym_farben = [(255,100,100),(100,200,255),(255,200,50),
                      (100,255,150),(200,100,255),(255,150,50)]

        if self._zeige_phase:
            lbl = font_sm.render("Merke dir die Reihenfolge!", True, (255, 230, 100))
            surface.blit(lbl, (sx - 80, sy - 55))
            for i, sym_idx in enumerate(self._sequenz):
                txt = font_gr.render(self.SYMBOLE[sym_idx], True, sym_farben[sym_idx])
                surface.blit(txt, (sx - len(self._sequenz) * 18 + i * 36, sy - 30))
        else:
            lbl = font_sm.render("Eingabe (Tasten 1-6):", True, (200, 200, 200))
            surface.blit(lbl, (sx - 70, sy - 55))

            for b in self._buttons:
                bsx = int(b["x"] - cam_x)
                bsy = int(b["y"] - cam_y)
                col = sym_farben[b["sym"]]
                pygame.draw.rect(surface, (40, 40, 50),
                                 (bsx, bsy, b["w"], b["h"]), border_radius=4)
                pygame.draw.rect(surface, col,
                                 (bsx, bsy, b["w"], b["h"]), 2, border_radius=4)
                ctxt = font_gr.render(self.SYMBOLE[b["sym"]], True, col)
                surface.blit(ctxt, (bsx + 6, bsy + 6))
                num = font_sm.render(str(b["sym"] + 1), True, (150, 150, 150))
                surface.blit(num, (bsx + 13, bsy + b["h"] + 3))

            for i, sym_idx in enumerate(self._eingabe):
                txt = font_gr.render(self.SYMBOLE[sym_idx], True, sym_farben[sym_idx])
                surface.blit(txt, (sx - 60 + i * 30, sy - 30))

            if self._fehler:
                err = font_sm.render("Falsch! Nochmal...", True, (220, 60, 60))
                surface.blit(err, (sx - 60, sy + 80))


class ComboTask(Task):
    # dreistelliger zahlencode am keller-schloss (kombination: 2-4-1)

    def __init__(self):
        super().__init__("R5_Keller", 300, 732)
        self._eingabe:      list[int] = []
        self._code:         tuple     = GV.KOMBINATION
        self._nahe:         bool      = False
        self._fehler:       bool      = False
        self._fehler_timer: int       = 0

    def interact(self, player_x, player_y, keys_pressed, events) -> bool:
        if self.completed:
            return False

        self._nahe = dist(player_x, player_y, self.x, self.y) < 70
        if not self._nahe:
            return False

        if self._fehler:
            self._fehler_timer -= 1
            if self._fehler_timer <= 0:
                self._fehler  = False
                self._eingabe = []
            return False

        for event in events:
            if event.type == pygame.KEYDOWN:
                if pygame.K_0 <= event.key <= pygame.K_9:
                    ziffer = event.key - pygame.K_0
                    if len(self._eingabe) < len(self._code):
                        self._eingabe.append(ziffer)
                        if len(self._eingabe) == len(self._code):
                            if tuple(self._eingabe) == self._code:
                                return True
                            else:
                                self._fehler       = True
                                self._fehler_timer = 90
                elif event.key == pygame.K_BACKSPACE:
                    if self._eingabe:
                        self._eingabe.pop()
        return False

    def draw_with_player(self, surface: pygame.Surface,
                          cam_x: int, cam_y: int,
                          player_x: float, player_y: float) -> None:
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)

        pygame.draw.rect(surface, (70, 65, 60),
                         (sx - 30, sy - 25, 60, 50), border_radius=5)
        pygame.draw.rect(surface, (120, 110, 90),
                         (sx - 30, sy - 25, 60, 50), 2, border_radius=5)

        font_sm = pygame.font.SysFont("monospace", 13)
        if not self._nahe:
            lbl = font_sm.render("Schloss", True, (160, 150, 130))
            surface.blit(lbl, (sx - 22, sy - 8))
            return

        font_gr = pygame.font.SysFont("monospace", 22, bold=True)
        anzeige = "".join(str(d) for d in self._eingabe)
        anzeige += "_" * (len(self._code) - len(self._eingabe))
        farbe   = (220, 60, 60) if self._fehler else (100, 220, 120)
        txt = font_gr.render(anzeige, True, farbe)
        surface.blit(txt, (sx - txt.get_width() // 2, sy - 12))

        hint1 = font_sm.render("Ziffern eingeben",    True, (180, 180, 180))
        hint2 = font_sm.render("[Backspace] löschen", True, (130, 130, 130))
        surface.blit(hint1, (sx - hint1.get_width() // 2, sy + 25))
        surface.blit(hint2, (sx - hint2.get_width() // 2, sy + 40))

        if self._fehler:
            err = font_sm.render("Falscher Code!", True, (220, 60, 60))
            surface.blit(err, (sx - err.get_width() // 2, sy + 55))


class HintNote:
    # ein lesbarer hinweiszettel für den zahlenkombinations-code

    def __init__(self, x: float, y: float, hinweis_text: str):
        self.x            = x
        self.y            = y
        self.hinweis_text = hinweis_text
        self._gelesen     = False

    def try_read(self, player_x: float, player_y: float, events: list) -> None:
        nahe = dist(player_x, player_y, self.x, self.y) < 40
        if nahe:
            for event in events:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
                    self._gelesen = not self._gelesen
        else:
            self._gelesen = False

    def draw(self, surface: pygame.Surface,
             cam_x: int, cam_y: int,
             player_x: float, player_y: float) -> None:
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)

        pygame.draw.rect(surface, (220, 210, 170), (sx - 8, sy - 12, 16, 20))
        pygame.draw.rect(surface, (140, 130, 100), (sx - 8, sy - 12, 16, 20), 1)
        for li in range(3):
            pygame.draw.line(surface, (140, 130, 100),
                             (sx - 5, sy - 8 + li * 5),
                             (sx + 5, sy - 8 + li * 5), 1)

        font = pygame.font.SysFont("monospace", 13)
        nahe = dist(player_x, player_y, self.x, self.y) < 40

        if nahe and not self._gelesen:
            hint = font.render("[E] lesen", True, (255, 240, 120))
            surface.blit(hint, (sx - 28, sy - 28))

        if self._gelesen:
            zeilen = self.hinweis_text.split("\n")
            bw = max(len(z) for z in zeilen) * 8 + 20
            bh = len(zeilen) * 18 + 16
            bg = pygame.Surface((bw, bh), pygame.SRCALPHA)
            bg.fill((20, 15, 10, 220))
            bx = sx - bw // 2
            by = sy - bh - 20
            surface.blit(bg, (bx, by))
            pygame.draw.rect(surface, (160, 140, 100), (bx, by, bw, bh), 1)
            for i, zeile in enumerate(zeilen):
                txt = font.render(zeile, True, (220, 210, 170))
                surface.blit(txt, (bx + 10, by + 8 + i * 18))


class BatteryPickup:
    # eine batterie zum aufladen – kann nur eingesammelt werden wenn akku unter 15% ist

    WIEDERHERSTELLUNG = 40.0   # wie viel prozent akku man bekommt
    SAMMEL_ABSTAND    = 35     # wie nah man rangehen muss
    SCHWELLE          = 15.0   # unter diesem akku-level kann man einsammeln

    def __init__(self, x: float, y: float):
        self.x         = x
        self.y         = y
        self.collected = False
        self._bob      = random.uniform(0, math.pi * 2)

    def update(self) -> None:
        self._bob += 0.05

    def try_collect(self, player_x: float, player_y: float,
                    player_battery: float, events: list) -> float:
        # gibt die akkumenge zurück die hinzugefügt werden soll (0.0 wenn nichts)

        if self.collected:
            return 0.0
        if dist(player_x, player_y, self.x, self.y) >= self.SAMMEL_ABSTAND:
            return 0.0
        # akku noch zu voll - nicht einsammelbar
        if player_battery >= self.SCHWELLE:
            return 0.0
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
                self.collected = True
                return self.WIEDERHERSTELLUNG
        return 0.0

    def draw(self, surface: pygame.Surface,
             cam_x: int, cam_y: int,
             player_x: float, player_y: float,
             player_battery: float) -> None:
        if self.collected:
            return

        bob = int(math.sin(self._bob) * 3)
        sx  = int(self.x - cam_x)
        sy  = int(self.y - cam_y + bob)

        # leuchtspur
        glow = pygame.Surface((56, 44), pygame.SRCALPHA)
        pygame.draw.ellipse(glow, (30, 180, 30, 45), (0, 0, 56, 44))
        surface.blit(glow, (sx - 28, sy - 22))

        # batterie-körper
        pygame.draw.rect(surface, (45, 160, 45), (sx - 13, sy - 8, 22, 16), border_radius=3)
        pygame.draw.rect(surface, (80, 220, 80), (sx - 13, sy - 8, 22, 16), 2, border_radius=3)
        # pol (kleines rechteck rechts)
        pygame.draw.rect(surface, (80, 220, 80), (sx + 9, sy - 4, 4, 8), border_radius=1)
        # ladebalken innen
        pygame.draw.rect(surface, (100, 255, 100), (sx - 11, sy - 5, 14, 10), border_radius=1)

        # hinweistext wenn nah genug
        nahe = dist(player_x, player_y, self.x, self.y) < self.SAMMEL_ABSTAND
        if nahe:
            font = pygame.font.SysFont("monospace", 12)
            if player_battery < self.SCHWELLE:
                hint = font.render("[E] Akku +40%", True, (100, 255, 100))
            else:
                hint = font.render("Akku noch voll", True, (130, 130, 80))
            surface.blit(hint, (sx - hint.get_width() // 2, sy - 26))


class ItemManager:
    # verwaltet alle aufgaben, schlüssel und hinweiszettel im spiel

    def __init__(self, sounds):
        self._sounds = sounds
        self.keys_collected: int = 0

        self.candle_task = CandleTask()
        self.switch_task = SwitchTask()
        self.box_task    = BoxTask()
        self.memory_task = MemoryTask()
        self.combo_task  = ComboTask()

        self._tasks: list[Task] = [
            self.candle_task, self.switch_task,
            self.box_task, self.memory_task, self.combo_task,
        ]

        self._gespawnte_schluessel: list[Key] = []

        self._hinweise: list[HintNote] = [
            HintNote(756, 150,
                     "Notiz:\nDer Code am Schloss\nim Keller lautet:\n"
                     + "-".join(str(d) for d in GV.KOMBINATION)),
            HintNote(1600, 732,
                     "Erinnerung:\nAlle Aufgaben erledigen\num Schlüssel zu\nbekommen!"),
        ]

        # batterie-pickups: nur einsammelbar wenn akku unter 15%
        self._batterien: list[BatteryPickup] = [
            BatteryPickup(220,  300),   # wohnzimmer (R1)
            BatteryPickup(880,  300),   # küche (R2)
            BatteryPickup(1480, 300),   # schlafzimmer (R3)
            BatteryPickup(1200, 850),   # eingangsbereich
        ]

    def update(self, player_x: float, player_y: float,
               events: list, keys_pressed: set,
               player_battery: float = 100.0) -> float:
        # einmal pro frame – gibt aufgeladene akkumenge zurück (0 wenn nichts eingesammelt)

        self.box_task.update_carry(player_x, player_y)

        for i, task in enumerate(self._tasks):
            if not task.completed:
                erledigt = task.interact(player_x, player_y, keys_pressed, events)
                if erledigt:
                    task.completed = True
                    schluessel = Key(player_x, player_y - 40, i)
                    self._gespawnte_schluessel.append(schluessel)
                    if self._sounds:
                        self._sounds.play("task_done")

        for schluessel in self._gespawnte_schluessel:
            schluessel.update()
            if not schluessel.collected:
                if schluessel.try_collect(player_x, player_y):
                    self.keys_collected += 1
                    if self._sounds:
                        self._sounds.play("key_pickup")

        for hinweis in self._hinweise:
            hinweis.try_read(player_x, player_y, events)

        # batterie-pickups prüfen
        akku_gewinn = 0.0
        for batterie in self._batterien:
            batterie.update()
            gewinn = batterie.try_collect(player_x, player_y, player_battery, events)
            if gewinn > 0:
                akku_gewinn += gewinn
                if self._sounds:
                    self._sounds.play("key_pickup")
        return akku_gewinn

    @property
    def all_tasks_done(self) -> bool:
        # true wenn alle 5 aufgaben abgeschlossen sind

        return all(t.completed for t in self._tasks)

    @property
    def lit_candle_positions(self) -> list[tuple[float, float]]:
        # weltkoordinaten aller brennenden kerzen (für die lichtberechnung)

        if not self.candle_task.completed:
            return self.candle_task.lit_positions
        return [(k["x"], k["y"]) for k in self.candle_task._kerzen]

    def draw(self, surface: pygame.Surface,
             cam_x: int, cam_y: int,
             player_x: float, player_y: float,
             player_battery: float = 100.0) -> None:
        # zeichnet alle items, aufgaben, hinweise und batterie-pickups

        self.candle_task.draw_with_player(surface, cam_x, cam_y, player_x, player_y)
        self.switch_task.draw_with_player(surface, cam_x, cam_y, player_x, player_y)
        self.box_task.draw_with_player(surface, cam_x, cam_y, player_x, player_y)
        self.memory_task.draw_with_player(surface, cam_x, cam_y, player_x, player_y)
        self.combo_task.draw_with_player(surface, cam_x, cam_y, player_x, player_y)

        for schluessel in self._gespawnte_schluessel:
            schluessel.draw(surface, cam_x, cam_y)

        for hinweis in self._hinweise:
            hinweis.draw(surface, cam_x, cam_y, player_x, player_y)

        for batterie in self._batterien:
            batterie.draw(surface, cam_x, cam_y, player_x, player_y, player_battery)
