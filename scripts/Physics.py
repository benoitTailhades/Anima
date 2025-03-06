#Heavily upgraded basic godot physics code that i then converted to Python --Aymeric
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

        #Vars related to constants
        self.dashtime_cur = 0  # Used to determine whether we are dashing or not. Also serves as a timer.
        self.dash_amt = 1
        self.tech_momentum_mult = 0

        #Direction vars
        self.direction = 0
        self.last_direction = 1
        self.dash_direction = [0, 0]  # [dash_x, dash_y]

        #Keyboard and movement exceptions utils
        self.dict_kb = {"key_right": 0, "key_left": 0, "key_up": 0, "key_down": 0, "key_jump": 0, "key_dash": 0}
        self.anti_dash_buffer = False
        self.stop_dash_momentum = {"y":False,"x":False}

        #Tilemap (stage)
        self.tilemap = tilemap

    def physics_process(self, tilemap, dict_kb):
        """Input : tilemap (map), dict_kb (dict)
        output : sends new coords for the PC to move to in accordance with player input and stage data (tilemap)"""
        self.dict_kb = dict_kb


        self.direction = self.get_direction("x")
        if self.direction != 0:
            self.last_direction = self.direction

        if not self.dashtime_cur > 0:
            if self.velocity[0] != 0 and abs(self.velocity[0]) / self.velocity[0] != self.direction:
                self.velocity[0] += self.direction * self.SPEED / 2
            elif abs(self.velocity[0]) <= abs(self.direction * self.SPEED):
                self.velocity[0] = self.direction * self.SPEED


        self.gravity()
        self.jump()
        self.dash()
        self.dash_momentum()
        self.collision_check()

        self.apply_momentum()

    def is_on_floor(self, cur_y="undef"):
        """Uses tilemap to check if on (above, standing on) a tile. used for gravity, jump, etc."""
        entity_rect = self.rect()
        if cur_y == "undef":
            cur_y = entity_rect.bottom

        # Create a slightly extended rectangle (e.g., 1px lower) to check for near-ground collisions
        expanded_rect = entity_rect.copy()
        expanded_rect.height += 1  # Extend the bottom of the rectangle by 1 pixel

        for rect in self.tilemap.physics_rects_around(self.pos):
            if expanded_rect.colliderect(rect):
                self.pos[1] = rect.top - self.size[1]
                return cur_y >= rect.top
        return False

    def gravity(self):
        """Handles gravity. Gives downwards momentum (capped at 5) if in the air, negates momentum if on the ground, gives back a dash if the
        player is missing some. Stops movement if no input is given."""
        if not self.is_on_floor() and not self.dashtime_cur > 0:
            self.velocity[1] = min(5, self.velocity[1] + 0.5)
        elif self.is_on_floor():
            if self.velocity[1] > 0:
                self.velocity[1] = 0
            if self.dashtime_cur < 10 and self.dash_amt == 0:
                self.dash_amt = 1
            # Stop unintended horizontal movement if no input is given
            if self.get_direction("x") == 0:
                self.velocity[0] = 0

    def jump(self):
        """Handles player jump and super/hyperdash tech"""

        #Jumping
        print(self.is_on_floor())
        if self.dict_kb["key_jump"] == 1 and self.is_on_floor():
            self.velocity[1] = self.JUMP_VELOCITY

            #Tech
            if self.dashtime_cur != 0:
                self.dashtime_cur = 0
                self.tech_momentum_mult = pow(abs(self.dash_direction[0]) + abs(self.dash_direction[1]), 0.5)
                self.velocity[0] = self.get_direction("x") * self.DASH_SPEED * self.tech_momentum_mult
                self.velocity[1] /= self.tech_momentum_mult

    def dash(self):
        """Handles player dash."""
        if not self.anti_dash_buffer:
            if self.dict_kb["key_dash"] == 1:
                if self.dash_amt > 0:
                    self.dash_direction = [self.get_direction("x"), self.get_direction("y")]
                    if self.dash_direction == [0, 0]:
                        self.dash_direction[0] = self.last_direction
                    self.dashtime_cur = self.DASHTIME
                    self.stop_dash_momentum["y"],self.stop_dash_momentum["x"] = False,False
                    self.dash_amt -= 1
                self.anti_dash_buffer = True
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

    def collision_check(self):
        """Checks for collision using tilemap"""
        entity_rect = self.rect()

        # Handle Vertical Collision First
        backup_velo = self.velocity[1]
        entity_rect.y += self.velocity[1] # Predict vertical movement
        for rect in self.tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if self.velocity[1] < 0: # Jumping (upward collision)
                    self.pos[1] = rect.bottom # Snap to bottom of block
                    # Reset vertical velocity and ensure precise positioning
                    self.velocity[1] = 0
                    # Recalculate entity_rect after snapping to prevent drift
                    entity_rect.y = self.pos[1]
                self.stop_dash_momentum["y"] = True

        entity_rect.y -= backup_velo

        # Handle Horizontal Collision After
        entity_rect.x += self.velocity[0]  # Predict horizontal movement
        for rect in self.tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if self.velocity[0] > 0:  # Moving right
                    self.pos[0] = rect.left - self.size[0]  # Snap to left side of block
                    self.velocity[0] = 0  # Stop movement
                elif self.velocity[0] < 0:  # Moving left
                    self.pos[0] = rect.right  # Snap to right side of block
                    self.velocity[0] = 0  # Stop movement
                    entity_rect.x = self.pos[0]
                self.stop_dash_momentum["x"] = True


    def apply_momentum(self):
        """Applies velocity to the coords of the object. Slows down movement depending on environment"""
        self.pos[0] += self.velocity[0]
        self.pos[1] += self.velocity[1]

        if self.is_on_floor():
            self.velocity[0] *= 0.2
        elif self.get_direction("x") == 0:
            self.velocity[0] *= 0.8

        return (-self.pos[0], self.pos[1])

    def get_direction(self, axis):
        """Gets the current direction the player is holding towards. Takes an axis as argument ('x' or 'y')"""
        if axis == "x":
            return self.dict_kb["key_right"] - self.dict_kb["key_left"]
        elif axis == "y":
            return self.dict_kb["key_up"] - self.dict_kb["key_down"]
        else:
            print("Error: get_direction() received an invalid axis")
            return 0

    def rect(self):
        return pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])

    def render(self, surf, offset = (0, 0)):
        surf.blit(self.game.assets['player'], (self.pos[0] - offset[0], self.pos[1] - offset[1]))
