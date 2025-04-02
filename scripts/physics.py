#Heavily upgraded basic godot physics code that I then converted to Python --Aymeric
from typing import reveal_type

import pygame as pg

import sys

import pygame

from scripts.tilemap import Tilemap

class PhysicsPlayer:
    # Overall physics and movement handler
    def __init__(self, game, tilemap, pos, size):

        #Hitbox util vars
        self.game = game
        self.pos = list(pos)  # [x, y]
        self.size = size
        self.velocity = [0, 0]  # [vel_x, vel_y]

        #Constants for movement
        self.SPEED = 2.5
        self.DASH_SPEED = 6
        self.JUMP_VELOCITY = -6.0
        self.DASHTIME = 12
        self.JUMPTIME = 10
        self.DASH_COOLDOWN = 50

        #Vars related to constants
        self.dashtime_cur = 0  # Used to determine whether we are dashing or not. Also serves as a timer.
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
        self.can_walljump = {"available":False,"wall":-1,"buffer":False,"timer":0,"blocks_around":0}
        #available used to know if you can walljump, wall to know where the wall is located,
        #buffer to deal with logic conflicts in collision_check, timer for walljump coyote time
        self.dash_cooldown_cur = 0
        self.noclip = False
        self.noclip_buffer = False


        self.allowNoClip = False #MANUALLY TURN IT ON HERE TO USE NOCLIP

        #Tilemap (stage)
        self.tilemap = tilemap

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

        # HIGHEST PRIORITY: Dash animations
        if self.dashtime_cur > 0:
            if self.dash_direction[0] == 1:
                self.set_action("dash/right")
                animation_applied = True
            elif self.dash_direction[0] == -1:
                self.set_action("dash/left")
                animation_applied = True
            elif self.dash_direction[0] == 0:  # Vertical dash
                if self.last_direction >= 0:
                    self.set_action("dash/right")
                else:
                    self.set_action("dash/left")
                animation_applied = True

        # SECOND PRIORITY: Wall sliding
        if not animation_applied and self.velocity[1] > 0 and not self.is_on_floor() and self.can_walljump["blocks_around"] >= 2:
            if self.collision["right"] and self.get_block_on["right"]:
                self.set_action("wall_slide/right")
                self.facing = "left"
                animation_applied = True
            elif self.collision["left"] and self.get_block_on["left"]:
                self.set_action("wall_slide/left")
                self.facing = "right"
                animation_applied = True

        if not animation_applied and (self.collision["right"] or self.collision["left"]):
            self.set_action("idle")
            animation_applied = True

        # THIRD PRIORITY: Jumping/Falling
        if not animation_applied and not self.is_on_floor():
            # Initial jump
            if self.velocity[1] < 0 and self.air_time < 20:
                if self.last_direction >= 0:
                    self.set_action("jump/right")
                else:
                    self.set_action("jump/left")
                animation_applied = True
            # Falling
            else:
                if self.get_direction("x") == 1 or self.last_direction >= 0:
                    self.set_action('falling/right')
                else:
                    self.set_action('falling/left')
                animation_applied = True

        # FOURTH PRIORITY: Running
        if not animation_applied and self.is_on_floor() and abs(self.velocity[0]) > 0.1:
            if self.velocity[0] > 0:
                self.set_action("run/right")
            else:
                self.set_action("run/left")
            animation_applied = True

        # LOWEST PRIORITY: Idle
        if not animation_applied:
            self.set_action("idle")

    def rect(self):
        return pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])

    def is_on_floor(self):
        """Uses tilemap to check if on (above, standing on) a tile. used for gravity, jump, etc."""
        for rect in self.tilemap.physics_rects_under(self.pos,self.size):
            entity_rect = pygame.Rect(self.pos[0], self.pos[1] + 1, self.size[0], self.size[1])
            if entity_rect.colliderect(rect):
                return self.rect().bottom == rect.top
        return False

    def gravity(self):
        """Handles gravity. Gives downwards momentum (capped at 5) if in the air, negates momentum if on the ground, gives back a dash if the
        player is missing some. Stops movement if no input is given."""
        if not self.is_on_floor() and not self.dashtime_cur > 0:
            self.velocity[1] = min(5, self.velocity[1] + 0.5)
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

        elif self.dict_kb["key_jump"] == 1 and self.can_walljump["available"] == True and not self.holding_jump and self.can_walljump["blocks_around"] >= 2: #Walljump
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
            self.dashtime_cur -= 1
            if not self.stop_dash_momentum["x"]:
                self.velocity[0] = self.dash_direction[0] * self.DASH_SPEED
            if not self.stop_dash_momentum["y"]:
                self.velocity[1] = -self.dash_direction[1] * self.DASH_SPEED
            if self.dashtime_cur == 0:
                self.velocity = [0, 0]

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
            for rect in tilemap.physics_rects_around(self.pos, self.size):
                self.can_walljump["blocks_around"] += 1
                if entity_rect.colliderect(rect):
                    if self.velocity[0] > 0:
                        entity_rect.right = rect.left
                        self.collision['right'] = True
                        self.collision_check_walljump_helper(1)
                        self.anti_dash_buffer = True
                        self.dash_cooldown = 5

                    if self.velocity[0] < 0:
                        entity_rect.left = rect.right
                        self.collision['left'] = True
                        self.collision_check_walljump_helper(-1)
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
        if not self.can_walljump["buffer"]:
            self.can_walljump["available"] = True
            self.can_walljump["wall"] = axis
            self.can_walljump["timer"] = 8

    def apply_momentum(self):
        """Applies velocity to the coords of the object. Slows down movement depending on environment"""
        self.can_walljump["blocks_around"] = 0
        if int(self.velocity[0]) != 0:
            self.collision["left"] = False
            self.collision["right"] = False
        if self.velocity[1] > 0:
            self.collision["bottom"] = False
        self.pos[0] += self.velocity[0]
        self.collision_check("x")
        self.pos[1] += self.velocity[1]
        self.collision_check("y")

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

    def render(self, surf, offset = (0, 0)):
        r = pygame.Rect(self.pos[0] - offset[0], self.pos[1] - offset[1], self.size[0], self.size[1])
        surf.blit(self.animation.img(), (self.pos[0] - offset[0] - 8, self.pos[1] - offset[1] - 5))
        #pygame.draw.rect(surf, (255,230,255), r)