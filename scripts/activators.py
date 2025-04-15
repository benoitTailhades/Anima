import pygame
import time


class Lever:
    def __init__(self, game, pos, size=(16, 16)):
        self.game = game
        self.pos = pos
        self.rect = pygame.Rect(pos[0], pos[1], size[0], size[1])
        self.state = False
        self.last_interaction_time = 0
        self.interaction_cooldown = 0.5


    def toggle(self):
        current_time = time.time()
        if current_time - self.last_interaction_time >= self.interaction_cooldown:
            self.state = not self.state
            self.last_interaction_time = current_time

            return True
        return False

    def can_interact(self, player_rect, interaction_distance=32):
        can_interact = self.rect.colliderect(player_rect.inflate(interaction_distance, interaction_distance))
        return can_interact

    def render(self, surface, offset=(0, 0)):
        variant = 1 if self.state else 0
        self._last_rendered_variant = variant

        color = (0, 255, 0) if self.state else (255, 0, 0)
        pygame.draw.circle(surface, color,(self.pos[0] - offset[0] + 8, self.pos[1] - offset[1] - 15),4)

        surface.blit(self.game.assets['lever'][variant], (self.pos[0] - offset[0], self.pos[1] - offset[1]))