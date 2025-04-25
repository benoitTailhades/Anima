import pygame
import time


class Lever:
    def __init__(self, game, pos, size=(16, 16), i=0):
        self.game = game
        self.pos = pos
        self.rect = pygame.Rect(pos[0], pos[1], size[0], size[1])
        self.state = 0
        self.last_interaction_time = 0
        self.interaction_cooldown = 0.5
        self.id = i

    def toggle(self):
        current_time = time.time()
        if current_time - self.last_interaction_time >= self.interaction_cooldown:
            self.state = int(not self.state)
            self.last_interaction_time = current_time

            return True
        return False

    def can_interact(self, player_rect, interaction_distance=2):
        can_interact = self.rect.colliderect(player_rect.inflate(interaction_distance, interaction_distance))
        return can_interact

    def render(self, surface, offset=(0, 0)):
        surface.blit(self.game.assets[self.game.get_environment(self.game.level) + '_lever'][self.state], (self.pos[0] - offset[0], self.pos[1] - offset[1]))


class Teleporter:
    def __init__(self, game, pos, size, t_id):
        self.game = game
        self.pos = list(pos)
        self.size = size
        self.id = t_id

    def rect(self):
        return pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])

    def can_interact(self, player_rect, interaction_distance=2):
        can_interact = self.rect().colliderect(player_rect.inflate(interaction_distance, interaction_distance))
        return can_interact