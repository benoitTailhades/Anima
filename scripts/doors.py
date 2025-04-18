import time

import pygame

class Door:
    def __init__(self, size, pos, d_type, flip, opening_speed, game):
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

    def update(self):
        if self.action == "opening" and not self.opened:
            print(self.action)
            if time.time() - self.last_time_interacted >= self.opening_speed:
                self.set_action("opened")
                self.opened = True
                print(self.action)

        if self.action == "closing":
            self.opened = False
            if time.time() - self.last_time_interacted >= self.opening_speed:
                self.set_action("closed")

    def open(self):
        self.set_action("opening")
        self.last_time_interacted = time.time()

    def close(self):
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