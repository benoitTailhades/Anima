import random

class Background:

    def __init__(self, pos, img, speed, depth, game):
        self.pos = list(pos)
        self.img = img
        self.speed = speed
        self.depth = depth
        self.game = game
        self.player = game.player

    def render(self, surf, offset=(0, 0)):
        render_pos = (self.pos[0] - offset[0] * self.depth,
                      self.pos[1] - offset[1] * self.depth )
        surf.blit(self.img, (render_pos[0] % (surf.get_width() + self.img.get_width()) - self.img.get_width(),
                             render_pos[1] % (surf.get_height() + self.img.get_hight()) - self.img.get_height()))