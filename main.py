import sys

import pygame

from script.utils import load_image, load_images
from script.entities import PhysicsEntity
from script.tilemap import Tilemap
from script.physics import Physics

class Game:
    def __init__(self):
        pygame.init()

        pygame.display.set_caption("Anima")
        self.screen = pygame.display.set_mode((640, 480))
        self.display = pygame.Surface((320, 240))

        self.clock = pygame.time.Clock()

        self.assets = {
            'decor': load_images('tiles/decor'),
            'grass': load_images('tiles/grass'),
            'large_decor': load_images('tiles/large_decor'),
            'stone': load_images('tiles/stone'),
            'player': load_image('entities/player.png')

        }

        self.phys = Physics()
        self.dict_kb = {"key_right": 0, "key_left": 0, "key_up": 0, "key_down": 0, "key_jump": 0, "key_dash": 0}
        self.player = PhysicsEntity(self, 'player', (50, 50), (8, 15))

        self.tilemap = Tilemap(self, tile_size=16)

    def run(self):
        while True:
            self.display.fill((14, 219, 248))

            self.tilemap.render(self.display)

            print(self.tilemap.physics_rects_around(self.player.pos))
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_z:
                        self.dict_kb["key_up"] = 1
                    if event.key == pygame.K_s:
                        self.dict_kb["key_down"] = 1
                    if event.key == pygame.K_q:
                        self.dict_kb["key_left"] = 1
                    if event.key == pygame.K_d:
                        self.dict_kb["key_right"] = 1
                    if event.key == pygame.K_q:
                        self.dict_kb["key_left"] = 1
                    if event.key == pygame.K_g:
                        self.dict_kb["key_dash"] = 1
                    if event.key == pygame.K_h:
                        self.dict_kb["key_attack"] = 1
                    if event.key == pygame.K_SPACE:
                        self.dict_kb["key_jump"] = 1
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_z:
                        self.dict_kb["key_up"] = 0
                    if event.key == pygame.K_s:
                        self.dict_kb["key_down"] = 0
                    if event.key == pygame.K_q:
                        self.dict_kb["key_left"] = 0
                    if event.key == pygame.K_d:
                        self.dict_kb["key_right"] = 0
                    if event.key == pygame.K_q:
                        self.dict_kb["key_left"] = 0
                    if event.key == pygame.K_g:
                        self.dict_kb["key_dash"] = 0
                    if event.key == pygame.K_h:
                        self.dict_kb["key_attack"] = 0
                    if event.key == pygame.K_SPACE:
                        self.dict_kb["key_jump"] = 0

            self.coords = self.phys.physics_process(1,self.dict_kb,[])
            self.player.update_coords(self.tilemap, self.coords)
            self.player.render(self.display)
            self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), (0, 0))
            pygame.display.update()
            self.clock.tick(60)

Game().run()
