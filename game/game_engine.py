import math
from array import array
import pygame
from game.round import Round

# Difficulty presets: number of rounds and random wait range (ms)
DIFFICULTIES = {
    "Easy":   {"rounds": 3, "min_wait": 2000, "max_wait": 5000},
    "Medium": {"rounds": 5, "min_wait": 1000, "max_wait": 4000},
    "Hard":   {"rounds": 7, "min_wait": 500,  "max_wait": 6000},
}
DIFFICULTY_NAMES = list(DIFFICULTIES.keys())

MENU, PLAYING, RESULTS = "menu", "playing", "results"

RESULT_PAUSE_MS = 1200    # pause between rounds
RESULTS_LOCKOUT_MS = 700  # ignore input briefly when results appear

GREY = (110, 110, 110)
GREEN = (46, 204, 113)
RED = (192, 57, 43)
DARK = (30, 30, 40)
WHITE = (255, 255, 255)
LIGHT = (200, 200, 210)


class GameEngine:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.should_quit = False

        self.font_big = pygame.font.Font(None, 72)
        self.font_mid = pygame.font.Font(None, 40)
        self.font_small = pygame.font.Font(None, 26)

        self.state = MENU
        self.difficulty = None
        self.cfg = None
        self.results = []          # ms value, or None for a false start
        self.round = None
        self.round_number = 0
        self.total_rounds = 0
        self.results_tick = 0

        bw, bh = 300, 60
        self.button_rects = {
            name: pygame.Rect((width - bw) // 2, 130 + i * 80, bw, bh)
            for i, name in enumerate(DIFFICULTY_NAMES)
        }

        self.sounds = {}
        self._build_sounds()

    # ------------------------------------------------------------ sound
    def _make_sound(self, notes):
        rate, _, channels = pygame.mixer.get_init()
        samples = array("h")
        for freq, ms in notes:
            n = int(rate * ms / 1000)
            fade = max(1, int(rate * 0.01))
            for i in range(n):
                env = min(1.0, i / fade, (n - i) / fade)
                v = int(32767 * 0.4 * env * math.sin(2 * math.pi * freq * i / rate))
                for _ in range(channels):
                    samples.append(v)
        return pygame.mixer.Sound(buffer=samples)

    def _build_sounds(self):
        if not pygame.mixer.get_init():
            return  # no audio device; game still works silently
        try:
            self.sounds["go"] = self._make_sound([(880, 150)])
            self.sounds["false"] = self._make_sound([(160, 350)])
            self.sounds["end"] = self._make_sound([(523, 150), (659, 150), (784, 300)])
        except Exception:
            self.sounds = {}

    def _play(self, name):
        sound = self.sounds.get(name)
        if sound:
            sound.play()

    # ------------------------------------------------------------ flow
    def _start_session(self, name):
        self.difficulty = name
        self.cfg = DIFFICULTIES[name]
        self.results = []
        self.round_number = 0
        self.total_rounds = self.cfg["rounds"]
        self.state = PLAYING
        self._next_round()

    def _next_round(self):
        self.round_number += 1
        self.round = Round(self.cfg["min_wait"], self.cfg["max_wait"])

    def _react(self):
        outcome = self.round.react()
        if outcome == Round.RESULT:
            self.results.append(self.round.reaction_ms)
        elif outcome == Round.FALSE_START:
            self.results.append(None)
            self._play("false")

    def _valid_times(self):
        return [r for r in self.results if r is not None]

    def _average(self):
        valid = self._valid_times()
        return sum(valid) / len(valid) if valid else None

    # ------------------------------------------------------------ input
    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.should_quit = True
            return

        if self.state == MENU:
            if event.type == pygame.KEYDOWN:
                keys = {pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2,
                        pygame.K_KP1: 0, pygame.K_KP2: 1, pygame.K_KP3: 2}
                if event.key in keys:
                    self._start_session(DIFFICULTY_NAMES[keys[event.key]])
                elif event.key in (pygame.K_q, pygame.K_ESCAPE):
                    self.should_quit = True
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for name, rect in self.button_rects.items():
                    if rect.collidepoint(event.pos):
                        self._start_session(name)
                        break

        elif self.state == PLAYING:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self._react()
                elif event.key == pygame.K_ESCAPE:
                    self.state = MENU
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._react()

        elif self.state == RESULTS:
            if pygame.time.get_ticks() - self.results_tick < RESULTS_LOCKOUT_MS:
                return
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER,
                                 pygame.K_SPACE, pygame.K_r):
                    self.state = MENU
                elif event.key in (pygame.K_q, pygame.K_ESCAPE):
                    self.should_quit = True

    # ------------------------------------------------------------ update
    def update(self):
        if self.state != PLAYING:
            return
        r = self.round
        if r.update():
            self._play("go")
        if r.finished and r.ms_since_end() >= RESULT_PAUSE_MS:
            if self.round_number >= self.total_rounds:
                self.state = RESULTS
                self.results_tick = pygame.time.get_ticks()
                self._play("end")
            else:
                self._next_round()

    # ------------------------------------------------------------ render
    def _text(self, screen, text, font, color, center):
        surf = font.render(text, True, color)
        screen.blit(surf, surf.get_rect(center=center))

    def render(self, screen):
        if self.state == MENU:
            self._render_menu(screen)
        elif self.state == PLAYING:
            self._render_play(screen)
        else:
            self._render_results(screen)

    def _render_menu(self, screen):
        screen.fill(DARK)
        cx = self.width // 2
        self._text(screen, "Reaction Time Tester", self.font_mid, WHITE, (cx, 50))
        self._text(screen, "Choose a difficulty (click or press 1/2/3)",
                   self.font_small, LIGHT, (cx, 95))
        mouse = pygame.mouse.get_pos()
        for i, name in enumerate(DIFFICULTY_NAMES):
            rect = self.button_rects[name]
            cfg = DIFFICULTIES[name]
            color = (70, 90, 140) if rect.collidepoint(mouse) else (50, 60, 90)
            pygame.draw.rect(screen, color, rect, border_radius=8)
            label = f"{i + 1}. {name} ({cfg['rounds']} rounds)"
            self._text(screen, label, self.font_small, WHITE, rect.center)
        self._text(screen, "Q / Esc to quit", self.font_small, LIGHT,
                   (cx, self.height - 25))

    def _render_play(self, screen):
        r = self.round
        cx, cy = self.width // 2, self.height // 2
        if r.state == Round.WAITING:
            screen.fill(GREY)
            self._text(screen, "Wait for green...", self.font_big, WHITE, (cx, cy))
        elif r.state == Round.GO:
            screen.fill(GREEN)
            self._text(screen, "CLICK!", self.font_big, WHITE, (cx, cy))
        elif r.state == Round.RESULT:
            screen.fill(GREEN)
            self._text(screen, f"{r.reaction_ms} ms", self.font_big, WHITE, (cx, cy))
        else:
            screen.fill(RED)
            self._text(screen, "Too soon!", self.font_big, WHITE, (cx, cy - 20))
            self._text(screen, "False start", self.font_mid, WHITE, (cx, cy + 40))

        info = self.font_small.render(
            f"{self.difficulty}  |  Round {self.round_number}/{self.total_rounds}",
            True, WHITE)
        screen.blit(info, (15, 12))

        avg = self._average()
        avg_text = f"Avg: {avg:.0f} ms" if avg is not None else "Avg: --"
        avg_surf = self.font_small.render(avg_text, True, WHITE)
        screen.blit(avg_surf, (self.width - avg_surf.get_width() - 15, 12))

        self._text(screen, "Click or press Space  |  Esc: menu",
                   self.font_small, WHITE, (cx, self.height - 20))

    def _render_results(self, screen):
        screen.fill(DARK)
        cx = self.width // 2
        self._text(screen, f"Results - {self.difficulty}", self.font_mid, WHITE, (cx, 30))
        y = 80
        for i, r in enumerate(self.results, start=1):
            text = f"Round {i}: {r} ms" if r is not None else f"Round {i}: False start"
            color = LIGHT if r is not None else (231, 120, 110)
            self._text(screen, text, self.font_small, color, (cx, y))
            y += 28
        avg = self._average()
        avg_text = (f"Average: {avg:.0f} ms" if avg is not None
                    else "Average: N/A (no valid rounds)")
        self._text(screen, avg_text, self.font_mid, GREEN, (cx, 305))
        self._text(screen, "Enter / Space: play again    Q / Esc: quit",
                   self.font_small, LIGHT, (cx, 360))