#Heavily upgraded basic godot physics code that i then converted to Python --Aymeric
import pygame as pg

import sys

import pygame

from script.tilemap import Tilemap

class PhysicsPlayer:
    # Overall physics and movement handler
    def __init__(self, game, pos, size):
        self.game = game
        self.pos = list(pos)  # [x, y]
        self.size = size
        self.velocity = [0, 0]  # [vel_x, vel_y]

        self.SPEED = 2.5
        self.DASH_SPEED = 6
        self.JUMP_VELOCITY = -6.0
        self.DASHTIME = 12
        self.JUMPTIME = 10

        self.dashtime_cur = 0  # Immune to gravity during dashtime
        self.dash_amt = 1
        self.jumptime_cur = 0

        self.direction = 0
        self.last_direction = 1

        self.dash_direction = [0, 0]  # [dash_x, dash_y]
        self.tech_momentum_mult = 0
        self.dict_kb = {"key_right": 0, "key_left": 0, "key_up": 0, "key_down": 0, "key_jump": 0, "key_dash": 0}
        self.anti_dash_buffer = False

    def physics_process(self, framerate, tilemap, dict_kb, stage):
        self.dict_kb = dict_kb
        self.stage = stage

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
        self.collision_check(tilemap)

        return self.apply_momentum()

    def gravity(self):
        if not self.is_on_floor() and not self.dashtime_cur > 0:
            self.velocity[1] = min(5, self.velocity[1] + 0.5)
        elif self.is_on_floor():
            if self.is_on_floor(self.pos[1] - 1):
                self.pos[1] -= 1
            if self.velocity[1] > 0:
                self.velocity[1] = 0
            if self.dashtime_cur < 10 and self.dash_amt == 0:
                self.dash_amt = 1

    def jump(self):
        if self.dict_kb["key_jump"] == 1 and self.is_on_floor():
            self.velocity[1] = self.JUMP_VELOCITY

            if self.dashtime_cur != 0:
                self.dashtime_cur = 0
                self.tech_momentum_mult = pow(abs(self.dash_direction[0]) + abs(self.dash_direction[1]), 0.5)
                self.velocity[0] = self.get_direction("x") * self.DASH_SPEED * self.tech_momentum_mult
                self.velocity[1] /= self.tech_momentum_mult

    def dash(self):
        if not self.anti_dash_buffer:
            if self.dict_kb["key_dash"] == 1:
                if self.dash_amt > 0:
                    self.dash_direction = [self.get_direction("x"), self.get_direction("y")]
                    if self.dash_direction == [0, 0]:
                        self.dash_direction[0] = self.last_direction
                    self.dashtime_cur = self.DASHTIME
                    self.dash_amt -= 1
                self.anti_dash_buffer = True
        else:
            if self.dict_kb["key_dash"] == 0:
                self.anti_dash_buffer = False

    def dash_momentum(self):
        if self.dashtime_cur > 0:
            self.dashtime_cur -= 1
            self.velocity[0] = self.dash_direction[0] * self.DASH_SPEED
            self.velocity[1] = -self.dash_direction[1] * self.DASH_SPEED
            if self.is_on_floor(self.pos[1] + self.velocity[1]):
                self.velocity[1] = 0
            if self.dashtime_cur == 0:
                self.velocity = [0, 0]

    def apply_momentum(self):
        self.pos[0] += self.velocity[0]
        self.pos[1] += self.velocity[1]

        if self.is_on_floor():
            self.velocity[0] *= 0.2
        elif self.get_direction("x") == 0:
            self.velocity[0] *= 0.8

        return (-self.pos[0], self.pos[1])

    def is_on_floor(self, cur_y="undef"):
        if cur_y == "undef":
            cur_y = self.pos[1]
        return cur_y > 50  # TODO: Replace with proper collision detection

    def get_direction(self, axis):
        if axis == "x":
            return self.dict_kb["key_right"] - self.dict_kb["key_right"]
        elif axis == "y":
            return self.dict_kb["key_up"] - self.dict_kb["key_down"]
        else:
            print("Error: get_direction() received an invalid axis")
            return 0

    def rect(self):
        return pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])

    def collision_check(self, tilemap):
        for rect in tilemap.physics_rects_around(self.pos):
            if self.rect().colliderect(rect):
                return True

    def render(self, surf):
        surf.blit(self.game.assets['player'], self.pos)


