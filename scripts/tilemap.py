import pygame

from scripts.utils import round_up

PHYSICS_TILES = {'grass', 'stone'}

class Tilemap:
    def __init__(self, game, tile_size = 16):
        self.game = game
        self.tile_size = tile_size
        self.tilemap = {}
        self.offgrid_tiles = []
        self.show_collisions = False

        for i in range(20):
            self.tilemap[str(3 + i) + ';10'] = {'type': 'grass', 'variant': 1, 'pos': (3 + i, 10)}
            self.tilemap[str(5 + i) + ';6'] = {'type': 'grass', 'variant': 1, 'pos': (5 + i, 6)}
            self.tilemap['10;' + str(i + 5)] = {'type': 'stone', 'variant': 1, 'pos': (10, 5 + i)}

    def neighbor_offset(self):
        offset = []
        tiles_x = round_up(self.game.player.size[0]/self.tile_size)
        tiles_y = round_up(self.game.player.size[1]/self.tile_size)
        for x in range(0, tiles_x + 1):
            for y in range(0, tiles_y + 1):
                offset.append((x, y))
        return offset

    def under_offset(self, n_offset):
        u_offset = []
        tiles_x = round_up(self.game.player.size[0] / self.tile_size)
        tiles_y = round_up(self.game.player.size[1] / self.tile_size)
        for offset in n_offset:
            if offset[1] > tiles_y - 1  and offset[0] in range(0, tiles_x):
                u_offset.append(offset)
        return u_offset

    def tiles_around(self, pos):
        tiles = []
        tile_loc = (int(pos[0] // self.tile_size), int(pos[1] // self.tile_size))
        for offset in self.neighbor_offset():
            check_loc = str(tile_loc[0] + offset[0]) + ';' + str(tile_loc[1] + offset[1])
            if self.show_collisions:
                pygame.draw.rect(self.game.display, (255, 0, 255),
                                 ((tile_loc[0] + offset[0]) * self.tile_size - int(self.game.scroll[0]),
                                  (tile_loc[1] + offset[1]) * self.tile_size - int(self.game.scroll[1]),
                                  16,
                                  16))
            if check_loc in self.tilemap:
                tiles.append(self.tilemap[check_loc])
        return tiles

    def tiles_under(self, pos):
        u_tiles = []
        u_tile_loc = (int(pos[0] // self.tile_size), int(pos[1] // self.tile_size))
        for offset in self.under_offset(self.neighbor_offset()):
            check_loc = str(u_tile_loc[0] + offset[0]) + ';' + str(u_tile_loc[1] + offset[1])
            if self.show_collisions:
                pygame.draw.rect(self.game.display, (0, 0, 255),
                                 ((u_tile_loc[0] + offset[0]) * self.tile_size - int(self.game.scroll[0]),
                                  (u_tile_loc[1] + offset[1]) * self.tile_size - int(self.game.scroll[1]),
                                  16,
                                  16))
            if check_loc in self.tilemap:
                u_tiles.append(self.tilemap[check_loc])
        return u_tiles

    def physics_rects_around(self, pos):
        rects = []
        for tile in self.tiles_around(pos):
            if tile['type'] in PHYSICS_TILES:
                rects.append(pygame.Rect(tile['pos'][0] * self.tile_size, tile['pos'][1] * self.tile_size, self.tile_size, self.tile_size))
        return rects

    def physics_rects_under(self, pos):
        u_rects = []
        for tile in self.tiles_under(pos):
            if tile['type'] in PHYSICS_TILES:
                u_rects.append(pygame.Rect(tile['pos'][0] * self.tile_size, tile['pos'][1] * self.tile_size, self.tile_size, self.tile_size))
        return u_rects

    def render(self, surf, offset = (0, 0)):
        for tile in self.offgrid_tiles:
            surf.blit(self.game.assets[tile['type']][tile['variant']], (tile['pos'][0] - offset[0], tile['pos'][1] - offset[1] ))

        for loc in self.tilemap:
            tile = self.tilemap[loc]
            surf.blit(self.game.assets[tile['type']][tile['variant']], (tile['pos'][0] * self.tile_size - offset[0], tile['pos'][1] * self.tile_size - offset[1]))