import sys

import pygame

from script.utils import load_image
from script.entities import PhysicsEntity

class Game:
    def __init__(self):
        pygame.init()

        pygame.display.set_caption("Anima")
        self.screen = pygame.display.set_mode((640, 480))
        self.display = pygame.Surface((1280, 960))

        self.clock = pygame.time.Clock()

        self.movement = [False,False]
        print()
        self.assets = {
            'player': load_image('debugasset.png')
        }

        self.player = PhysicsEntity(self, 'player', (50, 50), (8, 15))

    def run(self):
        while True:
            self.display.fill((14, 219, 248))

            self.player.update((self.movement[1]-self.movement[0], 0))
            self.player.render(self.display)
            for event in pygame.event.get():
                pass

            self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), (0, 0))
            pygame.display.update()
            self.clock.tick(60)

Game().run()
