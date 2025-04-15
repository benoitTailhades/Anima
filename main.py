import sys
import math
import os

import pygame
import random
import time
from scripts.entities import player_death, Enemy
from scripts.utils import load_image, load_images, Animation, display_bg
from scripts.tilemap import Tilemap
from scripts.physics import PhysicsPlayer
from scripts.particle import Particle
from scripts.boss import FirstBoss, Vine
from scripts.activators import Lever
from scripts.user_interface import Menu, start_menu
from scripts.saving import Save


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
            'picko/idle': Animation(load_images('entities/enemies/picko/idle'), img_dur=12),
            'picko/run/left': Animation(load_images('entities/enemies/picko/run/left'), img_dur=8),
            'picko/run/right': Animation(load_images('entities/enemies/picko/run/right'), img_dur=8),
            'picko/attack': Animation(load_images('entities/enemies/picko/attack'), img_dur=3, loop=False),
            'picko/death': Animation(load_images('entities/enemies/picko/death'), img_dur=3, loop=False),
            'picko/hit': Animation(load_images('entities/enemies/picko/hit'), img_dur=5, loop=False),

            'boss/idle': Animation(load_images('entities/enemies/picko/idle', 32), img_dur=12),
            'boss/run/left': Animation(load_images('entities/enemies/picko/run/left', 32), img_dur=8),
            'boss/run/right': Animation(load_images('entities/enemies/picko/run/right', 32), img_dur=8),
            'boss/attack': Animation(load_images('entities/enemies/picko/attack', 32), img_dur=3, loop=False),
            'boss/death': Animation(load_images('entities/enemies/picko/death', 32), img_dur=3, loop=False),
            'boss/hit': Animation(load_images('entities/enemies/picko/hit', 32), img_dur=5, loop=False),

            'vine/warning': Animation(load_images('entities/elements/vine/warning', (16, 48)), img_dur=12),
            'vine/attack': Animation(load_images('entities/elements/vine/attack', (16, 48)), img_dur=1, loop=False),
            'vine/retreat': Animation(load_images('entities/elements/vine/retreat', (16, 48)), img_dur=3, loop=False),

            'background': load_image('background_begin.png', self.display.get_size()),
            'background0': load_image('bg0.png'),
            'background1': load_image('bg1.png'),
            'background2': load_image('bg2.png'),
            'fog': load_image('fog.png'),

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
            'player/wall_slide/right': Animation(load_images('entities/player/wall_slide/right'), img_dur=3,loop=False),
            'player/wall_slide/left': Animation(load_images('entities/player/wall_slide/left'), img_dur=3, loop=False),
            'player/attack/right': Animation(load_images('entities/player/attack/right'), img_dur=2, loop=False),
            'player/attack/left': Animation(load_images('entities/player/attack/left'), img_dur=2, loop=False),
            'lever': load_images('tiles/lever'),
            'particle/leaf': Animation(load_images('particles/leaf'), loop=5),
            'full_heart': load_image('full_heart.png', (16, 16)),
            'half_heart': load_image('half_heart.png', (16, 16)),
            'empty_heart': load_image('empty_heart.png', (16, 16 ))
        }

        self.sound_running = False
        try:
            # Make sure pygame is properly initialized before trying to play sounds
            if not pygame.mixer.get_init():
                print("Initializing pygame mixer in Game.__init__...")
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
                time.sleep(0.1)  # Small delay to ensure initialization completes

            # Verify the sound file path and try different filename variations if needed
            sound_path = "assets/sounds/v2-level-1-sound-background_W72B8woG.wav"
            if not os.path.exists(sound_path):
                print(f"Sound file not found at: {sound_path}")
                # Try alternative filename from your screenshot
                sound_path = "assets/sounds/v2-level-1-sound-background_W728Bw06.wav"
                if not os.path.exists(sound_path):
                    print(f"Alternative sound file not found either: {sound_path}")

            self.volume = 0.5  # Volume par défaut : 50%
            self.background_music = pygame.mixer.Sound(sound_path)
            self.background_music.set_volume(self.volume)
            self.background_music.play(loops=-1)
            self.sound_running = True
            if not self.sound_running:
                print("Failed to start background music")
        except Exception as e:
            print(f"Error initializing sound: {e}")

        self.dict_kb = {"key_right": 0, "key_left": 0, "key_up": 0, "key_down": 0, "key_jump": 0, "key_dash": 0,
                        "key_noclip": 0, "key_attack": 0}

        self.tilemap = Tilemap(self, self.tile_size)
        self.level = 0
        self.levers = []
        self.in_bossfight = False

        self.player = PhysicsPlayer(self, self.tilemap, (100, 0), (19, 35))
        self.player_hp = 100
        self.player_dmg = 200
        self.player_attack_time = 0.3
        self.player_attack_dist = 20
        self.player_last_attack_time = 0
        self.holding_attack = False
        self.attacking = False
        self.player_attacked = False
        self.screenshake = 0


        self.damage_flash_active = False
        self.damage_flash_end_time = 0
        self.damage_flash_duration = 100  # milliseconds

        self.last_visual_movement_time = 0
        self.moving_visual = False
        self.visual_pos = (0, 0)
        self.visual_movement_duration = 0
        self.visual_start_time = 0

        self.particles = []

        self.load_level(self.level)
        self.selected_language = "English"
        self.menu = Menu(self)
        self.keyboard_layout = "azerty"
        self.save_system = Save(self)

        if hasattr(self, 'menu'):
            self.menu.start_menu_newgame()
        else:
            self.menu = Menu(self)
            self.menu.start_menu_newgame()

    def set_volume(self, volume):
        self.volume = max(0, min(1, volume))
        if self.background_music:
            self.background_music.set_volume(self.volume)

    def deal_dmg(self, entity, target, att_dmg=5, att_time=1):
        current_time = time.time()
        if target == "player" and current_time - entity.last_attack_time >= att_time:
            entity.last_attack_time = time.time()
            self.player_hp -= att_dmg
            self.damage_flash_active = True
            entity.is_dealing_damage = True
            self.damage_flash_end_time = pygame.time.get_ticks() + self.damage_flash_duration

        elif target != "player" and current_time - self.player_last_attack_time >= self.player_attack_time:
            self.player_last_attack_time = time.time()
            target.hp -= self.player_dmg

    def deal_knockback(self, entity, target, strenght):
        stun_elapsed = time.time() - target.last_stun_time
        stun_duration = 0.5

        knockback_dir_x = 1 if entity.rect().centerx < target.rect().centerx else -1
        knockback_dir_y = 0
        knockback_force = max(0, strenght * (1.0 - stun_elapsed / stun_duration))
        return knockback_dir_x * knockback_force, knockback_dir_y * knockback_force

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN | pygame.NOFRAME)
        else:
            self.screen = pygame.display.set_mode((960, 576), pygame.RESIZABLE)

    def draw_health_bar(self, max_hearts=5):
        full_hearts = self.player_hp // 20
        half_heart = 1 if self.player_hp % 20 >= 10 else 0

        start_x = 20
        start_y = 20
        heart_spacing = 22

        for i in range(full_hearts):
            self.display.blit(self.assets['full_heart'], (start_x + (i * heart_spacing), start_y))

        # Dessiner le demi-cœur si nécessaire
        if half_heart:
            self.display.blit(self.assets['half_heart'], (start_x + (full_hearts * heart_spacing), start_y))

        empty_hearts = max_hearts - full_hearts - half_heart
        for i in range(empty_hearts):
            pos = start_x + ((full_hearts + half_heart + i) * heart_spacing)
            self.display.blit(self.assets['empty_heart'], (pos, start_y))

    def get_key_map(self):
        if self.keyboard_layout.lower() == "azerty":
            return {
                pygame.K_z: "key_up",
                pygame.K_s: "key_down",
                pygame.K_q: "key_left",
                pygame.K_d: "key_right",
                pygame.K_g: "key_dash",
                pygame.K_SPACE: "key_jump",
                pygame.K_n: "key_noclip",
            }
        elif self.keyboard_layout.lower() == "qwerty":
            return {
                pygame.K_w: "key_up",
                pygame.K_s: "key_down",
                pygame.K_a: "key_left",
                pygame.K_d: "key_right",
                pygame.K_g: "key_dash",
                pygame.K_SPACE: "key_jump",
                pygame.K_n: "key_noclip",
            }

    def update_settings_from_game(self):
        self.volume = self.volume
        self.keyboard_layout = self.keyboard_layout

        if hasattr(self, "selected_language") and self.selected_language in self.languages:
            self.selected_language = self.selected_language

    def attacking_update(self):
        self.attacking = ((self.dict_kb["key_attack"] == 1 and time.time() - self.player_last_attack_time >= 0.03)
                          or self.player.action in ("attack/left", "attack/right")) and not self.player.is_stunned
        if self.attacking and self.player.action == "attack/right" and self.player.get_direction("x") == -1:
            self.attacking = False
            self.dict_kb["key_attack"] = 0
        elif self.attacking and self.player.action == "attack/left" and self.player.get_direction("x") == 1:
            self.attacking = False
            self.dict_kb["key_attack"] = 0

        if self.attacking and self.player.animation.done:
            self.dict_kb["key_attack"] = 0
            self.player_last_attack_time = time.time()

    def screen_shake(self, strenght):
        self.screenshake = max(strenght, self.screenshake)

    def save_game(self, slot=1):
        if hasattr(self, 'save_system'):
            success = self.save_system.save_game(slot)
            return success
        return False

    def load_game(self, slot=1):
        if hasattr(self, 'save_system'):
            success = self.save_system.load_game(slot)
            return success
        return False

    def load_level(self, map_id):
        self.tilemap.load("data/maps/" + str(map_id) + ".json")

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
            elif spawner['variant'] == 1:
                self.enemies.append(Enemy(self, "picko", spawner['pos'] , (16, 16), 100,
                                          {"attack_distance" : 20,
                                           "attack_dmg": 5,
                                           "attack_time": 2}))

        self.bosses = []
        for spawner in self.tilemap.extract([('spawners', 2)]):  # Assuming spawner variant 3 is for bosses
            if spawner['variant'] == 2:
                self.bosses.append(FirstBoss(self, "boss", spawner['pos'], (32, 32), 500,
                                          {"attack_distance": 20,
                                           "attack_dmg": 5,
                                           "attack_time": 2}))

        self.transitions = self.tilemap.extract([("transitions", 0), ("transitions", 1)])

        self.scroll = [0, 0]
        self.transition = -30
        self.max_falling_depth = 500 if self.level == 0 else 5000

        self.levers = []
        for lever in self.tilemap.extract([('lever', 0), ('lever', 1)]):
            l = Lever(self, lever['pos'])
            l.state = lever["variant"]
            self.levers.append(l)

    def display_level_bg(self, map_id):
        if map_id == 0:
            display_bg(self.display, self.assets['background0'], (-self.scroll[0] / 10, -20))
            display_bg(self.display, self.assets['background1'], (-self.scroll[0] / 10, -20))
            display_bg(self.display, self.assets['background2'], (self.scroll[0] / 50, -20))

    def display_level_fg(self, map_id):
        if map_id == 0:
            display_bg(self.display, self.assets['fog'], (-self.scroll[0], -20))

    def check_transition(self):
        for transition in self.transitions:
            if (transition['pos'][0] + 16 > self.player.rect().centerx >= transition['pos'][0] and
                    transition['pos'][1] > self.player.rect().centery >= transition['pos'][1] - 16):
                if transition["variant"] == 0:
                    self.level -= 1
                    self.load_level(self.level)
                elif transition["variant"] == 1:
                    self.level += 1
                    self.load_level(self.level)

    def move_visual(self, duration, pos):
        self.moving_visual = True
        self.visual_pos = pos
        self.visual_movement_duration = duration
        self.visual_start_time = time.time()

    def update_camera(self):
        current_time = time.time()

        # Check if we're in a visual movement mode
        if self.moving_visual:
            elapsed_time = current_time - self.visual_start_time

            if elapsed_time < self.visual_movement_duration:
                # Smoothly move to target position while duration is active
                self.scroll[0] += (self.visual_pos[0] - self.display.get_width() / 2 - self.scroll[0]) / 20
                self.scroll[1] += (self.visual_pos[1] - self.display.get_height() / 2 - self.scroll[1]) / 20
            else:
                # Duration completed, return to following player
                self.moving_visual = False

        # Default camera behavior - follow player
        if not self.moving_visual:
            self.scroll[0] += (self.player.rect().centerx - self.display.get_width() / 2 - self.scroll[0]) / 20
            self.scroll[1] += (self.player.rect().centery - self.display.get_height() / 2 - self.scroll[1]) / 20

    def run(self):
        while True:
            self.display.blit(self.assets['background'], (0, 0))

            self.screenshake = max(0, self.screenshake - 1)

            self.update_camera()
            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))

            if self.transition < 0:
                self.transition += 1

            for rect in self.leaf_spawners:
                if random.random() * 49999 < rect.width * rect.height:
                    pos = (rect.x + random.random() * rect.width, rect.y + random.random() * rect.height)
                    self.particles.append(
                        Particle(self, 'leaf', pos, velocity=[-0.1, 0.3], frame=random.randint(0, 20)))

            self.check_transition()
            self.display_level_bg(0)
            self.player.can_walljump["allowed"] = not (self.level == 1)

            self.tilemap.render(self.display, offset=render_scroll)

            for lever in self.levers:
                lever.render(self.display, offset=render_scroll)

            for enemy in self.enemies.copy():
                enemy.update(self.tilemap, (0, 0))
                enemy.render(self.display, offset=render_scroll)
                if enemy.hp <= 0:
                    enemy.set_action("death")
                    if enemy.animation.done:
                        self.enemies.remove(enemy)

            self.attacking_update()

            self.player.physics_process(self.tilemap, self.dict_kb)
            self.player.render(self.display, offset=render_scroll)

            for boss in self.bosses.copy():
                boss.update(self.tilemap, (0, 0))
                boss.render(self.display, offset=render_scroll)
                # Remove dead bosses
                if boss.hp <= 0:
                    boss.set_action("death")
                    if boss.animation.done:
                        self.bosses.remove(boss)

            self.tilemap.render_over(self.display, offset=render_scroll)
            self.display_level_fg(0)

            if self.player.pos[1] > self.max_falling_depth or self.player_hp <= 0:
                player_death(self, self.screen, self.spawn_pos)
                for key in self.dict_kb.keys():
                    self.dict_kb[key] = 0
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
                        for key in self.dict_kb.keys():
                            self.dict_kb[key] = 0

                    if event.key == pygame.K_e:
                        for lever in self.levers:
                            if lever.can_interact(self.player.rect()):
                                if lever.toggle():
                                    self.screen_shake(10)
                                    self.move_visual(2, (928, 208))
                                    self.tilemap.extract([('dark_vine', 0), ('dark_vine', 1), ('dark_vine', 2)])

                    if event.key == pygame.K_F11:
                        self.toggle_fullscreen()
                    if event.key == pygame.K_f:
                        if not self.holding_attack:
                            self.dict_kb["key_attack"] = 1
                        if self.dict_kb["key_attack"] == 1:
                            self.holding_attack = True
                    if event.key == pygame.K_j:
                        self.tilemap.extract([('dark_vine', 0), ('dark_vine', 1), ('dark_vine', 2)])

                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_f:
                        self.dict_kb["key_attack"] = 0
                        self.holding_attack = False

                if event.type in (pygame.KEYDOWN, pygame.KEYUP):
                    state = 1 if event.type == pygame.KEYDOWN else 0
                    key_map = self.get_key_map()

                    if event.key in key_map:
                        self.dict_kb[key_map[event.key]] = state

            if self.transition:
                transition_surf = pygame.Surface(self.display.get_size())
                pygame.draw.circle(transition_surf, (255, 255, 255),(self.display.get_width() // 2, self.display.get_height() // 2), (30 - abs(self.transition)) * 8)
                transition_surf.set_colorkey((255, 255, 255))
                self.display.blit(transition_surf, (0, 0))

            screenshake_offset = (random.random() * self.screenshake - self.screenshake / 2,
                                  random.random() * self.screenshake - self.screenshake / 2)
            self.draw_health_bar()

            self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), screenshake_offset)

            if self.damage_flash_active:
                # Check if the flash should still be displayed
                if pygame.time.get_ticks() < self.damage_flash_end_time:
                    # Create a transparent surface
                    flash_surface = pygame.Surface((self.screen.get_width(), self.screen.get_height()), pygame.SRCALPHA)
                    flash_surface.fill((255, 0, 0, 50))  # (R, G, B, Alpha)
                    # Blit the transparent red overlay onto the screen
                    self.screen.blit(flash_surface, (0, 0))
                else:
                    # Flash duration has ended
                    self.damage_flash_active = False

            pygame.display.update()
            self.clock.tick(60)

Game().run()