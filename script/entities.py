import pygame

class PhysicsEntity:
    def __init__(self,game, e_type, pos, size):
        self.game = game
        self.type = e_type
        self.pos = list(pos)
        self.size = size

    def update_coords(self, new_coords):
        self.pos[0] = new_coords[0]
        self.pos[1] = new_coords[1]

    def render(self, surf):
        surf.blit(self.game.assets['player'], self.pos)
