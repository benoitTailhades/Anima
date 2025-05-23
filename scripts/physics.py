#Heavily upgraded basic godot physics code that I then converted to Python --Aymeric
import time
from typing import reveal_type

import pygame as pg

import sys

import pygame
from time import sleep

import random

from scripts.particle import Particle
from scripts.tilemap import Tilemap
from scripts.sound import *
from scripts.entities import deal_knockback, update_throwable_objects_action

class PhysicsPlayer:
    def __init__(self, game, tilemap, pos, size):

        # Hitbox util vars
        self.game = game
        self.pos = list(pos)  # [x, y]
        self.size = size
        self.velocity = [0, 0]  # [vel_x, vel_y]
        self.acceleration = [0.0, 0.0]

        # Constants for movement
        self.SPEED = 2.5
        self.DASH_SPEED = 6
        self.JUMP_VELOCITY = -6.5
        self.DASHTIME = 12
        self.JUMPTIME = 10
        self.DASH_COOLDOWN = 50
        self.WALLJUMP_COOLDOWN = 5

        # Vars related to constants
        self.dashtime_cur = 0  # Used to determine whether we are dashing or not. Also serves as a timer.
        self.dash_cooldown = 0
        self.dash_amt = 1
        self.tech_momentum_mult = 0

        # Direction vars
        self.last_direction = 1
        self.dash_direction = [0, 0]  # [dash_x, dash_y]

        # Keyboard and movement exceptions utils
        self.dict_kb = {"key_right": 0, "key_left": 0, "key_up": 0, "key_down": 0, "key_jump": 0, "key_dash": 0,
                        "key_noclip": 0}  # Used for reference
        self.anti_dash_buffer = False
        self.stop_dash_momentum = {"y": False, "x": False}
        self.holding_jump = False
        self.can_walljump = {"available": False, "wall": -1, "buffer": False, "timer": 0, "blocks_around": False,
                             "cooldown": 0, "allowed": True}
        self.force_movement = {"r":[False,0],"l":[False,0]}
        self.prevent_walking = False
        # available used to know if you can walljump, wall to know where the wall is located,
        # buffer to deal with logic conflicts in collision_check, timer for walljump coyote time
        self.dash_cooldown_cur = 0
        self.noclip = False
        self.noclip_buffer = False

        self.is_stunned = False
        self.last_stun_time = 0
        self.stunned_by = None
        self.knockback_dir = [0, 0]
        self.knockback_strenght = 4
        self.knockback_duration = 0.5

        self.allowNoClip = True  # MANUALLY TURN IT ON HERE TO USE NOCLIP

        # Tilemap (stage)
        self.tilemap = tilemap
        self.ghost_images = []

        self.facing = ""
        self.action = "idle"
        self.animation = self.game.assets['player/' + "idle"].copy()
        self.collision = {'left': False, 'right': False, 'bottom': False}
        self.get_block_on = {'left': False, 'right': False}
        self.air_time = 0
        self.disablePlayerInput = False

        # Système de son
        self.init_sound_system()

        # Variables pour gérer les états des sons
        self.was_on_floor = True  # Pour gérer le son d'atterrissage
        self.running_sound_playing = False
        self.run_sound_timer = 0
        self.run_sound_interval = 15  # Intervalle entre les répétitions du son de course
        self.last_action = "idle"  # Pour détecter les changements d'action

    def init_sound_system(self):
        """Initialise le système de son avec tous les fichiers nécessaires"""
        # Dictionnaire qui stockera tous les sons
        base_path = "assets/sounds/player/"
        self.sounds = {
            'jump': base_path + "jump.wav",
            'dash': base_path + "dash.wav",
            'wall_jump': base_path + "wall_jump.wav",
            'land': base_path + "land.wav",
            'run': base_path + "run.wav",
            'walk': None,
            'stun': None
        }
        load_sounds(self, self.sounds)

    def play_sound(self, sound_key, force=False):
        """
        Joue un son spécifique

        Args:
            sound_key: La clé du son à jouer
            force: Si True, joue le son même s'il est déjà en cours
        """
        if sound_key in self.sounds and self.sounds[sound_key]:
            if force:
                self.sounds[sound_key].stop()

            # Vérifier si le son est déjà en cours de lecture
            if not pygame.mixer.Channel(0).get_busy() or force:
                self.sounds[sound_key].play(loops=0, maxtime=0, fade_ms=0)

    def update_sounds(self):
        """Met à jour et gère les sons en fonction de l'état du joueur"""

        # Son d'atterrissage
        if self.is_on_floor() and not self.was_on_floor:
            self.play_sound('land', True)

        # Mise à jour de l'état du sol pour le prochain frame
        self.was_on_floor = self.is_on_floor()

        # Son de course/marche
        if "run" in self.action:
            self.run_sound_timer += 1

            # Détermine si le joueur court ou marche
            sound_key = 'run' if abs(self.velocity[0]) > 1.5 else 'walk'

            # Joue le son à intervalles réguliers pour créer un effet de pas
            if self.run_sound_timer >= self.run_sound_interval:
                self.play_sound('run', True)
                self.run_sound_timer = 0
        else:
            self.run_sound_timer = 0

        # Détecte les changements d'action pour les événements ponctuels
        if self.action != self.last_action:
            if self.action in ["stun"]:
                self.play_sound('stun')

            self.last_action = self.action

    def physics_process(self, tilemap, dict_kb):
        """Input : tilemap (map), dict_kb (dict)
        output : sends new coords for the PC to move to in accordance with player input and stage data (tilemap)"""
        self.dict_kb = dict_kb
        self.force_player_movement()

        if self.disablePlayerInput:
            self.dict_kb = {"key_right": 0, "key_left": 0, "key_up": 0, "key_down": 0, "key_jump": 0, "key_dash": 0,
                            "key_noclip": 0}
            # Consider all keys as not pressed


        if self.is_stunned:
            # Calculate time since stun started
            stun_elapsed = time.time() - self.last_stun_time
            stun_duration = 0.2

            if stun_elapsed < stun_duration:
                if self.stunned_by:
                    self.velocity = list(deal_knockback(self.stunned_by, self, self.knockback_strenght, self.knockback_duration))

                # Jouer le son de stun
                if stun_elapsed < 0.05:  # Pour ne jouer le son qu'une fois au début du stun
                    self.play_sound('stun')

                # When stunned, only apply knockback and gravity
                self.gravity()
                self.apply_momentum()
                self.apply_animations()
                self.animation.update()
                return  # Skip the rest of the normal update logic
            else:
                self.stunned_by = None
                self.is_stunned = False
                self.knockback_dir = [0, 0]

        if not self.noclip:
            if self.dict_kb["key_noclip"] == 1 and self.allowNoClip:
                self.noclip = True

            self.air_time += 1
            direction = self.get_direction("x")
            if direction != 0:
                self.last_direction = direction

            if not self.dashtime_cur > 0 and not self.prevent_walking:
                self.walk(direction)

            self.gravity()
            self.jump()
            self.dash()
            self.dash_momentum()

            self.apply_momentum()

            self.apply_animations()
            self.apply_particle()
            self.animation.update()

            # Mise à jour des sons
            self.update_sounds()

        else:
            self.pos[0] += self.SPEED * self.get_direction("x")
            self.pos[1] += self.SPEED * -self.get_direction("y")


            if self.dict_kb["key_noclip"] == 1:
                self.noclip = False

    def force_player_movement(self):
        """forces some keys to be pressed"""
        if self.force_movement["r"][0] or self.force_movement["l"][0]:
            if self.force_movement["l"][0]:
                self.walk(-1,1.5)
            else:
                self.walk(1,1.5)
            if (self.force_movement["l"][1] < 1 and self.force_movement["l"][0]) or (self.force_movement["r"][0] and self.force_movement["r"][1] < 1) or self.is_on_floor():
                self.force_movement = {"r":[False,0],"l":[False,0]}
            else:
                self.force_movement["l"][1] -= 1
                self.force_movement["r"][1] -= 1

    def walk(self,direction,mult=1):
        """Changes x velocity depending on current speed and direction. To make walking faster in specific calls, use the mult parameter"""
        if self.velocity[0] != 0 and abs(self.velocity[0]) / self.velocity[0] != float(direction):
            self.velocity[0] += direction * self.SPEED / 2 * mult
        elif abs(self.velocity[0]) <= abs(direction * self.SPEED*mult):
            self.velocity[0] = direction * self.SPEED * mult

    def set_action(self, action):
        if action != self.action :
            self.action = action
            self.animation = self.game.assets['player/' + self.action].copy()

    def apply_animations(self):
        """
        Handles animation state changes based on player movement state.
        Follows clear priority rules for animations.
        """
        # Reset animation flags
        animation_applied = False

        # Check if we just finished dashing this frame
        just_finished_dash = self.dashtime_cur == 0 and self.action in ("dash/right", "dash/left")

        # HIGHEST PRIORITY: Dash animations
        if self.dashtime_cur > 0:
            if self.dash_direction[0] == 1:
                self.set_action("dash/right")
                animation_applied = True
            elif self.dash_direction[0] == -1:
                self.set_action("dash/left")
                animation_applied = True
            elif self.dash_direction[0] == 0:  # Vertical dash
                self.set_action("dash/top")
                animation_applied = True

        # SECOND PRIORITY: Attack animation (moved up in priority)
        if not animation_applied and self.game.attacking and not self.animation.done:
            if self.last_direction == 1:
                self.set_action("attack/right")
                animation_applied = True
            elif self.last_direction == -1:
                self.set_action("attack/left")
                animation_applied = True

        # THIRD PRIORITY: Wall sliding
        if not animation_applied and self.velocity[1] > 0 and not self.is_on_floor() and self.can_walljump[
            "blocks_around"]:
            if self.collision["right"]:
                self.set_action("wall_slide/right")
                self.facing = "left"
                animation_applied = True
            elif self.collision["left"]:
                self.set_action("wall_slide/left")
                self.facing = "right"
                animation_applied = True

        if not animation_applied and (self.collision["right"] or self.collision["left"]):
            if self.is_on_floor():
                self.set_action("idle")
                animation_applied = True  # Add this line to prevent overriding
            elif self.action in ("wall_slide/right", "wall_slide/left"):
                if self.get_direction("x") == 1 or self.last_direction >= 0:
                    self.set_action('falling/right')
                else:
                    self.set_action('falling/left')
                animation_applied = True

        # FOURTH PRIORITY: Jumping/Falling
        if not animation_applied and not self.is_on_floor():
            # Initial jump
            if self.velocity[1] < 0 and self.air_time < 20:
                if self.get_direction("x") == 0:
                    self.set_action("jump/top")

                elif self.get_direction("x") == 1 and self.action != "jump/top":
                    self.set_action("jump/right")
                elif self.get_direction("x") == -1 and self.action != "jump/top":
                    self.set_action("jump/left")
                animation_applied = True
            # Falling
            else:
                if (self.get_direction("x") == 1 or (self.action == 'falling/right' and self.get_direction("x") != -1) or self.force_movement["r"][0]) and not self.force_movement["l"][0]:
                    self.set_action('falling/right')
                elif self.get_direction("x") == -1 or (self.action == 'falling/left' and self.get_direction("x") != 1) or self.force_movement["l"][0]:
                    self.set_action('falling/left')
                elif self.get_direction("x") == 0:
                    self.set_action('falling/vertical')
                animation_applied = True

        # FIFTH PRIORITY: Running
        # Check if player is moving OR just finished a dash and is trying to move
        if not animation_applied and (
                (self.is_on_floor() and abs(self.velocity[0]) > 0.1) or
                (just_finished_dash and self.get_direction("x") != 0)
        ):
            if self.get_direction("x") > 0 or (just_finished_dash and self.dash_direction[0] > 0):
                self.set_action("run/right")
            else:
                self.set_action("run/left")
            animation_applied = True

        # LOWEST PRIORITY: Idle
        if not animation_applied:
            self.set_action("idle")

    def apply_particle(self):
        '''if self.velocity[1] < 0 and self.air_time < 20:
            self.game.particles.append(Particle(self.game, 'leaf', self.pos, velocity=[-0.1, 0.3], frame=random.randint(0, 20)))'''

    def rect(self):
        return pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])

    def is_on_floor(self):
        """Uses tilemap to check if on (above, standing on) a tile. used for gravity, jump, etc."""
        for rect in self.tilemap.physics_rects_under(self.pos,self.size) + self.game.doors_rects:
            entity_rect = pygame.Rect(self.pos[0], self.pos[1] + 1, self.size[0], self.size[1])
            if entity_rect.colliderect(rect):
                return self.rect().bottom == rect.top and self.velocity[1] >= 0
        return False

    def gravity(self):
        """Handles gravity. Gives downwards momentum (capped at 5) if in the air, negates momentum if on the ground, gives back a dash if the
        player is missing some. Stops movement if no input is given."""
        if not self.is_on_floor() and not self.dashtime_cur > 0:
            if self.can_walljump["available"]:
                if self.acceleration[1] == 0.45:
                    self.velocity[1] = 0
                self.acceleration[1] = 0.1
            else:
                self.acceleration[1] = 0.45
            self.velocity[1] = min(7, self.velocity[1] + self.acceleration[1])
        elif self.is_on_floor():
            if self.velocity[1] > 0:
                self.velocity[1] = 0
            if self.dashtime_cur < 5 and self.dash_amt == 0:
                self.dash_amt = 1
            # Stop unintended horizontal movement if no input is given
            if self.get_direction("x") == 0 and not self.is_stunned:
                self.velocity[0] = 0

    def disallow_movement(self,bool):
        """allows to disable or re-enable player movement. Bool as parameter, True to disable, False to enable movement."""
        self.disablePlayerInput = bool

    def jump(self):
        """Handles player jump and super/hyperdash tech"""

        # Jumping
        if self.dict_kb["key_jump"] == 1 and self.is_on_floor() and not self.holding_jump:  # Jump on the ground
            self.jump_logic_helper()

            # Jouer le son de saut
            self.play_sound('jump', True)

            # Tech
            if self.dashtime_cur != 0:
                self.dashtime_cur = 0
                self.tech_momentum_mult = pow(abs(self.dash_direction[0]) + abs(self.dash_direction[1]), 0.5)
                self.velocity[0] = self.get_direction("x") * self.DASH_SPEED * self.tech_momentum_mult
                self.velocity[1] /= self.tech_momentum_mult

        elif self.dict_kb["key_jump"] == 1 and self.can_walljump["available"] == True and not self.holding_jump and \
                self.can_walljump["blocks_around"] and self.can_walljump["cooldown"] < 1 and self.can_walljump[
            "allowed"]:  # Walljump
            self.jump_logic_helper()

            # Jouer le son de wall jump
            self.play_sound('wall_jump', True)

            if self.can_walljump["wall"] == self.get_direction("x"):  # Jumping into the wall
                self.velocity[0] = -self.can_walljump["wall"] * self.SPEED * 3
                self.velocity[1] *= 1.18
            else:  # Jumping away from the wall
                self.velocity[0] = 0
                if self.can_walljump["wall"] == 1:
                    self.force_movement["l"] = [True, 22]
                    self.force_movement["r"] = [False, 0]
                else:
                    self.force_movement["r"] = [True, 22]
                    self.force_movement["l"] = [False, 0]


            self.can_walljump["available"] = False

        if self.dict_kb["key_jump"] == 0:
            self.holding_jump = False

    def jump_logic_helper(self):
        """Avoid code redundancy"""
        self.velocity[1] = self.JUMP_VELOCITY
        self.holding_jump = True

    def dash(self):
        """Handles player dash."""
        self.dash_cooldown_cur = max(self.dash_cooldown_cur - 1, 0)
        if not self.anti_dash_buffer:
            self.dash_direction = [self.get_direction("x"), max(0, self.get_direction("y"))]
            if self.dict_kb["key_dash"] == 1 and self.dash_cooldown_cur == 0 and self.dash_direction != [0, -1]:
                if self.game.player_grabbing:
                    update_throwable_objects_action(self.game)
                if self.dash_amt > 0:
                    if self.dash_direction == [0, 0]:
                        self.dash_direction[0] = self.last_direction
                    self.dashtime_cur = self.DASHTIME
                    self.stop_dash_momentum["y"], self.stop_dash_momentum["x"] = False, False
                    self.dash_amt -= 1

                    # Jouer le son de dash
                    self.play_sound('dash', force=True)

                self.anti_dash_buffer = True
                self.dash_cooldown_cur = self.DASH_COOLDOWN
        else:
            if self.dict_kb["key_dash"] == 0:
                self.anti_dash_buffer = False

    def dash_momentum(self):
        """Applies momentum from dash. Deletes all momentum when the dash ends."""
        if self.dashtime_cur > 0:
            self.dash_ghost_trail()
            self.dashtime_cur -= 1
            if not self.stop_dash_momentum["x"]:
                self.velocity[0] = self.dash_direction[0] * self.DASH_SPEED
            if not self.stop_dash_momentum["y"]:
                self.velocity[1] = -self.dash_direction[1] * self.DASH_SPEED
            if self.dashtime_cur == 0:
                self.velocity = [0, 0]

        self.update_ghost_trail()

    def collision_check(self, axe):
        """Checks for collision using tilemap"""
        entity_rect = self.rect()
        tilemap = self.tilemap
        b_r = set()
        b_l = set()

        # Handle Vertical Collision First
        if axe == "y":
            backup_velo = self.velocity[1]
            entity_rect.y += self.velocity[1]

            self.can_walljump["buffer"] = False
            self.can_walljump["timer"] = max(0, self.can_walljump["timer"] - 1)

            if self.can_walljump["timer"] == 0:
                self.can_walljump["available"] = False

            for rect in tilemap.physics_rects_under(self.pos, self.size) + self.game.doors_rects:
                if entity_rect.colliderect(rect):
                    if self.velocity[1] > 0:
                        self.pos[1] = rect.top - entity_rect.height
                        self.velocity[1] = 0
                        self.collision['bottom'] = True
                        self.can_walljump["buffer"] = True
                        self.can_walljump["available"] = False

            for rect in tilemap.physics_rects_around(self.pos, self.size) + self.game.doors_rects:
                if entity_rect.colliderect(rect):
                    if self.velocity[1] < 0:
                        self.pos[1] = rect.bottom
                        self.velocity[1] = 0
                        self.can_walljump["buffer"] = True
                        self.can_walljump["available"] = False

                    self.stop_dash_momentum["y"] = True

            entity_rect.y -= backup_velo

        if axe == "x":
            entity_rect.x += self.velocity[0]  # Predict horizontal movement
            if self.can_walljump["available"]:
                self.can_walljump["cooldown"] = max(self.can_walljump["cooldown"]-1,0)
            for rect in tilemap.physics_rects_around(self.pos, self.size) + self.game.doors_rects:
                if entity_rect.colliderect(rect):
                    if self.velocity[0] > 0:
                        entity_rect.right = rect.left
                        self.collision['right'] = True
                        self.anti_dash_buffer = True
                        self.dash_cooldown = 5

                    if self.velocity[0] < 0:
                        entity_rect.left = rect.right
                        self.collision['left'] = True
                        self.anti_dash_buffer = True
                        self.dash_cooldown = 5
                    self.pos[0] = entity_rect.x
                    self.stop_dash_momentum["x"] = True
                if entity_rect.x - 17 < rect.x < entity_rect.x:
                    b_l.add(True)
                if entity_rect.x + 32 > rect.x > entity_rect.x:
                    b_r.add(True)

            self.get_block_on["left"] = bool(b_l)
            self.get_block_on["right"] = bool(b_r)

    def collision_check_walljump_helper(self,axis):
        """Avoids redundancy"""
        if not self.can_walljump["buffer"] and self.velocity[1] > 0 and not self.is_on_floor() and self.can_walljump["blocks_around"]:
            if not self.can_walljump["available"]:
                self.can_walljump["cooldown"] = self.WALLJUMP_COOLDOWN
            self.can_walljump["available"] = True
            self.can_walljump["wall"] = axis
            self.can_walljump["timer"] = 16

    def apply_momentum(self):
        """Applies velocity to the coords of the object. Slows down movement depending on environment"""
        self.can_walljump["blocks_around"] = (self.tilemap.solid_check((self.rect().centerx + 11*self.last_direction, self.pos[1])) and
                                              self.tilemap.solid_check((self.rect().centerx + 11*self.last_direction, self.pos[1] + self.size[1])))

        if int(self.velocity[0]) > 0 or not self.get_block_on["left"]:
            self.collision["left"] = False
        if int(self.velocity[0]) < 0 or not self.get_block_on["right"]:
            self.collision["right"] = False
        if self.velocity[1] > 0:
            self.collision["bottom"] = False
        self.pos[0] += self.velocity[0]
        self.collision_check("x")

        self.pos[1] += self.velocity[1]
        self.collision_check("y")

        if self.collision["right"]:
            self.collision_check_walljump_helper(1)
        if self.collision["left"]:
            self.collision_check_walljump_helper(-1)

        if not( not self.can_walljump["buffer"] and self.velocity[1] > 0 and not self.is_on_floor() and self.can_walljump[
            "blocks_around"]):
            self.can_walljump["available"] = False

        if not self.is_stunned:
            if self.is_on_floor():
                self.air_time = 0
                self.velocity[0] *= 0.2
            elif self.get_direction("x") == 0:
                self.velocity[0] *= 0.8
        else:
            self.velocity[0] *= 0.95

    def get_direction(self, axis):
        """Gets the current direction the player is holding towards. Takes an axis as argument ('x' or 'y')
        returns : -1 if left/down, 1 if right/up. 0 if bad arguments"""
        if axis == "x":
            return self.dict_kb["key_right"] - self.dict_kb["key_left"]
        elif axis == "y":
            return self.dict_kb["key_up"] - self.dict_kb["key_down"]

    def dash_ghost_trail(self):
        """Creates ghost images that fade out over time."""
        # Store current position and image with a timer
        ghost = {
            "pos": self.pos.copy(),  # Assuming self.pos is a list or has a copy method
            "img": self.animation.img().copy(),  # Create a copy of the current image
            "lifetime": 20  # How long the ghost remains visible (in frames)
        }

        # Add to list of ghost images
        self.ghost_images.append(ghost)

        # Max number of ghost images to prevent using too much memory
        max_ghosts = 20
        if len(self.ghost_images) > max_ghosts:
            self.ghost_images.pop(0)

    def update_ghost_trail(self):
        for ghost in self.ghost_images[:]:
            ghost["lifetime"] -= 1
            if ghost["lifetime"] <= 0:
                self.ghost_images.remove(ghost)

    def render(self, surf, offset = (0, 0)):
        r = pygame.Rect(self.pos[0] - offset[0], self.pos[1] - offset[1], self.size[0], self.size[1])
        #pygame.draw.rect(surf, (255, 230, 255), r)

        for ghost in self.ghost_images[:]:
            # Calculate transparency based on remaining lifetime
            alpha = int(255 * (ghost["lifetime"] / 20) ** 2)
            # Create a copy with transparency
            ghost_surf = ghost["img"].copy()
            ghost_surf.fill((255, 255, 255, 0), special_flags=pygame.BLEND_RGBA_MAX)
            ghost_surf.fill((109, 156, 159, 70),  special_flags=pygame.BLEND_RGBA_MIN)
            ghost_surf.set_alpha(alpha)
            # Draw ghost
            surf.blit(ghost_surf, (ghost["pos"][0] - offset[0] - 11, ghost["pos"][1] - offset[1] - 5))

        surf.blit(self.animation.img(), (self.pos[0] - offset[0] - 11, self.pos[1] - offset[1] - 5))
