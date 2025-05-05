import time

import pygame
import random

from scripts.particle import Particle
from scripts.spark import Spark
from pygame.sprite import collide_rect
from scripts.sound import *


class Door:
    def __init__(self, size, pos, d_type, d_id, flip, opening_speed, game):
        self.size = size
        self.pos = pos
        self.type = d_type
        self.opened = False
        self.action = "closed"
        self.game = game
        self.animation = self.game.assets[self.type + '/' + self.action].copy()
        self.flip = flip
        self.opening_speed = opening_speed
        self.last_time_interacted = 0
        self.id = d_id

        self.breaking_sound = pygame.mixer.Sound('assets/sounds/door_breaking.wav')

    def update(self):
        self.animation.update()

        if self.type == 'breakable_stalactite' and self.game.attacking and self.rect().colliderect(
                self.game.player.rect().inflate(32, 32)):
            pos = (self.rect().x + random.random() * self.rect().width,
                   self.rect().y + 5 + random.random() * self.rect().height)
            self.game.particles.append(
                Particle(self.game, 'crystal_fragment', pos, velocity=[-0.1, 1.2], frame=0))
            self.open()

        if self.action == "opening" and not self.opened:
            if time.time() - self.last_time_interacted >= self.opening_speed:
                self.set_action("opened")
                self.opened = True

        if self.action == "closing":
            self.opened = False
            if time.time() - self.last_time_interacted >= self.opening_speed:
                self.set_action("closed")

        if not self.opened and self.action == "opened":
            self.set_action("closed")
        elif self.opened and self.action != "opened":
            self.set_action("opened")

    def open(self):
        if not self.opened:
            self.set_action("opening")
            self.last_time_interacted = time.time()

            if self.type == 'breakable_stalactite':
                self.breaking_sound.play()

    def close(self):
        if self.opened:
            self.set_action("closing")
            self.last_time_interacted = time.time()

    def rect(self):
        if self.action == "opened":
            return pygame.Rect(self.pos[0], self.pos[1], 0, 0)
        else:
            return pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])

    def set_action(self, action):
        if action != self.action:
            self.action = action
            self.animation = self.game.assets[self.type + '/' + self.action].copy()

    def render(self, surf, offset=(0, 0)):
        surf.blit(pygame.transform.flip(self.animation.img(), self.flip, False),
                  (self.pos[0] - offset[0], self.pos[1] - offset[1]))