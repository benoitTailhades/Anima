import sys
import math
import os
import json

import pygame
import random
import time
from scripts.entities import player_death, Enemy, Throwable, deal_dmg, deal_knockback
from scripts.utils import *
from scripts.tilemap import Tilemap
from scripts.physics import PhysicsPlayer
from scripts.particle import Particle
from scripts.boss import FirstBoss
from scripts.activators import Lever, Teleporter
from scripts.user_interface import Menu, start_menu
from scripts.saving import Save
from scripts.doors import Door
from scripts.visual_effects import *
from scripts.spark import Spark


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

        self.e_info = {
            "picko":{"left/right": ["run"],
                                "size": (16, 16),
                                "img_dur": {"idle": 12, "run": 8, "attack": 3, "death": 3, "hit": 5},
                                "loop": {"idle": True, "run": True, "attack": False, "death": False, "hit": False}},
            "vine":{"left/right":[],
                               "size": (16, 48),
                               "img_dur":{"warning": 12, "attack": 1, "retreat": 3},
                               "loop": {"warning": True, "attack": False, "retreat": False}},
            "wrath":{"left/right": ["run"],
                                "size": (48, 48),
                                "img_dur": {"idle": 12, "run": 8, "jump": 5, "death": 3, "hit": 5, "charge": 5},
                                "loop": {"idle": True, "run": True, "death": False, "hit": False, "jump":False, "charge": False}},
            "blue_rock": {"left/right": [],
                      "size": (16, 16),
                      "img_dur": {"intact":1, "breaking":2},
                      "loop": {"intact":False, "breaking":False}}
                       }

        self.d_info = {
            "vines_door_h":{"size":(64, 16),"img_dur":5},
            "vines_door_v": {"size": (16, 64),"img_dur": 5},
            "breakable_stalactite": {"size": (16, 48), "img_dur": 1},
            "blue_vine_door_v": {"size": (16, 64), "img_dur": 5},
            "blue_vine_door_h": {"size": (64, 16), "img_dur": 5}
                       }

        self.b_info = {"green_cave/0":{"size":self.display.get_size()}}

        self.environments = {"green_cave":(0, 1, 2),
                             "blue_cave": (3,)}

        self.spawners = {}

        self.scroll_limits = {0: {"x":(-272, 1680),"y":(-1000, 100)},
                              1: {"x":(-48, 16), "y":(-1000, 400)},
                              2: {"x":(-48, 280), "y":(-192, -80)},
                              3: {"x":(16, 40000), "y":(0, 20000000)}}

        self.light_infos = {0:{"darkness_level":180, "light_radius": 200},
                            1:{"darkness_level":180, "light_radius":300},
                            2:{"darkness_level":180, "light_radius": 200},
                            3:{"darkness_level":180, "light_radius": 200}}

        self.assets = {

            'green_cave_lever': load_images('levers/green_cave'),
            'blue_cave_lever': load_images('levers/green_cave'),
            'particle/leaf': Animation(load_images('particles/leaf'), loop=5),
            'particle/crystal': Animation(load_images('particles/crystal'), loop=1),
            'particle/crystal_fragment': Animation(load_images('particles/crystal_fragment'), loop=1),
            'full_heart': load_image('full_heart.png', (16, 16)),
            'half_heart': load_image('half_heart.png', (16, 16)),
            'empty_heart': load_image('empty_heart.png', (16, 16)),
            'teleporter': load_images('teleporters/blue_cave')
        }

        self.assets.update(load_doors(self.d_info))
        self.assets.update(load_tiles())
        self.assets.update(load_entities(self.e_info))
        self.assets.update(load_player())
        self.assets.update(load_backgrounds(self.b_info))

        self.doors_id_pairs = []
        for env in self.environments:
            self.doors_id_pairs += [(door, 0) for door in load_doors('editor', env)]

        self.sound_running = False

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
                time.sleep(0.1)

            sound_path = "assets/sounds/maintheme.wav"

            self.volume = 0.5
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
        self.levels = {i:{"charged": False} for i in range(len(os.listdir("data/maps")))}
        self.charged_levels = []

        self.levers = []
        self.activators_actions = load_activators_actions()
        self.boss_levels = [1]
        self.in_boss_level = False

        self.spawner_pos = {}

        self.player = PhysicsPlayer(self, self.tilemap, (100, 0), (19, 35))
        self.player_hp = 100
        self.player_dmg = 50
        self.player_attack_time = 0.03
        self.player_attack_dist = 20
        self.player_last_attack_time = 0
        self.holding_attack = False
        self.attacking = False
        self.player_attacked = False

        self.teleporting = False
        self.tp_id = None
        self.last_teleport_time = 0

        self.screenshake = 0

        self.cutscene = False
        self.floating_texts = {}
        self.game_texts = load_game_texts()
        self.tutorial_active = False
        self.tutorial_step = 0
        self.tutorial_next_time = 0
        self.tutorial_messages = []

        self.doors_rects = []

        self.damage_flash_active = False
        self.damage_flash_end_time = 0
        self.damage_flash_duration = 100
        self.floating_text_shown = False

        self.darkness_level = 150
        self.light_radius = 100
        self.light_soft_edge = 350
        self.light_emitting_tiles = []
        self.light_emitting_objects = []

        self.light_properties = {
            "player": {"radius": 100, "intensity": 250, "edge_softness": 255, "color": (255, 255, 255),
                       "flicker": False},
            "torch": {"radius": 80, "intensity": 220, "edge_softness": 30, "color": (255, 180, 100), "flicker": True},
            "crystal": {"radius": 120, "intensity": 200, "edge_softness": 50, "color": (100, 180, 255),
                        "flicker": False},
            "glowing_mushroom": {"radius": 20, "intensity": 150, "edge_softness": 500, "color": (160, 230, 180),
                                 "flicker": False},
            "lava": {"radius": 100, "intensity": 210, "edge_softness": 40, "color": (255, 120, 50), "flicker": True}
        }

        self.light_mask = pygame.Surface((self.light_radius * 2, self.light_radius * 2), pygame.SRCALPHA)
        create_light_mask(self.light_radius)

        self.player_light = self.light_properties["player"]

        self.last_visual_movement_time = 0
        self.moving_visual = False
        self.visual_pos = (0, 0)
        self.visual_movement_duration = 0
        self.visual_start_time = 0

        self.player_grabbing = False
        self.interacting = False

        self.particles = []

        self.selected_language = "English"
        self.menu = Menu(self)
        self.keyboard_layout = "azerty"
        self.save_system = Save(self)

        if not self.menu.start_menu_newgame():
            self.load_level(self.level)

    def set_volume(self, volume):
        self.volume = max(0, min(1, volume))
        if self.background_music:
            self.background_music.set_volume(self.volume)

    def get_environment(self, level):
        for environment in self.environments:
            if level in self.environments[environment]:
                return environment

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN | pygame.NOFRAME)
        else:
            self.screen = pygame.display.set_mode((960, 576), pygame.RESIZABLE)

    def draw_health_bar(self, max_hearts=5):
        display_hp = max(10, self.player_hp) if self.player_hp > 0 else 0

        full_hearts = display_hp // 20
        half_heart = 1 if display_hp % 20 >= 10 else 0

        start_x = 20
        start_y = 20
        heart_spacing = 22

        for i in range(full_hearts):
            self.display.blit(self.assets['full_heart'], (start_x + (i * heart_spacing), start_y))

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

    def update_light(self):
        level_info = self.light_infos[self.level]
        self.darkness_level = level_info["darkness_level"]

        self.player_light["radius"] = level_info["light_radius"]
        self.light_mask = pygame.Surface((self.light_radius * 2, self.light_radius * 2), pygame.SRCALPHA)
        create_light_mask(self.light_radius)

    def update_settings_from_game(self):
        self.volume = self.volume
        self.keyboard_layout = self.keyboard_layout

        if hasattr(self, "selected_language") and self.selected_language in self.languages:
            self.selected_language = self.selected_language

    def attacking_update(self):
        self.attacking = ((self.dict_kb["key_attack"] == 1 and time.time() - self.player_last_attack_time >= 0.03)
                          or self.player.action in ("attack/left", "attack/right")) and not self.player.is_stunned and not self.player_grabbing
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
        self.light_emitting_tiles = []
        self.light_emitting_objects = []

        self.teleporters = []
        for tp in self.tilemap.extract([('teleporter',0)], keep=True):
            self.teleporters.append(Teleporter(self, tp['pos'], (16, 16), tp['id']))


        self.throwable = []
        for o in self.tilemap.extract([('throwable',0)]):
            self.throwable.append(Throwable(self, "blue_rock", o['pos'], (16, 16)))


        self.leaf_spawners = []
        for plant in self.tilemap.extract([('vine_decor', 3), ('vine_decor', 4), ('vine_decor', 5),
                                           ('mossy_stone_decor', 15), ('mossy_stone_decor', 16)],
                                          keep=True):
            self.leaf_spawners.append(pygame.Rect(4 + plant['pos'][0], 4 + plant['pos'][1], 23, 13))

        self.crystal_spawners = []
        for mushroom in self.tilemap.extract([("blue_decor", 0),], keep=True):
            if not self.levels[map_id]["charged"]:
                register_light_emitting_tile(self,
                    (mushroom['pos'][0] + 8, mushroom['pos'][1] + 8),
                    "glowing_mushroom"
                )
            self.crystal_spawners.append(pygame.Rect(4 + mushroom['pos'][0], 4 + mushroom['pos'][1], 23, 13))

        if not self.levels[map_id]["charged"]:
            self.enemies = []
            self.bosses = []
            for spawner in self.tilemap.extract([('spawners', 0), ('spawners', 1), ('spawners', 2)]):
                if spawner['variant'] == 0:
                    self.spawners[map_id] = spawner["pos"].copy()
                    self.spawner_pos[map_id] = spawner["pos"]
                    self.player.pos = spawner["pos"].copy()
                elif spawner['variant'] == 1:
                    self.enemies.append(Enemy(self, "picko", spawner['pos'], (16, 16), 100,
                                              {"attack_distance": 20,
                                               "attack_dmg": 10,
                                               "attack_time": 1.5}))
                elif spawner['variant'] == 2:
                    self.bosses.append(FirstBoss(self, "wrath", spawner['pos'], (48, 48), 500,
                                                 {"attack_distance": 25,
                                                  "attack_dmg": 50,
                                                  "attack_time": 0.1}))

            self.levers = []
            for lever in self.tilemap.extract([('lever', 0),('lever', 1)]):
                l = Lever(self, lever['pos'], i=lever["id"])
                l.state = lever["variant"]
                self.levers.append(l)

            self.doors = []
            for door in self.tilemap.extract(self.doors_id_pairs):
                if door['type'] == 'breakable_stalactite':
                    self.doors.append(Door(self.d_info[door["type"]]["size"], door["pos"], door["type"], None, False, 0.01, self))
                else:
                    self.doors.append(Door(self.d_info[door["type"]]["size"], door["pos"], door["type"], door["id"], False, 1, self))

            if not self.in_boss_level:
                self.levels[map_id]["charged"] = True
                self.charged_levels.append(map_id)

            self.transitions = self.tilemap.extract([("transition", 0)])
            self.scroll = [self.player.pos[0], self.player.pos[1]]

        else:
            for spawner in self.tilemap.extract([('spawners', 0), ('spawners', 1), ('spawners', 2)]):
                if spawner['variant'] == 0:
                    self.spawner_pos[map_id] = spawner["pos"]
            self.player.pos = self.spawners[map_id].copy()
            self.tilemap.extract([('lever', 0),('lever', 1)])
            self.tilemap.extract(self.doors_id_pairs)
            self.transitions = self.tilemap.extract([("transition", 0)])
            self.enemies = self.levels[map_id]["enemies"].copy()
            self.bosses = self.levels[map_id]["bosses"].copy()
            self.levers = self.levels[map_id]["levers"].copy()
            self.doors = self.levels[map_id]["doors"].copy()

        self.cutscene = False
        self.particles = []
        self.sparks = []
        self.transition = -30
        self.max_falling_depth = 50000000 if self.level in (1,3) else 500
        self.update_light()
        if map_id == 0 and not self.levels[map_id]["charged"]:
            self.start_tutorial_sequence()

    def display_level_bg(self, map_id):
        if map_id in (0, 1, 2):
            self.display.blit(self.assets['green_cave/0'], (0, 0))
            display_bg(self.display, self.assets['green_cave/1'], (-self.scroll[0] / 10, -20))
            display_bg(self.display, self.assets['green_cave/2'], (-self.scroll[0] / 10, -20))
            display_bg(self.display, self.assets['green_cave/3'], (self.scroll[0] / 50, -20))
        if map_id == 3:
            self.display.blit(self.assets['blue_cave/0'], (0, 0))
            display_bg(self.display, self.assets['blue_cave/1'], (-self.scroll[0] / 10, 0))
            display_bg(self.display, self.assets['blue_cave/2'], (-self.scroll[0] / 30, 0))
            display_bg(self.display, self.assets['blue_cave/3'], (self.scroll[0] / 30, 0))
            display_bg(self.display, self.assets['blue_cave/4'], (self.scroll[0] / 50, 0))

    def draw_boss_health_bar(self, boss):
        if not self.bosses or boss.hp <= 0:
            return

        bar_width = 200
        bar_height = 6
        border_thickness = 1
        border_radius = 3

        bar_x = (self.display.get_width() - bar_width) // 2
        bar_y = 25

        health_percentage = max(0, boss.hp / boss.max_hp)
        current_bar_width = int(bar_width * health_percentage)

        border_color = (30, 30, 30)
        bg_color = (60, 60, 60)
        health_color = (133, 6, 6)

        shadow_offset = 2
        pygame.draw.rect(
            self.display,
            (20, 20, 20),
            (bar_x - border_thickness + shadow_offset,
             bar_y - border_thickness + shadow_offset,
             bar_width + (border_thickness * 2),
             bar_height + (border_thickness * 2)),
            0,
            border_radius + border_thickness
        )

        pygame.draw.rect(self.display,border_color,(bar_x - border_thickness,bar_y - border_thickness,bar_width + (border_thickness * 2),bar_height + (border_thickness * 2)),0, border_radius + border_thickness)

        pygame.draw.rect(self.display,bg_color,(bar_x, bar_y, bar_width, bar_height),0,border_radius)

        if current_bar_width > 0:
            right_radius = border_radius if current_bar_width >= border_radius * 2 else 0
            pygame.draw.rect(self.display,health_color,(bar_x, bar_y, current_bar_width, bar_height),0,border_radius, right_radius, border_radius, right_radius)

        if current_bar_width > 5:
            highlight_height = max(2, bar_height // 3)
            highlight_width = current_bar_width - 4
            pygame.draw.rect(self.display,(220, 60, 60),  (bar_x + 2, bar_y + 1, highlight_width, highlight_height),0,border_radius // 2)


        try:
            font = pygame.font.SysFont("Arial", 15)
        except:
            font = pygame.font.Font(None, 26)

        boss_name = boss.name if hasattr(boss, 'name') else "Wrath"

        text_surface = font.render(boss_name, True, (255, 255, 255))
        text_rect = text_surface.get_rect(centerx=bar_x + bar_width // 2, bottom=bar_y - 4)

        shadow_surface = font.render(boss_name, True, (0, 0, 0))
        shadow_rect = shadow_surface.get_rect(centerx=text_rect.centerx + 1, centery=text_rect.centery + 1)

        self.display.blit(shadow_surface, shadow_rect)
        self.display.blit(text_surface, text_rect)

    def display_level_fg(self, map_id):
        if map_id in (0,1,2):
            generate_fog(self.display, color=(24, 38, 31), opacity=130)
        if map_id == 3:
            generate_fog(self.display, color=(28, 50, 73), opacity=130)

    def check_transition(self):
        for transition in self.transitions:
            if (transition['pos'][0] + 16 > self.player.rect().centerx >= transition['pos'][0] and
                    self.player.rect().bottom >= transition['pos'][1] >= self.player.rect().top):
                if self.player.get_direction("x") != 0:
                    self.spawners[self.level] = [self.player.pos.copy()[0] - 16*(self.player.get_direction("x")), self.player.pos.copy()[1]]
                self.level = transition["destination"]
                self.in_boss_level = self.level in self.boss_levels
                self.load_level(self.level)

    def display_text_above_player(self, text_key, duration=2.0, color=(255, 255, 255), offset_y=-30):

        level_str = str(self.level)
        if level_str in self.game_texts and text_key in self.game_texts[level_str]:
            text = self.game_texts[level_str][text_key]

            self.floating_texts[text_key] = {
                'text': text,
                'color': color,
                'end_time': time.time() + duration,
                'offset_y': offset_y,
                'opacity': 255
            }
        else:
            print(f"Texte non trouvé: niveau {level_str}, clé {text_key}")

    def update_floating_texts(self, render_scroll):
        current_time = time.time()
        for text_key in self.floating_texts.copy():
            text_data = self.floating_texts[text_key]
            remaining_time = text_data['end_time'] - current_time + 1
            if remaining_time < 0.5:
                self.floating_texts[text_key]['opacity'] = int(255 * (remaining_time / 0.5))

            player_x = self.player.rect().centerx - render_scroll[0]
            player_y = self.player.rect().top - render_scroll[1] + text_data['offset_y']

            try:
                font = pygame.font.SysFont("Arial", 14)
            except:
                font = pygame.font.Font(None, 18)

            text_surface = font.render(text_data['text'], True, text_data['color'])
            text_surface.set_alpha(text_data['opacity'])

            shadow_surface = font.render(text_data['text'], True, (0, 0, 0))
            shadow_surface.set_alpha(text_data['opacity'] * 0.7)

            text_rect = text_surface.get_rect(center=(player_x, player_y))
            shadow_rect = shadow_surface.get_rect(center=(player_x + 1, player_y + 1))

            self.display.blit(shadow_surface, shadow_rect)
            self.display.blit(text_surface, text_rect)

            if remaining_time <= 0:
                self.floating_text_shown = False
                del self.floating_texts[text_key]
            else:
                self.floating_text_shown = True

    def start_tutorial_sequence(self):
        self.tutorial_active = True
        self.tutorial_step = 0
        self.tutorial_next_time = time.time()

        if str(self.level) == "0":
            self.tutorial_messages = [
                {"key": "tuto_movement", "duration": 4.0, "delay": 1.0, "color": (255, 255, 255)},
                {"key": "tuto_space", "duration": 4.0, "delay": 1.0, "color": (220, 255, 255)},
                {"key": "tuto_FG", "duration": 4.0, "delay": 1.0, "color": (255, 255, 255)},
                {"key": "Interaction","duration":4.0,"delay":1.0,"color":(255,255,255)}
            ]

    def update_tutorial_sequence(self):
        if not self.tutorial_active or self.tutorial_step >= len(self.tutorial_messages):
            self.tutorial_active = False
            return

        current_time = time.time()

        if current_time >= self.tutorial_next_time:
            message = self.tutorial_messages[self.tutorial_step]
            self.display_text_above_player(
                message["key"],
                message["duration"],
                message["color"],
                -30
            )

            self.tutorial_next_time = current_time + message["duration"] + message["delay"]
            self.tutorial_step += 1

    def move_visual(self, duration, pos):
        self.moving_visual = True
        self.visual_pos = pos
        self.visual_movement_duration = duration
        self.visual_start_time = time.time()

    def update_camera(self):
        current_time = time.time()

        if self.moving_visual:
            elapsed_time = current_time - self.visual_start_time

            if elapsed_time < self.visual_movement_duration:
                self.scroll[0] += (self.visual_pos[0] - self.display.get_width() / 2 - self.scroll[0]) / 20
                self.scroll[1] += (self.visual_pos[1] - self.display.get_height() / 2 - self.scroll[1]) / 20
            else:
                self.moving_visual = False

        else:
            target_x = self.player.rect().centerx - self.display.get_width() / 2
            target_y = self.player.rect().centery - self.display.get_height() / 2

            if self.level in self.scroll_limits:
                level_limits = self.scroll_limits[self.level]

                if level_limits["x"]:
                    min_x, max_x = level_limits["x"]
                    target_x = max(min_x, min(target_x, max_x))

                if level_limits["y"]:
                    min_y, max_y = level_limits["y"]
                    target_y = max(min_y, min(target_y, max_y))

            self.scroll[0] += (target_x - self.scroll[0]) / 20
            self.scroll[1] += (target_y - self.scroll[1]) / 20

    def update_spawn_point(self):
        if self.level in (0, 1, 2):
            self.spawn_point = {"pos": self.spawner_pos[0], "level": 0}
        elif self.level in (3, 4, 5):
            self.spawn_point = {"pos": self.spawner_pos[3], "level": 3}

    def update_activators_actions(self, level):
        for lever in self.levers:
            if lever.can_interact(self.player.rect()):
                lever_id = str(lever.id)
                if lever_id in self.activators_actions[str(level)]["levers"]:
                    action = self.activators_actions[str(level)]["levers"][lever_id]

                    if action["type"] == "visual_and_door":
                        for door in self.doors:
                            if door.id == action["door_id"]:
                                lever.toggle()
                                self.move_visual(action["visual_duration"], door.pos)
                                lever.activated = False
                                door.open()

                        self.screen_shake(10)
        for tp in self.teleporters:
            if tp.can_interact(self.player.rect()):
                if str(tp.id) in self.activators_actions[str(level)]["teleporters"]:
                    self.last_teleport_time = time.time()
                    self.teleporting = True
                    self.tp_id = tp.id

    def update_teleporter(self, t_id):
        if t_id is not None:
            action = self.activators_actions[str(self.level)]["teleporters"][str(t_id)]
            if time.time() - self.last_teleport_time < action["time"] - 0.2:
                pos = (self.player.rect().x + random.random() * self.player.rect().width,
                       self.player.rect().y + 5 + random.random() * self.player.rect().height)
                self.particles.append(
                    Particle(self, 'crystal_fragment', pos, velocity=[-0.1, 4], frame=0))
                pass
            else:
                self.last_teleport_time = time.time()
                self.player.pos = action["dest"].copy()
                self.teleporting = False
                self.tp_id = None

    def update_throwable_objects_action(self):
        for o in self.throwable:
            if not o.grabbed and not self.player_grabbing:
                if o.can_interact(self.player.rect()):
                    o.grab(self.player)
                    return
            elif o.grabbed:
                o.launch([self.player.last_direction, -1], 3.2)
                return

    def run(self):
        while True:
            self.screenshake = max(0, self.screenshake - 1)

            self.check_transition()

            self.update_camera()
            render_scroll = (round(self.scroll[0]), round(self.scroll[1]))

            self.update_tutorial_sequence()
            self.update_floating_texts(render_scroll)


            if self.transition < 0:
                self.transition += 1

            self.light_emitting_objects = [obj for obj in self.light_emitting_objects
                                           if obj in self.enemies or obj in self.throwable
                                           or obj in self.bosses]

            if self.teleporting:
                self.update_teleporter(self.tp_id)

            self.update_spawn_point()

            self.player.disablePlayerInput = self.cutscene or self.moving_visual or self.teleporting

            for rect in self.leaf_spawners:
                if random.random() * 49999 < rect.width * rect.height:
                    pos = (rect.x + random.random() * rect.width, rect.y + random.random() * rect.height)
                    self.particles.append(
                        Particle(self, 'leaf', pos, velocity=[-0.1, 0.3], frame=random.randint(0, 20)))

            self.display_level_bg(self.level)
            self.player.can_walljump["allowed"] = self.level not in self.boss_levels or not self.bosses

            ds = []
            for door in self.doors:
                door.update()
                door.render(self.display, offset=render_scroll)
                if not door.opened:
                    ds.append(door.rect())
            self.doors_rects = ds

            self.tilemap.render(self.display, offset=render_scroll)

            for lever in self.levers:
                lever.render(self.display, offset=render_scroll)

                if lever.can_interact(self.player.rect()):
                    text_key = "Lever_interaction"
                    if not self.floating_text_shown:
                        self.display_text_above_player(text_key, duration=1)
                    else:
                        self.floating_texts[text_key]['end_time'] = time.time()

            for enemy in self.enemies.copy():
                enemy.update(self.tilemap, (0, 0))
                enemy.render(self.display, offset=render_scroll)
                if enemy.hp <= 0 or enemy.pos[1] > self.max_falling_depth:
                    enemy.set_action("death")
                    if enemy.animation.done:
                        self.enemies.remove(enemy)
                for o in self.throwable:
                    if (o.rect().colliderect(enemy.rect().inflate(-enemy.rect().width/2, -enemy.rect().height/3)) and
                            int(o.velocity[1]) != 0 and not o.grabbed):
                        if o.action != "breaking":
                            deal_dmg(self, "player", enemy, 10, 0)
                            enemy.stunned = True
                            enemy.last_stun_time = time.time()
                        o.set_action("breaking")
                    if o.action == "breaking" and o.animation.done:
                        self.throwable.remove(o)

            s = []
            for n in range(4):
                s += [("spikes", n), ("bloody_spikes", n), ("big_spikes", n), ("big_bloody_spikes", n)]
            for spike in self.tilemap.extract(s, keep=True):
                r = pygame.Rect(spike["pos"][0], spike["pos"][1],
                                self.assets[spike["type"]][spike["variant"]].get_width(), self.assets[spike["type"]][spike["variant"]].get_height())
                if self.player.rect().colliderect(r.inflate(-r.width/2, -r.height/3)):
                    self.player_hp = 0
                for o in self.throwable:
                    if o.rect().colliderect(r.inflate(-r.width/2, -r.height/3)):
                        o.set_action("breaking")
                        if o.animation.done:
                            self.throwable.remove(o)

            self.attacking_update()

            self.player.physics_process(self.tilemap, self.dict_kb)
            self.player.render(self.display, offset=render_scroll)

            for o in self.throwable:
                o.update(self.tilemap, (0, 0))
                o.render(self.display, offset=render_scroll)
                if o.can_interact(self.player.rect()) and not self.floating_text_shown:
                    self.display_text_above_player("Interaction",duration=4)
                    
            for tp in self.teleporters:
                if tp.can_interact(self.player.rect())and not self.floating_text_shown:
                    self.display_text_above_player("Interaction",duration=4)
                    
            for boss in self.bosses.copy():
                boss.update(self.tilemap, (0, 0))
                boss.render(self.display, offset=render_scroll)
                if boss.hp <= 0:
                    boss.set_action("death")
                    for enemy in self.enemies:
                        enemy.hp = 0
                    if boss.animation.done:
                        self.bosses.remove(boss)
                        self.levels[self.level]["charged"] = True

            self.tilemap.render_over(self.display, offset=render_scroll)

            for rect in self.crystal_spawners:
                if random.random() * 49999 < rect.width * rect.height:
                    pos = (rect.x + random.random() * rect.width, rect.y + random.random() * rect.height)
                    self.particles.append(
                        Particle(self, 'crystal', pos, velocity=[-0.1, 0.3], frame=random.randint(0, 20)))

            self.display_level_fg(self.level)

            if self.player.pos[1] > self.max_falling_depth or self.player_hp <= 0:
                player_death(self, self.screen, self.spawn_point["pos"], self.spawn_point["level"])
                for key in self.dict_kb.keys():
                    self.dict_kb[key] = 0
                self.player_hp = 100

            for spark in self.sparks.copy():
                kill = spark.update()
                spark.render(self.display, offset=render_scroll)
                if kill:
                    self.sparks.remove(spark)

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
                        self.update_throwable_objects_action()
                        if not self.player_grabbing:
                            self.update_activators_actions(self.level)

                    if event.key == pygame.K_F11:
                        self.toggle_fullscreen()
                    if event.key == pygame.K_f and not self.holding_attack:
                        self.dict_kb["key_attack"] = 1
                        self.holding_attack = True
                    if event.key == pygame.K_b:
                        self.doors[0].open()

                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_f:
                        self.dict_kb["key_attack"] = 0
                        self.holding_attack = False

                if event.type in (pygame.KEYDOWN, pygame.KEYUP):
                    state = 1 if event.type == pygame.KEYDOWN else 0
                    key_map = self.get_key_map()

                    if event.key in key_map:
                        self.dict_kb[key_map[event.key]] = state

            self.levels[self.level]["enemies"] = self.enemies.copy()
            self.levels[self.level]["bosses"] = self.bosses.copy()
            self.levels[self.level]["levers"] = self.levers.copy()
            self.levels[self.level]["doors"] = self.doors.copy()

            if self.transition:
                transition_surf = pygame.Surface(self.display.get_size())
                pygame.draw.circle(transition_surf, (255, 255, 255),(self.display.get_width() // 2, self.display.get_height() // 2), (30 - abs(self.transition)) * 8)
                transition_surf.set_colorkey((255, 255, 255))
                self.display.blit(transition_surf, (0, 0))

            apply_lighting(self, render_scroll)
            screenshake_offset = (random.random() * self.screenshake - self.screenshake / 2,random.random() * self.screenshake - self.screenshake / 2)
            self.update_floating_texts(render_scroll)

            if self.cutscene:
                draw_cutscene_border(self.display)
            else:
                self.draw_health_bar()
                if self.bosses:
                    self.draw_boss_health_bar(self.bosses[0])

            self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), screenshake_offset)

            if self.damage_flash_active:
                if pygame.time.get_ticks() < self.damage_flash_end_time:
                    self.screen_shake(16)
                    screen_width = self.screen.get_width()
                    screen_height = self.screen.get_height()

                    border_surface = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)

                    elapsed = pygame.time.get_ticks() - (self.damage_flash_end_time - self.damage_flash_duration)
                    progress = elapsed / self.damage_flash_duration

                    max_border_width = 220
                    border_width = int(max_border_width * (1 - progress))
                    alpha_base = int(240 * (1 - progress))

                    for i in range(border_width):
                        fade_factor = 1 - (i / border_width)
                        color_alpha = int(alpha_base * fade_factor)
                        color = (0, 0, 0, color_alpha)

                        pygame.draw.line(border_surface, color, (0, i), (screen_width, i), 1)
                        pygame.draw.line(border_surface, color, (screen_width - i - 1, 0),
                                         (screen_width - i - 1, screen_height), 1)
                        pygame.draw.line(border_surface, color, (0, screen_height - i - 1),
                                         (screen_width, screen_height - i - 1), 1)
                        pygame.draw.line(border_surface, color, (i, 0), (i, screen_height), 1)

                    corner_radius = min(0, border_width)
                    if corner_radius > 0:
                        for i in range(corner_radius):
                            fade_factor = 1 - (i / corner_radius)
                            color_alpha = int(
                                alpha_base * fade_factor * 0.7)
                            color = (0, 0, 0, color_alpha)

                            pygame.draw.arc(border_surface, color, (0, 0, corner_radius * 2, corner_radius * 2),
                                            math.pi / 2, math.pi, 1)
                            pygame.draw.arc(border_surface, color, (screen_width - corner_radius * 2, 0,
                                                                    corner_radius * 2, corner_radius * 2), 0,
                                            math.pi / 2, 1)
                            pygame.draw.arc(border_surface, color, (screen_width - corner_radius * 2,
                                                                    screen_height - corner_radius * 2,
                                                                    corner_radius * 2, corner_radius * 2),
                                            -math.pi / 2, 0, 1)
                            pygame.draw.arc(border_surface, color, (0, screen_height - corner_radius * 2,
                                                                    corner_radius * 2, corner_radius * 2), math.pi,
                                            3 * math.pi / 2, 1)

                    self.screen.blit(border_surface, (0, 0))
                else:
                    self.damage_flash_active = False

            pygame.display.update()
            self.clock.tick(60)

Game().run()