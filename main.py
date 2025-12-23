import sys
import math
import os
import json
import pygame
import random
import time

# --- Game Script Imports ---
from scripts.entities import *
from scripts.utils import *
from scripts.tilemap import Tilemap
from scripts.physics import PhysicsPlayer
from scripts.particle import Particle
from scripts.activators import *
from scripts.user_interface import Menu, start_menu
from scripts.saving import Save
from scripts.doors import Door
from scripts.display import *
from scripts.text import load_game_texts, display_bottom_text, update_bottom_text
from scripts.spark import Spark
from scripts.sound import set_game_volume


class Game:
    def __init__(self):
        """
        Initialize the main game object, Pygame, display, and load assets.
        """
        pygame.init()
        start_menu()  # Start a separate screen with anima logo

        pygame.display.set_caption("Anima")
        self.screen = pygame.display.set_mode((960, 576), pygame.RESIZABLE)
        self.display = pygame.Surface((480, 288))  # Render surface (pixel art scale)
        self.clock = pygame.time.Clock()

        # --- Icon Setup ---
        try:
            icon_img = pygame.image.load("assets/images/logo.png").convert_alpha()
            icon_img = pygame.transform.smoothscale(icon_img, (32, 32))
            pygame.display.set_icon(icon_img)
        except FileNotFoundError:
            pass  # Handle missing icon gracefully

        self.fullscreen = False
        self.tile_size = 16

        # --- Entity Definitions ---
        # Removed "wrath" and "ego" (bosses) to save memory
        self.e_info = {
            "picko": {"left/right": ["run"], "size": (16, 16),
                      "img_dur": {"idle": 12, "run": 8, "attack": 3, "death": 3, "hit": 5},
                      "loop": {"idle": True, "run": True, "attack": False, "death": False, "hit": False}},
            "glorbo": {"left/right": [], "size": (16, 16),
                       "img_dur": {"idle": 12, "run": 8, "attack": 3, "death": 3, "hit": 5},
                       "loop": {"idle": True, "run": True, "attack": False, "death": False, "hit": False}},
            "vine": {"left/right": [], "size": (16, 48),
                     "img_dur": {"warning": 12, "attack": 1, "retreat": 3},
                     "loop": {"warning": True, "attack": False, "retreat": False}},
            "blue_rock": {"left/right": [], "size": (16, 16),
                          "img_dur": {"intact": 1, "breaking": 2},
                          "loop": {"intact": False, "breaking": False}},
        }

        self.d_info = {
            "vines_door_h": {"size": (64, 16), "img_dur": 5},
            "vines_door_v": {"size": (16, 64), "img_dur": 5},
            "breakable_stalactite": {"size": (16, 48), "img_dur": 1},
            "blue_vine_door_v": {"size": (16, 64), "img_dur": 5},
            "blue_vine_door_h": {"size": (64, 16), "img_dur": 5}
        }

        self.b_info = {"green_cave/0": {"size": self.display.get_size()}}

        # Environment mappings for lighting or specific aesthetics
        self.environments = {"green_cave": (0, 1, 2), "blue_cave": (3, 4, 5)}

        self.spawners = {}

        # Camera/Scroll limits per level
        self.scroll_limits = {
            0: {"x": (-272, 1680), "y": (-1000, 100)},
            1: {"x": (-48, 16), "y": (-1000, 400)},
            2: {"x": (-48, 280), "y": (-192, -80)},
            3: {"x": (16, 190400), "y": (0, 20000000)},
            4: {"x": (-64, -16), "y": (-288, -256)}
        }

        # --- Asset Loading ---
        self.assets = {
            'particle/leaf': Animation(load_images('particles/leaf'), loop=5),
            'particle/crystal': Animation(load_images('particles/crystal'), loop=1000),
            'particle/crystal_fragment': Animation(load_images('particles/crystal_fragment'), loop=1),
            'full_heart': load_image('full_heart.png', (16, 16)),
            'half_heart': load_image('half_heart.png', (16, 16)),
            'empty_heart': load_image('empty_heart.png', (16, 16)),
            'glorbo_projectile': load_image('projectiles/glorbo_projectile.png', (16, 16)),
            'missile': load_image('projectiles/missile.png', (16, 16)),
        }

        self.assets.update(load_activators())
        self.assets.update(load_doors(self.d_info))
        self.assets.update(load_tiles())
        self.assets.update(load_entities(self.e_info))
        self.assets.update(load_player())
        self.assets.update(load_backgrounds(self.b_info))

        # --- Map Object Caching ---
        # Pre-calculate ID pairs for map loading to avoid re-looping constantly
        self.doors_id_pairs = []
        self.levers_id_pairs = []
        self.buttons_id_pairs = []
        self.tp_id_pairs = []

        for env in self.environments:
            self.doors_id_pairs += [(door, 0) for door in load_doors('editor', env)]
            self.levers_id_pairs += [(lever, 0) for lever in load_activators(env) if "lever" in lever]
            self.buttons_id_pairs += [(button, 0) for button in load_activators(env) if "button" in button]
            self.tp_id_pairs += [(tp, 0) for tp in load_activators(env) if "teleporter" in tp]

        # --- Audio System ---
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
        except Exception as e:
            print(f"Error initializing sound: {e}")

        # --- Input & State ---
        self.dict_kb = {"key_right": 0, "key_left": 0, "key_up": 0, "key_down": 0,
                        "key_jump": 0, "key_dash": 0, "key_noclip": 0, "key_attack": 0}

        self.tilemap = Tilemap(self, self.tile_size)
        self.level = 0
        self.levels = {i: {"charged": False} for i in range(len(os.listdir("data/maps")))}

        self.activators = []
        self.projectiles = []
        self.activators_actions = load_activators_actions()

        # Spawner logic
        self.spawner_pos = {}

        # Player stats
        self.player = PhysicsPlayer(self, self.tilemap, (100, 0), (16, 16))
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
        self.game_texts = load_game_texts()
        self.bottom_text = None

        self.doors_rects = []

        # VFX
        self.damage_flash_active = False
        self.damage_flash_end_time = 0
        self.damage_flash_duration = 100

        # Lighting System
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
            "glowing_mushroom": {"radius": 80, "intensity": 80, "edge_softness": 500, "color": (160, 230, 180),
                                 "flicker": False},
            "lava": {"radius": 100, "intensity": 210, "edge_softness": 40, "color": (255, 120, 50), "flicker": True}
        }

        self.light_infos = {0: {"darkness_level": 180, "light_radius": 200},

                            1: {"darkness_level": 180, "light_radius": 300},

                            2: {"darkness_level": 180, "light_radius": 200},

                            3: {"darkness_level": 180, "light_radius": 200},

                            4: {"darkness_level": 180, "light_radius": 200}}

        self.light_mask = pygame.Surface((self.light_radius * 2, self.light_radius * 2), pygame.SRCALPHA)
        create_light_mask(self.light_radius)
        self.player_light = self.light_properties["player"]

        # Interactions
        self.last_visual_movement_time = 0
        self.moving_visual = False
        self.visual_pos = (0, 0)
        self.visual_movement_duration = 0
        self.visual_start_time = 0
        self.player_grabbing = False
        self.interacting = False
        self.spike_knockback_on = True

        self.particles = []

        self.charged_levels = []

        # Menu & System
        self.selected_language = "English"
        self.menu = Menu(self)
        self.keyboard_layout = "azerty"
        self.save_system = Save(self)

        if not self.menu.start_menu_newgame():
            self.load_level(self.level)

    def get_environment(self, level):
        """Return environment key for the given level ID."""
        for environment in self.environments:
            if level in self.environments[environment]:
                return environment
        return "green_cave"  # Default fallback

    def get_key_map(self):
        """Return input mapping based on selected layout."""
        if self.keyboard_layout.lower() == "azerty":
            return {pygame.K_z: "key_up", pygame.K_s: "key_down", pygame.K_q: "key_left",
                    pygame.K_d: "key_right", pygame.K_g: "key_dash", pygame.K_SPACE: "key_jump",
                    pygame.K_n: "key_noclip"}
        elif self.keyboard_layout.lower() == "qwerty":
            return {pygame.K_w: "key_up", pygame.K_s: "key_down", pygame.K_a: "key_left",
                    pygame.K_d: "key_right", pygame.K_g: "key_dash", pygame.K_SPACE: "key_jump",
                    pygame.K_n: "key_noclip"}

    def update_settings_from_game(self):
        """Placeholder for sync settings logic."""
        pass

    def load_level(self, map_id):
        """
        Loads tiles, entities, and state for a specific level.
        Handles persistence (if level was already visited/charged).
        """
        self.tilemap.load("data/maps/" + str(map_id) + ".json")
        self.display = pygame.Surface((480, 288))
        self.light_emitting_tiles = []
        self.light_emitting_objects = []

        # --- Sound Check ---
        # Ensure main theme is playing (simplified from boss logic)
        if self.sound_running and hasattr(self, 'background_music'):
            # If we were playing something else or it stopped, restart main theme
            # Note: You might want to add a check here to not restart if it's already playing
            pass

            # --- Static Level Elements (Spikes, Decor) ---
        self.spikes = []
        spike_types = []
        for n in range(4):
            spike_types += [("spikes", n), ("bloody_spikes", n), ("big_spikes", n), ("big_bloody_spikes", n)]

        for spike in self.tilemap.extract(spike_types, keep=True):
            self.spikes.append(DamageBlock(self, spike["pos"], self.assets[spike["type"]][spike["variant"]]))

        self.throwable = []
        for o in self.tilemap.extract([('throwable', 0)]):
            self.throwable.append(Throwable(self, "blue_rock", o['pos'], (16, 16)))

        self.leaf_spawners = []
        for plant in self.tilemap.extract([('vine_decor', 3), ('vine_decor', 4), ('vine_decor', 5),
                                           ('mossy_stone_decor', 15), ('mossy_stone_decor', 16)], keep=True):
            self.leaf_spawners.append(pygame.Rect(4 + plant['pos'][0], 4 + plant['pos'][1], 23, 13))

        self.crystal_spawners = []
        for mushroom in self.tilemap.extract([("blue_decor", 14), ("blue_decor", 15)], keep=True):
            register_light_emitting_tile(self, (mushroom['pos'][0] + 8, mushroom['pos'][1] + 8), "glowing_mushroom")
            self.crystal_spawners.append(pygame.Rect(4 + mushroom['pos'][0], 4 + mushroom['pos'][1], 23, 13))

        # --- Dynamic Elements (Enemies, Doors) ---

        # If level is fresh (not charged), load from tilemap
        if not self.levels[map_id]["charged"]:
            self.enemies = []

            # Extract spawners
            for spawner in self.tilemap.extract([('spawners', 0), ('spawners', 1), ('spawners', 3)]):
                if spawner['variant'] == 0:  # Player Spawn
                    self.spawners[str(map_id)] = spawner["pos"].copy()
                    self.spawner_pos[str(map_id)] = spawner["pos"]
                    self.player.pos = spawner["pos"].copy()
                elif spawner['variant'] == 1:  # Standard Enemy
                    self.enemies.append(Enemy(self, "picko", spawner['pos'], (16, 16), 100,
                                              {"attack_distance": 20, "attack_dmg": 10, "attack_time": 1.5}))
                elif spawner['variant'] == 3:  # Ranged Enemy
                    self.enemies.append(DistanceEnemy(self, "glorbo", spawner['pos'], (16, 16), 100,
                                                      {"attack_distance": 100, "attack_dmg": 10, "attack_time": 1.5}))

            self.activators = []
            for activator in self.tilemap.extract(self.levers_id_pairs + self.buttons_id_pairs + self.tp_id_pairs):
                a = Activator(self, activator['pos'], activator['type'], i=activator["id"])
                a.state = activator["variant"]
                self.activators.append(a)

            self.doors = []
            for door in self.tilemap.extract(self.doors_id_pairs):
                if door['type'] == 'breakable_stalactite':
                    self.doors.append(
                        Door(self.d_info[door["type"]]["size"], door["pos"], door["type"], None, False, 0.01, self))
                else:
                    self.doors.append(
                        Door(self.d_info[door["type"]]["size"], door["pos"], door["type"], door["id"], False, 1, self))

            # Mark level as initialized so we remember killed enemies if we return
            self.levels[map_id]["charged"] = True

            if map_id not in self.charged_levels:
                self.charged_levels.append(map_id)

            self.transitions = self.tilemap.extract([("transition", 0)])
            self.scroll = [self.player.pos[0], self.player.pos[1]]

            # Save state
            self.levels[self.level]["enemies"] = self.enemies.copy()
            self.levels[self.level]["activators"] = self.activators.copy()
            self.levels[self.level]["doors"] = self.doors.copy()

        # If level is already visited, load from memory
        else:
            spawners = self.tilemap.extract([('spawners', 0), ('spawners', 1), ('spawners', 2), ('spawners', 3), ('spawners', 4)])
            for spawner in spawners:
                if spawner['variant'] == 0:
                    self.spawner_pos[str(map_id)] = spawner["pos"]

            if spawners:
                self.player.pos = self.spawners[str(map_id)].copy()

            # Clear these from tilemap as they are in memory
            self.tilemap.extract(self.levers_id_pairs + self.buttons_id_pairs)
            self.tilemap.extract(self.doors_id_pairs)
            self.transitions = self.tilemap.extract([("transition", 0)])

            # Load stored state
            self.enemies = self.levels[map_id]["enemies"].copy()
            self.activators = self.levels[map_id]["activators"].copy()
            self.doors = self.levels[map_id]["doors"].copy()

        self.interactable = self.throwable.copy() + self.activators.copy()
        self.cutscene = False
        self.particles = []
        self.sparks = []
        self.transition = -30
        self.max_falling_depth = 50000000000000000 if self.level in (1, 3) else 500
        update_light(self)

    def check_transition(self):
        """Checks if player hit a level transition point."""
        for transition in self.transitions:
            if (transition['pos'][0] + 16 > self.player.rect().centerx >= transition['pos'][0] and
                    self.player.rect().bottom >= transition['pos'][1] >= self.player.rect().top):
                self.level = transition["destination"]
                self.load_level(self.level)

                self.player.pos = [transition["dest_pos"][0] * 16, transition["dest_pos"][1] * 16]
                self.scroll[0] = self.player.pos[0]
                self.scroll[1] = self.player.pos[1]

                if self.level in self.scroll_limits:
                    limits = self.scroll_limits[self.level]
                    if "x" in limits:
                        self.scroll[0] = max(limits["x"][0], min(self.scroll[0], limits["x"][1]))
                    if "y" in limits:
                        self.scroll[1] = max(limits["y"][0], min(self.scroll[1], limits["y"][1]))

    def update_spawn_point(self):
        """Updates safe spawn location based on current level."""
        if self.level in (0, 1, 2):
            self.spawn_point = {"pos": self.spawner_pos['0'], "level": 0}
        elif self.level in (3, 4, 5):
            self.spawn_point = {"pos": self.spawner_pos['3'], "level": 3}

    def run(self):
        """Main Game Loop."""
        while True:
            # --- General Updates ---
            self.screenshake = max(0, self.screenshake - 1)
            self.check_transition()
            update_camera(self)

            # Convert float scroll to int for rendering
            render_scroll = (round(self.scroll[0]), round(self.scroll[1]))

            if self.transition < 0:
                self.transition += 1

            # Update lighting sources
            self.light_emitting_objects = [obj for obj in self.light_emitting_objects
                                           if obj in self.enemies or obj in self.throwable]

            if self.teleporting:
                update_teleporter(self, self.tp_id)

            self.update_spawn_point()

            # Disable input during specific events
            self.player.disablePlayerInput = self.cutscene or self.moving_visual or self.teleporting

            # Walljump logic (Optimized: Removed boss check)
            self.player.can_walljump["allowed"] = True

            # --- Background Rendering ---
            display_level_bg(self, self.level)

            # --- Particle Spawning (Environment) ---
            for rect in self.leaf_spawners:
                if random.random() * 49999 < rect.width * rect.height:
                    pos = (rect.x + random.random() * rect.width, rect.y + random.random() * rect.height)
                    self.particles.append(
                        Particle(self, 'leaf', pos, velocity=[-0.1, 0.3], frame=random.randint(0, 20)))

            # --- Projectile Logic ---
            for projectile in self.projectiles[:]:  # Iterate copy to allow removal
                # Homing Logic
                if 'homing' in projectile and projectile['homing']:
                    player_pos = [self.player.rect().centerx, self.player.rect().centery]
                    missile_pos = projectile['pos']

                    # Math optimization: Calculate vector
                    dx, dy = player_pos[0] - missile_pos[0], player_pos[1] - missile_pos[1]
                    magnitude = math.sqrt(dx ** 2 + dy ** 2)

                    if magnitude > 0:
                        turning_factor = 0.1
                        speed = projectile['speed']

                        # Blend current direction with target direction
                        cur_dx, cur_dy = projectile['direction']
                        tgt_dx, tgt_dy = (dx / magnitude) * speed, (dy / magnitude) * speed

                        new_dx = cur_dx + (tgt_dx - cur_dx) * turning_factor
                        new_dy = cur_dy + (tgt_dy - cur_dy) * turning_factor

                        # Renormalize
                        new_mag = math.sqrt(new_dx ** 2 + new_dy ** 2)
                        if new_mag > 0:
                            projectile['direction'] = [new_dx / new_mag * speed, new_dy / new_mag * speed]

                # Movement
                projectile['pos'][0] += projectile['direction'][0]
                projectile['pos'][1] += projectile['direction'][1]
                projectile['timer'] += 1

                # Rendering
                img = self.assets[projectile['type']].convert_alpha()
                if 'homing' in projectile and projectile['homing']:
                    angle = math.degrees(math.atan2(projectile['direction'][1], projectile['direction'][0]))
                    img = pygame.transform.rotate(img, -angle)

                screen_pos = (projectile['pos'][0] - img.get_width() / 2 - render_scroll[0],
                              projectile['pos'][1] - img.get_height() / 2 - render_scroll[1])
                self.display.blit(img, screen_pos)

                # Collision
                if self.tilemap.solid_check(projectile['pos']) or projectile['timer'] > 360:
                    self.projectiles.remove(projectile)
                    if projectile.get('homing'): screen_shake(self, 20)
                elif self.player.rect().collidepoint(projectile['pos']):
                    damage = projectile.get('damage', 10)
                    self.player_hp -= damage
                    self.damage_flash_active = True
                    self.damage_flash_end_time = pygame.time.get_ticks() + self.damage_flash_duration
                    self.projectiles.remove(projectile)
                    if projectile.get('homing'): screen_shake(self, 10)

            # --- Tilemap Rendering ---
            self.tilemap.render(self.display, offset=render_scroll)

            # --- Entity Rendering & Updates ---
            for activator in self.activators:
                activator.render(self.display, offset=render_scroll)

            for enemy in self.enemies.copy():
                enemy.update(self.tilemap, (0, 0))
                enemy.render(self.display, offset=render_scroll)

                # Despawn logic
                if enemy.hp <= 0 or enemy.pos[1] > self.max_falling_depth:
                    enemy.set_action("death")
                    if enemy.animation.done:
                        self.enemies.remove(enemy)

                # Throwable collision with enemies
                for o in self.throwable:
                    if (o.rect().colliderect(
                            enemy.rect().inflate(-enemy.rect().width / 2, -enemy.rect().height / 3)) and
                            int(o.velocity[1]) != 0 and not o.grabbed):
                        if o.action != "breaking":
                            deal_dmg(self, "player", enemy, 10, 0)
                            enemy.stunned = True
                            enemy.last_stun_time = time.time()
                        o.set_action("breaking")
                    if o.action == "breaking" and o.animation.done:
                        if o in self.throwable: self.throwable.remove(o)

            # --- Spike Collision ---
            for spike_hitbox in self.spikes:
                if time.time() - spike_hitbox.last_attack_time >= 0.01:
                    if self.player.rect().colliderect(spike_hitbox.rect()) and not self.player.noclip:
                        deal_dmg(self, spike_hitbox, "player", 10, 0.5)
                        self.spike_knockback_on = False
                        self.player.knockback_dir[
                            0] = 1 if spike_hitbox.rect().centerx < self.player.rect().centerx else -1
                        self.player.velocity = list(deal_knockback(spike_hitbox, self.player, 3, knockback="custom"))
                        self.player.knockback_strenght = 3
                        self.player.is_stunned = True
                        self.player.stunned_by = spike_hitbox
                        self.player.last_stun_time = time.time()
                        if not self.damage_flash_active:
                            self.damage_flash_active = True
                            self.damage_flash_end_time = pygame.time.get_ticks() + self.damage_flash_duration

                for o in self.throwable:
                    if o.rect().colliderect(spike_hitbox.rect()):
                        o.set_action("breaking")
                        if o.animation.done:
                            self.throwable.remove(o)

            # --- Player & Physics ---
            attacking_update(self)
            self.player.physics_process(self.tilemap, self.dict_kb)
            self.player.render(self.display, offset=render_scroll)

            for o in self.throwable:
                o.update(self.tilemap, (0, 0))
                o.render(self.display, offset=render_scroll)

            # --- Interaction Check ---
            interaction_found = False
            for inter in self.interactable:
                if inter.can_interact(self.player.rect()):
                    display_bottom_text(self, "Interaction", duration=0.1)
                    interaction_found = True
                    break

            # Render Foreground Tiles
            self.tilemap.render_over(self.display, offset=render_scroll)

            # --- Particle Spawning (Crystal) ---
            for rect in self.crystal_spawners:
                if random.random() * 49999 < rect.width * rect.height:
                    pos = (rect.x + random.random() * rect.width, rect.y + random.random() * rect.height)
                    self.particles.append(
                        Particle(self, 'crystal', pos, velocity=[-0.1, 0.3], frame=random.randint(0, 20)))

            display_level_fg(self, self.level)
            apply_lighting(self, render_scroll)

            # --- Door Logic ---
            ds = []
            for door in self.doors:
                door.update()
                door.render(self.display, offset=render_scroll)
                if not door.opened:
                    ds.append(door.rect())
            self.doors_rects = ds

            # --- Death Logic ---
            if self.player.pos[1] > self.max_falling_depth or self.player_hp <= 0:
                player_death(self, self.screen, self.spawn_point["pos"], self.spawn_point["level"])
                for key in self.dict_kb.keys():
                    self.dict_kb[key] = 0
                self.player_hp = 100

            # --- VFX Updates ---
            for spark in self.sparks[:]:
                kill = spark.update()
                spark.render(self.display, offset=render_scroll)
                if kill: self.sparks.remove(spark)

            for particle in self.particles[:]:
                kill = particle.update()
                particle.render(self.display, offset=render_scroll)
                if particle.type == 'leaf':
                    particle.pos[0] += math.sin(particle.animation.frame * 0.035) * 0.3
                if kill: self.particles.remove(particle)

            # --- Event Handling ---
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
                        update_throwable_objects_action(self)
                        if not self.player_grabbing:
                            update_activators_actions(self, self.level)

                    if event.key == pygame.K_F11:
                        toggle_fullscreen(self)
                    if event.key == pygame.K_f and not self.holding_attack:
                        self.dict_kb["key_attack"] = 1
                        self.holding_attack = True
                    if event.key == pygame.K_b:
                        if self.doors: self.doors[0].open()  # Safe check

                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_f:
                        self.dict_kb["key_attack"] = 0
                        self.holding_attack = False

                if event.type in (pygame.KEYDOWN, pygame.KEYUP):
                    state = 1 if event.type == pygame.KEYDOWN else 0
                    key_map = self.get_key_map()
                    if event.key in key_map:
                        self.dict_kb[key_map[event.key]] = state

            # --- State Persistence Update ---
            self.levels[self.level]["enemies"] = self.enemies.copy()
            self.levels[self.level]["activators"] = self.activators.copy()
            self.levels[self.level]["doors"] = self.doors.copy()

            # --- UI & Screen Shake ---
            if self.transition:
                transition_surf = pygame.Surface(self.display.get_size())
                pygame.draw.circle(transition_surf, (255, 255, 255),
                                   (self.display.get_width() // 2, self.display.get_height() // 2),
                                   (30 - abs(self.transition)) * 8)
                transition_surf.set_colorkey((255, 255, 255))
                self.display.blit(transition_surf, (0, 0))

            screenshake_offset = (random.random() * self.screenshake - self.screenshake / 2,
                                  random.random() * self.screenshake - self.screenshake / 2)
            update_bottom_text(self)

            if self.cutscene:
                draw_cutscene_border(self.display)
            else:
                draw_health_bar(self)

            self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), screenshake_offset)

            # --- Damage Flash Effect ---
            if self.damage_flash_active:
                if pygame.time.get_ticks() < self.damage_flash_end_time:
                    screen_shake(self, 16)
                    # (Code for drawing the red vignette/border effect)
                    screen_width, screen_height = self.screen.get_size()
                    border_surface = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)

                    elapsed = pygame.time.get_ticks() - (self.damage_flash_end_time - self.damage_flash_duration)
                    progress = elapsed / self.damage_flash_duration

                    max_border_width = 220
                    border_width = int(max_border_width * (1 - progress))
                    alpha_base = int(240 * (1 - progress))

                    # Optimization: Removed complex loop if not strictly needed for style,
                    # but kept it here as it seems to be a specific visual style you wanted.
                    # A faster way is to blit a pre-made vignette, but this is procedural.
                    for i in range(border_width):
                        fade_factor = 1 - (i / border_width)
                        color = (0, 0, 0, int(alpha_base * fade_factor))
                        pygame.draw.rect(border_surface, color, (i, i, screen_width - 2 * i, screen_height - 2 * i), 1)

                    self.screen.blit(border_surface, (0, 0))
                else:
                    self.damage_flash_active = False

            pygame.display.update()
            self.clock.tick(60)

Game().run()