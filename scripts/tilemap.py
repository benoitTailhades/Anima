import pygame

import json

from scripts.utils import round_up

AUTOTILE_MAP = {
    tuple(sorted([(1, 0), (0, 1)])): 0,
    tuple(sorted([(1, 0), (0, 1), (-1, 0)])): 1,
    tuple(sorted([(-1, 0), (0, 1)])): 2,
    tuple(sorted([(-1, 0), (0, -1), (0, 1)])): 3,
    tuple(sorted([(-1, 0), (0, -1)])): 4,
    tuple(sorted([(-1, 0), (0, -1), (1, 0)])): 5,
    tuple(sorted([(1, 0), (0, -1)])): 6,
    tuple(sorted([(1, 0), (0, -1), (0, 1)])): 7,
    tuple(sorted([(1, 0), (-1, 0), (0, 1), (0, -1)])): 8,

}

PHYSICS_TILES = {'grass','stone', 'vine','mossy_stone'}
TRANSPARENT_TILES = {'vine_transp':[0,1,2], 'vine_transp_back':[0,1,2]}
AUTOTILE_TYPES = {'grass', 'stone', 'mossy_stone'}

class Tilemap:
    def __init__(self, game, tile_size = 16):
        self.game = game
        self.tile_size = tile_size
        self.tilemap = {}
        self.offgrid_tiles = []
        self.show_collisions = False

    def extract(self, id_pairs, keep=False):
        matches = []
        for tile in self.offgrid_tiles.copy():
            if (tile['type'], tile['variant']) in id_pairs:
                matches.append(tile.copy())
                if not keep:
                    self.offgrid_tiles.remove(tile)
        for loc in self.tilemap:
            tile = self.tilemap[loc]
            if (tile['type'], tile['variant']) in id_pairs:
                matches.append(tile.copy())
                matches[-1]['pos'] = matches[-1]['pos'].copy()
                matches[-1]['pos'][0] *= self.tile_size
                matches[-1]['pos'][1] *= self.tile_size
                if not keep:
                    del self.tilemap[loc]
        return matches

    def neighbor_offset(self):
        offset = []
        tiles_x = round_up(self.game.player.size[0]/self.tile_size)
        tiles_y = round_up(self.game.player.size[1]/self.tile_size)
        for x in range(0, tiles_x + 1):
            for y in range(0, tiles_y):
                offset.append((x, y))
        return offset

    def under_offset(self, n_offset):
        u_offset = []
        tiles_x = round_up(self.game.player.size[0] / self.tile_size)
        tiles_y = round_up(self.game.player.size[1] / self.tile_size)
        for x in range(0, tiles_x + 1):
            for y in range(tiles_y, tiles_y+1):
                u_offset.append((x, y))
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

    def save(self, path):
        f = open(path, 'w')
        json.dump({'tilemap': self.tilemap,
                   'tilesize': self.tile_size,
                   'offgrid': self.offgrid_tiles}, f)
        f.close()

    def load(self, path):
        f = open(path, 'r')
        map_data = json.load(f)
        f.close()

        self.tilemap = map_data['tilemap']
        self.tile_size = map_data['tilesize']
        self.offgrid_tiles = map_data['offgrid']

    def autotile(self):
        for loc in self.tilemap:
            tile = self.tilemap[loc]
            neighbors = set()
            for shift in [(1, 0), (-1, 0), (0, -1), (0, 1)]:
                check_loc = str(tile['pos'][0] + shift[0]) + ";" + str(tile['pos'][1] + shift[1])
                if check_loc in self.tilemap:
                    if self.tilemap[check_loc]['type'] == tile['type']:
                        neighbors.add(shift)
            neighbors = tuple(sorted(neighbors))
            if (tile['type'] in AUTOTILE_TYPES) and (neighbors in AUTOTILE_MAP):
                tile['variant'] = AUTOTILE_MAP[neighbors]

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
            elif tile['type'] in set(TRANSPARENT_TILES.keys()) and tile['variant'] in TRANSPARENT_TILES[tile['type']]:
                u_rects.append(pygame.Rect(tile['pos'][0] * self.tile_size, tile['pos'][1] * self.tile_size, self.tile_size,self.tile_size))
        return u_rects

    def get_type_from_rect(self, rect):
        for tile in self.tilemap:
            if str(rect.x//self.tile_size) + ";" + str(rect.y//self.tile_size) == tile:
                return self.tilemap[tile]["type"]
    def get_variant_from_rect(self, rect):
        for tile in self.tilemap:
            if str(rect.x//self.tile_size) + ";" + str(rect.y//self.tile_size) == tile:
                return self.tilemap[tile]["variant"]

    def render(self, surf, offset = (0, 0)):
        for tile in self.offgrid_tiles:
            surf.blit(self.game.assets[tile['type']][tile['variant']], (tile['pos'][0] - offset[0], tile['pos'][1] - offset[1] ))

        for x in range(offset[0]// self.tile_size, (offset[0] + surf.get_width()) // self.tile_size + 1):
            for y in range(offset[1] // self.tile_size, (offset[1] + surf.get_height()) // self.tile_size + 1):
                loc = str(x) + ";" + str(y)
                if loc in self.tilemap:
                    tile = self.tilemap[loc]
                    surf.blit(self.game.assets[tile['type']][tile['variant']], (
                    tile['pos'][0] * self.tile_size - offset[0], tile['pos'][1] * self.tile_size - offset[1]))