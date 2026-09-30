import pygame

pygame.mixer.pre_init(44100, -16, 1, 512)
pygame.init()

from game.game_engine import GameEngine

# Screen dimensions
WIDTH, HEIGHT = 600, 400
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Reaction Time Tester - Pygame Version")

# Clock
clock = pygame.time.Clock()
FPS = 60

engine = GameEngine(WIDTH, HEIGHT)

def main():
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            engine.handle_event(event)

        if engine.should_quit:
            running = False

        engine.update()
        engine.render(SCREEN)
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()