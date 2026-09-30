import random
import pygame

class Round:
    """One reaction round: WAITING (grey) -> GO (green) -> RESULT,
    or WAITING -> FALSE_START if the player reacts too early."""

    WAITING = "waiting"
    GO = "go"
    RESULT = "result"
    FALSE_START = "false_start"

    def __init__(self, min_wait_ms, max_wait_ms):
        self.state = Round.WAITING
        self.wait_ms = random.randint(min_wait_ms, max_wait_ms)
        self.start_tick = pygame.time.get_ticks()
        self.go_tick = None        # moment the screen turned green
        self.end_tick = None       # moment the round finished
        self.reaction_ms = None

    def update(self):
        """Advance the round. Returns True on the frame it flips to GO."""
        if self.state == Round.WAITING:
            now = pygame.time.get_ticks()
            if now - self.start_tick >= self.wait_ms:
                self.state = Round.GO
                self.go_tick = now
                return True
        return False

    def react(self):
        """Player clicked/pressed Space. Returns the new state, or None
        if the input should be ignored (round already finished)."""
        now = pygame.time.get_ticks()
        if self.state == Round.WAITING:
            self.state = Round.FALSE_START
            self.end_tick = now
            return Round.FALSE_START
        if self.state == Round.GO:
            self.reaction_ms = now - self.go_tick   # measured from "go"
            self.state = Round.RESULT
            self.end_tick = now
            return Round.RESULT
        return None

    @property
    def finished(self):
        return self.state in (Round.RESULT, Round.FALSE_START)

    def ms_since_end(self):
        if self.end_tick is None:
            return 0
        return pygame.time.get_ticks() - self.end_tick