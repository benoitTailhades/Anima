#Heavily upgraded basic godot physics code that I then converted to Python --Aymeric
from typing import reveal_type

import pygame as pg

import sys

import pygame

import random

from scripts.particle import Particle
from scripts.tilemap import Tilemap

class PhysicsPlayer:
    # Overall physics and movement handler
    def __init__(self, game, tilemap, pos, size):

        #Hitbox util vars
        self.game = game
        self.pos = list(pos)  # [x, y]
        self.size = size
        self.velocity = [0, 0]  # [vel_x, vel_y]
        self.acceleration = [0.0, 0.0]

        #Constants for movement
        self.SPEED = 2.5
        self.DASH_SPEED = 6
        self.JUMP_VELOCITY = -7.0
        self.DASHTIME = 12
        self.JUMPTIME = 10
        self.DASH_COOLDOWN = 50
        self.WALLJUMP_COOLDOWN = 5

        #Vars related to constants
        self.dashtime_cur = 0  # Used to determine whether we are dashing or not. Also serves as a timer.
        self.dash_cooldown = 0
        self.dash_amt = 1
        self.tech_momentum_mult = 0

        #Direction vars
        self.last_direction = 1
        self.dash_direction = [0, 0]  # [dash_x, dash_y]

        #Keyboard and movement exceptions utils
        self.dict_kb = {"key_right": 0, "key_left": 0, "key_up": 0, "key_down": 0, "key_jump": 0, "key_dash": 0,"key_noclip":0} #Used for reference
        self.anti_dash_buffer = False
        self.stop_dash_momentum = {"y": False,"x": False}
        self.holding_jump = False
        self.can_walljump = {"available": False, "wall": -1, "buffer": False, "timer": 0, "blocks_around": False, "cooldown":0}
        #available used to know if you can walljump, wall to know where the wall is located,
        #buffer to deal with logic conflicts in collision_check, timer for walljump coyote time
        self.dash_cooldown_cur = 0
        self.noclip = False
        self.noclip_buffer = False


        self.allowNoClip = False #MANUALLY TURN IT ON HERE TO USE NOCLIP

        #Tilemap (stage)
        self.tilemap = tilemap
        self.ghost_images = []

        self.facing = ""
        self.action = "idle"
        self.animation = self.game.assets['player/' + "idle"].copy()
        self.collision = {'left': False, 'right': False, 'bottom': False}
        self.get_block_on = {'left': False, 'right': False}
        self.air_time = 0

    def physics_process(self, tilemap, dict_kb):
        """Input : tilemap (map), dict_kb (dict)
        output : sends new coords for the PC to move to in accordance with player input and stage data (tilemap)"""
        self.dict_kb = dict_kb


        if not self.noclip:
            if self.dict_kb["key_noclip"] == 1 and self.allowNoClip:
                self.noclip = True

            self.air_time += 1
            direction = self.get_direction("x")
            if direction != 0:
                self.last_direction = direction

            if not self.dashtime_cur > 0:
                if self.velocity[0] != 0 and abs(self.velocity[0]) / self.velocity[0] != direction:
                    self.velocity[0] += direction * self.SPEED / 2
                elif abs(self.velocity[0]) <= abs(direction * self.SPEED):
                    self.velocity[0] = direction * self.SPEED

            self.gravity()
            self.jump()
            self.dash()
            self.dash_momentum()

            self.apply_momentum()

            self.apply_animations()
            self.apply_particle()
            self.animation.update()
        else:
            self.pos[0] += self.SPEED * self.get_direction("x")
            self.pos[1] += self.SPEED * -self.get_direction("y")
            if self.dict_kb["key_noclip"] == 1:
                self.noclip = False

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

        if self.dict_kb["key_attack"] == 1:
            if self.last_direction == 1:
                self.set_action("attack/right")
            elif self.last_direction == -1:
                self.set_action("attack/left")
            animation_applied = True

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


        # SECOND PRIORITY: Wall sliding
        if not animation_applied and self.velocity[1] > 0 and not self.is_on_floor() and self.can_walljump["blocks_around"]:
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
                animation_applied = True
            elif self.action in ("wall_slide/right", "wall_slide/left"):
                if self.get_direction("x") == 1 or self.last_direction >= 0:
                    self.set_action('falling/right')
                else:
                    self.set_action('falling/left')
                animation_applied = True

        # THIRD PRIORITY: Jumping/Falling
        if not animation_applied and not self.is_on_floor():
            # Initial jump
            if self.velocity[1] < 0 and self.air_time < 20:
                if self.get_direction("x") == 1:
                    self.set_action("jump/right")
                elif self.get_direction("x") == -1:
                    self.set_action("jump/left")
                elif self.get_direction("x") == 0:
                    self.set_action("jump/top")
                animation_applied = True
            # Falling
            else:
                if self.get_direction("x") == 1 or (self.action == 'falling/right' and self.get_direction("x") != -1):
                    self.set_action('falling/right')
                elif self.get_direction("x") == -1 or (self.action == 'falling/left' and self.get_direction("x") != 1):
                    self.set_action('falling/left')
                elif self.get_direction("x") == 0:
                    self.set_action('falling/vertical')
                animation_applied = True

        # FOURTH PRIORITY: Running
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
        for rect in self.tilemap.physics_rects_under(self.pos,self.size):
            entity_rect = pygame.Rect(self.pos[0], self.pos[1] + 1, self.size[0], self.size[1])
            if entity_rect.colliderect(rect):
                return self.rect().bottom == rect.top and self.velocity[1] >= 0
        return False

    def gravity(self):
        """Handles gravity. Gives downwards momentum (capped at 5) if in the air, negates momentum if on the ground, gives back a dash if the
        player is missing some. Stops movement if no input is given."""
        if not self.is_on_floor() and not self.dashtime_cur > 0:
            if self.can_walljump["available"]:
                if self.acceleration[1] == 0.6:
                    self.velocity[1] = 0
                self.acceleration[1] = 0.1
            else:
                self.acceleration[1] = 0.6
            self.velocity[1] = min(7, self.velocity[1] + self.acceleration[1])
        elif self.is_on_floor():
            if self.velocity[1] > 0:
                self.velocity[1] = 0
            if self.dashtime_cur < 5 and self.dash_amt == 0:
                self.dash_amt = 1
            # Stop unintended horizontal movement if no input is given
            if self.get_direction("x") == 0:
                self.velocity[0] = 0

    def jump(self):
        """Handles player jump and super/hyperdash tech"""

        #Jumping
        if self.dict_kb["key_jump"] == 1 and self.is_on_floor() and not self.holding_jump: #Jump on the ground
            self.jump_logic_helper()

            # Tech
            if self.dashtime_cur != 0:
                self.dashtime_cur = 0
                self.tech_momentum_mult = pow(abs(self.dash_direction[0]) + abs(self.dash_direction[1]), 0.5)
                self.velocity[0] = self.get_direction("x") * self.DASH_SPEED * self.tech_momentum_mult
                self.velocity[1] /= self.tech_momentum_mult

        elif self.dict_kb["key_jump"] == 1 and self.can_walljump["available"] == True and not self.holding_jump and self.can_walljump["blocks_around"] and self.can_walljump["cooldown"] < 1: #Walljump
            self.jump_logic_helper()
            if self.can_walljump["wall"] == self.get_direction("x"): #Jumping into the wall
                self.velocity[0] = -self.can_walljump["wall"] * self.SPEED * 3
                self.velocity[1] *= 1.3
            else: #Jumping away from the wall
                self.velocity[0] = -self.can_walljump["wall"] * self.SPEED * 1.5

            self.can_walljump["available"] = False

        if self.dict_kb["key_jump"] == 0:
            self.holding_jump = False

    def jump_logic_helper(self):
        """Avoid code redundancy"""
        self.velocity[1] = self.JUMP_VELOCITY
        self.holding_jump = True

    def dash(self):
        """Handles player dash."""
        self.dash_cooldown_cur = max(self.dash_cooldown_cur-1,0)
        if not self.anti_dash_buffer:
            self.dash_direction = [self.get_direction("x"), max(0, self.get_direction("y"))]
            if self.dict_kb["key_dash"] == 1 and self.dash_cooldown_cur == 0 and self.dash_direction != [0, -1]:
                if self.dash_amt > 0:
                    if self.dash_direction == [0, 0]:
                        self.dash_direction[0] = self.last_direction
                    self.dashtime_cur = self.DASHTIME
                    self.stop_dash_momentum["y"],self.stop_dash_momentum["x"] = False,False
                    self.dash_amt -= 1
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

            for rect in tilemap.physics_rects_under(self.pos, self.size):
                if entity_rect.colliderect(rect):
                    if self.velocity[1] > 0:
                        self.pos[1] = rect.top - entity_rect.height
                        self.velocity[1] = 0
                        self.collision['bottom'] = True
                        self.can_walljump["buffer"] = True
                        self.can_walljump["available"] = False

            for rect in tilemap.physics_rects_around(self.pos, self.size):
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
            for rect in tilemap.physics_rects_around(self.pos, self.size):
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
                if rect.x < entity_rect.x:
                    b_l.add(True)
                if rect.x > entity_rect.x:
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

        if self.is_on_floor():
            self.air_time = 0
            self.velocity[0] *= 0.2
        elif self.get_direction("x") == 0:
            self.velocity[0] *= 0.8

    def get_direction(self, axis):
        """Gets the current direction the player is holding towards. Takes an axis as argument ('x' or 'y')
        returns : -1 if left/down, 1 if right/up. 0 if bad arguments"""
        if axis == "x":
            return self.dict_kb["key_right"] - self.dict_kb["key_left"]
        elif axis == "y":
            return self.dict_kb["key_up"] - self.dict_kb["key_down"]
        else:
            print("Error: get_direction() received an invalid axis")
            return 0

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
