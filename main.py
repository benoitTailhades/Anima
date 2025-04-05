import sys
import math

import pygame
import random
import time
from scripts.entities import player_death, Enemy
from scripts.utils import load_image, load_images, Animation, display_bg
from scripts.tilemap import Tilemap
from scripts.physics import PhysicsPlayer
from scripts.particle import Particle
from scripts.user_interface import Menu, start_menu


class Game:
    def __init__(self):
        pygame.init()
        start_menu()
        pygame.display.set_caption("Anima")
        self.screen = pygame.display.set_mode((960, 576), pygame.RESIZABLE)
        self.display = pygame.Surface((480, 288))
        self.clock = pygame.time.Clock()
        self.fullscreen = False

        self.tile_size = 16

        self.assets = {
            'decor': load_images('tiles/decor', self.tile_size),
            'grass': load_images('tiles/grass', self.tile_size),
            'vine': load_images('tiles/vine', self.tile_size),
            'vine_transp': load_images('tiles/vine_transp', self.tile_size),
            'vine_transp_back': load_images('tiles/vine_transp_back', self.tile_size),
            'vine_decor': load_images('tiles/vine_decor'),
            'large_decor': load_images('tiles/large_decor'),
            'dark_vine': load_images('tiles/dark_vine'),
            'hanging_vine': load_images('tiles/hanging_vine'),
            'stone': load_images('tiles/stone', self.tile_size),
            'mossy_stone': load_images('tiles/mossy_stone', self.tile_size),
            'mossy_stone_decor': load_images('tiles/mossy_stone_decor', self.tile_size),
            'player': load_image('entities/player.png', (40, 40)),
            'enemy/idle': Animation(load_images('entities/enemy/idle'), img_dur=12),
            'enemy/run/left': Animation(load_images('entities/enemy/run/left'), img_dur=8),
            'enemy/run/right': Animation(load_images('entities/enemy/run/right'), img_dur=8),
            'enemy/attack': Animation(load_images('entities/enemy/attack'), img_dur=3, loop=False),
            'background': load_image('background_begin.png', self.display.get_size()),
            'background1': load_image('bg1.png'),
            'background2': load_image('bg2.png'),
            'brume': load_image('brume_begin.png'),
            'player/idle': Animation(load_images('entities/player/idle'), img_dur=12),
            'player/run/right': Animation(load_images('entities/player/run/right'), img_dur=3),
            'player/run/left': Animation(load_images('entities/player/run/left'), img_dur=3),
            'player/jump/right': Animation(load_images('entities/player/jump/right'), img_dur=3, loop=False),
            'player/jump/left': Animation(load_images('entities/player/jump/left'), img_dur=3, loop=False),
            'player/jump/top': Animation(load_images('entities/player/jump/top'), img_dur=3, loop=False),
            'player/falling/right': Animation(load_images('entities/player/falling/right'), img_dur=3, loop=True),
            'player/falling/left': Animation(load_images('entities/player/falling/left'), img_dur=3, loop=True),
            'player/falling/vertical': Animation(load_images('entities/player/falling/vertical'), img_dur=3, loop=True),
            'player/dash/right': Animation(load_images('entities/player/dash/right'), img_dur=3, loop=False),
            'player/dash/left': Animation(load_images('entities/player/dash/left'), img_dur=3, loop=False),
            'player/dash/top': Animation(load_images('entities/player/dash/top'), img_dur=3, loop=False),
            'player/wall_slide/right': Animation(load_images('entities/player/wall_slide/right'), img_dur=3,
                                                 loop=False),
            'player/wall_slide/left': Animation(load_images('entities/player/wall_slide/left'), img_dur=3, loop=False),
            'particle/leaf': Animation(load_images('particles/leaf'), loop=5)
        }

        self.dict_kb = {"key_right": 0, "key_left": 0, "key_up": 0, "key_down": 0, "key_jump": 0, "key_dash": 0,
                        "key_noclip": 0}

        self.tilemap = Tilemap(self, self.tile_size)
        self.tilemap.load('map.json')

        self.player = PhysicsPlayer(self, self.tilemap, (100, 0), (25, 35))
        self.player_hp = 100

        self.leaf_spawners = []
        for plant in self.tilemap.extract([('vine_decor', 3), ('vine_decor', 4), ('vine_decor', 5),
                                           ('mossy_stone_decor', 15), ('mossy_stone_decor', 16)],
                                          keep=True):
            self.leaf_spawners.append(pygame.Rect(4 + plant['pos'][0], 4 + plant['pos'][1], 23, 13))

        self.enemies = []
        for spawner in self.tilemap.extract([('spawners', 0), ('spawners', 1)]):
            if spawner['variant'] == 0:
                self.spawn_pos = spawner['pos']
                self.player.pos = spawner['pos'].copy()
            else:
                self.enemies.append(Enemy(self, spawner['pos'], (16, 16)))

        self.scroll = [0, 0]

        self.particles = []

        self.menu = Menu(self)
        self.keyboard_layout = "azerty"

    def deal_dmg(self,entity, target, att_speed):
        current_time = time.time()
        if target == "player" and current_time - entity.last_attack_time >= 1:
            entity.last_attack_time = time.time()
            self.player_hp -= att_speed
            # Create a transparent surface
            flash_surface = pygame.Surface((self.screen.get_width(), self.screen.get_height()), pygame.SRCALPHA)
            flash_surface.fill((255, 0, 0, 50))  # (R, G, B, Alpha)

            # Blit the transparent red overlay onto the screen
            self.screen.blit(flash_surface, (0, 0))
            pygame.display.update()
            pygame.time.delay(100)

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN | pygame.NOFRAME)
        else:
            self.screen = pygame.display.set_mode((960, 576), pygame.RESIZABLE)

    def get_key_map(self):
        if self.keyboard_layout.lower() == "azerty":
            return {
                pygame.K_z: "key_up",
                pygame.K_s: "key_down",
                pygame.K_q: "key_left",
                pygame.K_d: "key_right",
                pygame.K_g: "key_dash",
                pygame.K_h: "key_attack",
                pygame.K_SPACE: "key_jump",
                pygame.K_n: "key_noclip"
            }
        elif self.keyboard_layout.lower() == "qwerty":
            return {
                pygame.K_w: "key_up",
                pygame.K_s: "key_down",
                pygame.K_a: "key_left",
                pygame.K_d: "key_right",
                pygame.K_g: "key_dash",
                pygame.K_h: "key_attack",
                pygame.K_SPACE: "key_jump",
                pygame.K_n: "key_noclip"
            }

    def run(self):
        while True:
            self.display.blit(self.assets['background'], (0, 0))
            self.scroll[0] += (self.player.rect().centerx - self.display.get_width() / 2 - self.scroll[0]) / 20
            self.scroll[1] += (self.player.rect().centery - self.display.get_height() / 2 - self.scroll[1]) / 20
            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))

            for rect in self.leaf_spawners:
                if random.random() * 49999 < rect.width * rect.height:
                    pos = (rect.x + random.random() * rect.width, rect.y + random.random() * rect.height)
                    self.particles.append(
                        Particle(self, 'leaf', pos, velocity=[-0.1, 0.3], frame=random.randint(0, 20)))

            display_bg(self.display, self.assets['background1'], (-self.scroll[0] / 10, -20))
            display_bg(self.display, self.assets['background2'], (self.scroll[0] / 50, -20))

            self.tilemap.render(self.display, offset=render_scroll)

            for enemy in self.enemies.copy():
                enemy.update(self.tilemap, (0, 0))
                enemy.render(self.display, offset=render_scroll)

            self.player.physics_process(self.tilemap, self.dict_kb)
            self.player.render(self.display, offset=render_scroll)

            self.tilemap.render_over(self.display, offset=render_scroll)

            if (self.player.pos[1] > 500 and not (int(self.player.pos[0]) in range(736, 1152))) or self.player_hp <= 0:
                player_death(self, self.screen, self.spawn_pos)
                self.player_hp = 100

            for particle in self.particles.copy():
                kill = particle.update()
                particle.render(self.display, offset=render_scroll)
                if particle.type == 'leaf':
                    particle.pos[0] += math.sin(particle.animation.frame * 0.035) * 0.3
                if kill:
                    self.particles.remove(particle)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.menu.menu_display()
                    elif event.key == pygame.K_F11:
                        self.toggle_fullscreen()

                if event.type in (pygame.KEYDOWN, pygame.KEYUP):
                    state = 1 if event.type == pygame.KEYDOWN else 0
                    key_map = self.get_key_map()

                    if event.key in key_map:
                        self.dict_kb[key_map[event.key]] = state

            self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), (0, 0))
            pygame.display.update()
            self.clock.tick(60)

Game().run()