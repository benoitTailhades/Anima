import sys

import pygame

from scripts.utils import load_image, load_images, Animation
from scripts.entities import PhysicsEntity
from scripts.tilemap import Tilemap
from scripts.Physics import PhysicsPlayer
from scripts.user_interface import Menu

class Game:
    def __init__(self):
        pygame.init()

        pygame.display.set_caption("Anima")
        self.screen = pygame.display.set_mode((1000, 600), pygame.RESIZABLE)
        self.display = pygame.Surface((500, 300),pygame.RESIZABLE)

        self.clock = pygame.time.Clock()

        self.tile_size = 16

        self.assets = {
            'decor': load_images('tiles/decor', self.tile_size),
            'grass': load_images('tiles/grass', self.tile_size),
            'vine': load_images('tiles/vine', self.tile_size),
            'vine_decor': load_images('tiles/vine_decor'),
            'large_decor': load_images('tiles/large_decor'),
            'stone': load_images('tiles/stone', self.tile_size),
            'player': load_image('entities/player.png', (40, 40)),
            'background' : load_image('background_begin.png', self.display.get_size()),
            'brume': load_image('brume_begin.png'),
            'player/idle': Animation(load_images('entities/player/idle'), img_dur=12),
            'player/run/right' : Animation(load_images('entities/player/run/right'), img_dur=3),
            'player/run/left': Animation(load_images('entities/player/run/left'), img_dur=3),
            'player/jump/right' : Animation(load_images('entities/player/jump/right'), img_dur=3, loop=False),
            'player/jump/left': Animation(load_images('entities/player/jump/left'), img_dur=3, loop=False),
            'player/falling/right': Animation(load_images('entities/player/falling/right'), img_dur=3, loop=False),
            'player/falling/left': Animation(load_images('entities/player/falling/left'), img_dur=3, loop=False)
        }

        self.dict_kb = {"key_right": 0, "key_left": 0, "key_up": 0, "key_down": 0, "key_jump": 0, "key_dash": 0}

        self.tilemap = Tilemap(self, self.tile_size)
        self.tilemap.load('map.json')

        self.scroll = [0, 0]

        self.player = PhysicsPlayer(self, self.tilemap, (100, -50), (25, 35))

    def run(self):
        while True:

            self.display.blit(self.assets['background'], (0, 0))

            self.scroll[0] += (self.player.rect().centerx - self.display.get_width() / 2 - self.scroll[0]) / 20
            self.scroll[1] += (self.player.rect().centery - self.display.get_height() / 2 - self.scroll[1]) / 20
            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))

            self.tilemap.render(self.display, offset=render_scroll)

            self.player.physics_process(self.tilemap, self.dict_kb)
            self.player.render(self.display, offset=render_scroll)

            self.display.blit(self.assets['brume'], (-137-(self.assets['brume'].get_width()/2)-render_scroll[0], -135-(self.assets['brume'].get_height()/4)-render_scroll[1]))

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    menu()
                if event.type in (pygame.KEYDOWN, pygame.KEYUP):
                    state = 1 if event.type == pygame.KEYDOWN else 0
                    key_map = {
                        pygame.K_z: "key_up",
                        pygame.K_s: "key_down",
                        pygame.K_q: "key_left",
                        pygame.K_d: "key_right",
                        pygame.K_g: "key_dash",
                        pygame.K_h: "key_attack",
                        pygame.K_SPACE: "key_jump",
                        pygame.K_n: "key_noclip"
                    }
                    if event.key in key_map:
                        self.dict_kb[key_map[event.key]] = state
                elif event.type == pygame.VIDEORESIZE:
                    self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)

            self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), (0, 0))
            pygame.display.update()
            self.clock.tick(60)

Game().run()