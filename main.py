import sys

import pygame

from scripts.utils import load_image, load_images
from scripts.entities import PhysicsEntity
from scripts.tilemap import Tilemap
from scripts.Physics import PhysicsPlayer
from scripts.user_interface import *

class Game:
    def __init__(self):
        pygame.init()

        pygame.display.set_caption("Anima")
        self.screen = pygame.display.set_mode((1000, 600), pygame.RESIZABLE)
        self.display = pygame.Surface((500, 300),pygame.RESIZABLE)

        self.clock = pygame.time.Clock()

        self.assets = {
            'decor': load_images('tiles/decor'),
            'grass': load_images('tiles/grass'),
            'large_decor': load_images('tiles/large_decor'),
            'stone': load_images('tiles/stone'),
            'player': load_image('entities/player.png')
        }

        self.dict_kb = {"key_right": 0, "key_left": 0, "key_up": 0, "key_down": 0, "key_jump": 0, "key_dash": 0}

        self.tilemap = Tilemap(self, tile_size=16)

        self.scroll = [0, 0]

        self.player = PhysicsPlayer(self, self.tilemap, (50, 50), (8, 15))

    def run(self):
        while True:
            self.display.fill((14, 219, 248))

            self.tilemap.render(self.display)

            self.player.physics_process(1,self.tilemap, self.dict_kb)
            self.player.render(self.display, offset= self.scroll)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type ==pygame.KEYDOWN  and event.key == pygame.K_ESCAPE:
                    menu()

                if event.type in (pygame.KEYDOWN, pygame.KEYUP):
                    state = 1 if event.type == pygame.KEYDOWN else 0
                    key_map = {
                        pygame.K_ESCAPE: "key_menu",
                        pygame.K_z: "key_up",
                        pygame.K_s: "key_down",
                        pygame.K_q: "key_left",
                        pygame.K_d: "key_right",
                        pygame.K_g: "key_dash",
                        pygame.K_h: "key_attack",
                        pygame.K_SPACE: "key_jump",
                    }
                    if event.key in key_map:
                        self.dict_kb[key_map[event.key]] = state
                elif event.type == pygame.VIDEORESIZE:
                    self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)

            self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), (0, 0))
            pygame.display.update()
            self.clock.tick(60)

Game().run()
