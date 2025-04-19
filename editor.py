import sys

import pygame

import json

from scripts.utils import load_images, load_image
from scripts.tilemap import Tilemap

RENDER_SCALE = 2.0

class Editor:
    def __init__(self):
        pygame.init()

        pygame.display.set_caption("Editor")
        self.screen = pygame.display.set_mode((960, 576), pygame.RESIZABLE)
        self.display = pygame.Surface((480, 288))

        self.clock = pygame.time.Clock()

        self.tile_size = 16

        self.assets = {
            'decor': load_images('tiles/decor', self.tile_size),
            'grass': load_images('tiles/grass', self.tile_size),
            'vine': load_images('tiles/vine', self.tile_size),
            'vine_transp': load_images('tiles/vine_transp', self.tile_size),
            'vine_transp_back': load_images('tiles/vine_transp_back', self.tile_size),
            'mossy_stone': load_images('tiles/mossy_stone', self.tile_size),
            'mossy_stone_decor': load_images('tiles/mossy_stone_decor', self.tile_size),
            'dark_vine': load_images('tiles/dark_vine'),
            'hanging_vine': load_images('tiles/hanging_vine'),
            'vine_decor': load_images('tiles/vine_decor'),
            'large_decor': load_images('tiles/large_decor'),
            'stone': load_images('tiles/stone', self.tile_size),
            'gray_mossy_stone': load_images('tiles/gray_mossy_stone', self.tile_size),
            'spawners': load_images('tiles/spawners'),
            'transitions': load_images('tiles/transitions'),
            'lever': load_images('tiles/lever'),
            'vines_door_h/closed': load_images('doors/vines_door_h/closed'),
        }

        self.movement = [False, False, False, False]

        self.tilemap = Tilemap(self, self.tile_size)

        self.level = 0

        try:
            self.tilemap.load('data/maps/'+str(self.level)+'.json')
        except FileNotFoundError:
            pass

        self.scroll = [0, 0]

        self.tile_list = list(self.assets)
        self.tile_group = 0
        self.tile_variant = 0
        self.free_lever_id = 0

        self.clicking = False
        self.right_clicking = False
        self.shift = False
        self.ongrid = True

    def run(self):
        while True:
            self.display.fill((0, 0, 0))

            self.scroll[0] += (self.movement[1] - self.movement[0]) * 8
            self.scroll[1] += (self.movement[3] - self.movement[2]) * 8
            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))


            self.tilemap.render(self.display, offset=render_scroll)
            self.tilemap.render_over(self.display, offset=render_scroll)

            current_tile_img = self.assets[self.tile_list[self.tile_group]][self.tile_variant].copy()
            current_tile_img.set_alpha(100)

            mpos = pygame.mouse.get_pos()
            mpos = ((mpos[0] / RENDER_SCALE)*(960/self.screen.get_size()[0]), (mpos[1] / RENDER_SCALE)*(576/self.screen.get_size()[1]))
            tile_pos = (int((mpos[0] + self.scroll[0]) // self.tilemap.tile_size),
                        int((mpos[1] +  self.scroll[1]) // self.tilemap.tile_size))

            if self.ongrid:
                self.display.blit(current_tile_img, (tile_pos[0] * self.tilemap.tile_size - self.scroll[0],
                                                     tile_pos[1] * self.tilemap.tile_size - self.scroll[1]))
            else:
                self.display.blit(current_tile_img, mpos)

            if self.clicking and self.ongrid:
                if self.tile_list[self.tile_group] != "lever":
                    self.tilemap.tilemap[str(tile_pos[0]) + ";" + str(tile_pos[1])] = {'type': self.tile_list[self.tile_group],
                                                                                   'variant': self.tile_variant,
                                                                                   'pos': tile_pos}
                else:
                    self.tilemap.tilemap[str(tile_pos[0]) + ";" + str(tile_pos[1])] = {
                        'type': self.tile_list[self.tile_group],
                        'variant': self.tile_variant,
                        'pos': tile_pos,
                        'id': self.free_lever_id}

            if self.right_clicking:
                tile_loc = str(tile_pos[0]) + ";" + str(tile_pos[1])
                if tile_loc in self.tilemap.tilemap:
                    del self.tilemap.tilemap[tile_loc]
                for tile in self.tilemap.offgrid_tiles.copy():
                    tile_img = self.assets[tile['type']][tile['variant']]
                    tile_r = pygame.Rect(tile['pos'][0] - self.scroll[0],
                                         tile['pos'][1] - self.scroll[1],
                                         tile_img.get_width(),
                                         tile_img.get_height())
                    if tile_r.collidepoint(mpos):
                        self.tilemap.offgrid_tiles.remove(tile)

            for lever in self.tilemap.extract([("lever", 0), ("lever",1)], keep=True):
                if not self.clicking or (tile_pos != (lever["pos"][0]//self.tilemap.tile_size,
                                                     lever["pos"][1]//self.tilemap.tile_size)):
                    self.free_lever_id = lever["id"]+1

            self.display.blit(current_tile_img, (5, 5))

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self.clicking = True
                        if not self.ongrid:
                            self.tilemap.offgrid_tiles.append({'type': self.tile_list[self.tile_group],
                                                               'variant': self.tile_variant,
                                                               'pos': (mpos[0] + self.scroll[0], mpos[1] + self.scroll[1])})
                    if event.button == 3:
                        self.right_clicking = True
                    if self.shift:
                        if event.button == 4:
                            self.tile_variant = (self.tile_variant - 1) % len(self.assets[self.tile_list[self.tile_group]])
                        if event.button == 5:
                            self.tile_variant = (self.tile_variant + 1) % len(self.assets[self.tile_list[self.tile_group]])
                    else:
                        if event.button == 4:
                            self.tile_group = (self.tile_group - 1) % len(self.tile_list)
                            self.tile_variant = 0
                        if event.button == 5:
                            self.tile_group = (self.tile_group + 1) % len(self.tile_list)
                            self.tile_variant = 0
                if event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        self.clicking = False
                    if event.button == 3:
                        self.right_clicking = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        self.movement[0] = True
                    if event.key == pygame.K_RIGHT:
                        if self.tilemap.tilemap != {}:
                            self.tilemap.save('data/maps/' + str(self.level) + '.json')
                            self.level += 1
                            try:
                                self.tilemap.load('data/maps/' + str(self.level) + '.json')
                                self.scroll = [0, 0]
                            except FileNotFoundError:
                                f = open('data/maps/' + str(self.level) + '.json', 'w')
                                json.dump({'tilemap': {},
                                           'tilesize': 16,
                                           'offgrid': []}, f)
                                f.close()
                                self.tilemap.load('data/maps/' + str(self.level) + '.json')
                                self.scroll = [0, 0]
                            else:
                                pass
                    if event.key == pygame.K_LEFT:
                        if self.level > 0:
                            self.tilemap.save('data/maps/' + str(self.level) + '.json')
                            self.level -= 1
                            try:
                                self.tilemap.load('data/maps/' + str(self.level) + '.json')
                                self.scroll = [0, 0]
                            except FileNotFoundError:
                                pass

                    if event.key == pygame.K_d:
                        self.movement[1] = True
                    if event.key == pygame.K_z:
                        self.movement[2] = True
                    if event.key == pygame.K_s:
                        self.movement[3] = True
                    if event.key == pygame.K_g:
                        self.ongrid = not self.ongrid
                    if event.key == pygame.K_t:
                        self.tilemap.autotile()
                    if event.key == pygame.K_LSHIFT:
                        self.shift = True
                    if event.key == pygame.K_o:
                        self.tilemap.save('data/maps/' + str(self.level) + '.json')
                        print("saved")
                    if event.key == pygame.K_c:
                        print((tile_pos[0]*16,tile_pos[1]*16))
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_q:
                        self.movement[0] = False
                    if event.key == pygame.K_d:
                        self.movement[1] = False
                    if event.key == pygame.K_z:
                        self.movement[2] = False
                    if event.key == pygame.K_s:
                        self.movement[3] = False
                    if event.key == pygame.K_LSHIFT:
                        self.shift = False
                elif event.type == pygame.VIDEORESIZE:
                    self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)

            self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), (0, 0))
            pygame.display.update()
            self.clock.tick(60)

Editor().run()