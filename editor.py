import sys

import pygame

import json

from scripts.utils import load_images, load_tiles, load_doors, load_activators
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

        self.base_assets = {
            'lever': load_images('spawners'),
            'spawners': load_images('spawners'),
            'transition': load_images('transition'),
            'throwable':load_images('entities/elements/blue_rock/intact'),
            'teleporter':load_images('teleporters/blue_cave'),
            'progressive_teleporter': load_images('teleporters/blue_cave')
        }

        self.environments = {"green_cave": (0, 1, 2),
                             "blue_cave": (3, 4)}

        self.level = 0

        self.base_assets.update(load_doors('editor', self.get_environment(self.level)))
        self.doors = []
        self.levers = []
        self.buttons = []
        for env in self.environments:
            self.doors += [(door, 0) for door in load_doors('editor', env) if "door" in door]
            self.levers += [(lever, 0) for lever in load_activators(env) if "lever" in lever]
            self.buttons += [(button, 0) for button in load_activators(env) if "button" in button]

        self.assets = self.base_assets | load_tiles(self.get_environment(self.level))
        self.assets.update(load_doors('editor', self.get_environment(self.level)))
        self.assets.update(load_activators(self.get_environment(self.level)))

        self.movement = [False, False, False, False]

        self.tilemap = Tilemap(self, self.tile_size)


        try:
            self.tilemap.load('data/maps/'+str(self.level)+'.json')
        except FileNotFoundError:
            pass

        self.scroll = [0, 0]

        self.tile_list = list(self.assets)
        self.tile_group = 0
        self.tile_variant = 0
        self.levers_ids = set()
        self.doors_ids = set()
        self.buttons_ids = set()
        self.tps_ids = set()


        self.zoom = 1

        self.clicking = False
        self.right_clicking = False
        self.shift = False
        self.ongrid = True

    def get_environment(self, level):
        for environment in self.environments:
            if level in self.environments[environment]:
                return environment

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
            mpos = ((mpos[0] / RENDER_SCALE)*(960/self.screen.get_size()[0])*self.zoom, (mpos[1] / RENDER_SCALE)*(576/self.screen.get_size()[1])*self.zoom)
            tile_pos = (int((mpos[0] + self.scroll[0]) // self.tilemap.tile_size),
                        int((mpos[1] +  self.scroll[1]) // self.tilemap.tile_size))

            for lever in self.tilemap.extract(self.levers, keep=True):
                self.levers_ids.add(lever['id'])

            for door in self.tilemap.extract(self.doors, keep=True):
                self.doors_ids.add(door['id'])

            for tp in self.tilemap.extract([('teleporter', 0), ('progressive_teleporter', 0)], keep=True):
                self.tps_ids.add(tp['id'])
                
            for button in self.tilemap.extract(self.buttons, keep=True):
                self.buttons_ids.add(button['id'])

            if self.ongrid:
                self.display.blit(current_tile_img, (tile_pos[0] * self.tilemap.tile_size - self.scroll[0],
                                                     tile_pos[1] * self.tilemap.tile_size - self.scroll[1]))
            else:
                self.display.blit(current_tile_img, mpos)

            if self.clicking and self.ongrid:
                if self.tile_list[self.tile_group] in (l[0] for l in self.levers):
                    iD = int(input("Enter the lever id: "))
                    while iD in self.levers_ids:
                        print("id already used")
                        iD = int(input("Enter the lever id: "))
                    self.levers_ids.add(iD)
                    self.tilemap.tilemap[str(tile_pos[0]) + ";" + str(tile_pos[1])] = {
                        'type': self.tile_list[self.tile_group],
                        'variant': self.tile_variant,
                        'pos': tile_pos,
                        'id': iD}

                elif self.tile_list[self.tile_group] in (d[0] for d in self.doors):
                    iD = int(input("Enter the door id: "))
                    while iD in self.doors_ids:
                        print("id already used")
                        iD = int(input("Enter the door id: "))
                    self.doors_ids.add(iD)
                    self.tilemap.tilemap[str(tile_pos[0]) + ";" + str(tile_pos[1])] = {
                        'type': self.tile_list[self.tile_group],
                        'variant': self.tile_variant,
                        'pos': tile_pos,
                        'id': iD}
                    
                elif self.tile_list[self.tile_group] in (b[0] for b in self.buttons):
                    iD = int(input("Enter the button id: "))
                    while iD in self.buttons_ids:
                        print("id already used")
                        iD = int(input("Enter the button id: "))
                    self.buttons_ids.add(iD)
                    self.tilemap.tilemap[str(tile_pos[0]) + ";" + str(tile_pos[1])] = {
                        'type': self.tile_list[self.tile_group],
                        'variant': self.tile_variant,
                        'pos': tile_pos,
                        'id': iD}

                elif self.tile_list[self.tile_group] in ["teleporter", "progressive_teleporter"]:
                    iD = int(input("Enter the tp id: "))
                    while iD in self.tps_ids:
                        print("id already used")
                        iD = int(input("Enter the tp id: "))
                    self.tps_ids.add(iD)
                    self.tilemap.tilemap[str(tile_pos[0]) + ";" + str(tile_pos[1])] = {
                        'type': self.tile_list[self.tile_group],
                        'variant': self.tile_variant,
                        'pos': tile_pos,
                        'id': iD}

                elif self.tile_list[self.tile_group] == "transition":
                    direction = int(input("Enter the destination level: "))
                    self.tilemap.tilemap[str(tile_pos[0]) + ";" + str(tile_pos[1])] = {
                        'type': self.tile_list[self.tile_group],
                        'variant': self.tile_variant,
                        'pos': tile_pos,
                        'destination': direction}

                else:
                    self.tilemap.tilemap[str(tile_pos[0]) + ";" + str(tile_pos[1])] = {
                        'type': self.tile_list[self.tile_group],
                        'variant': self.tile_variant,
                        'pos': tile_pos}

            if self.right_clicking:
                tile_loc = str(tile_pos[0]) + ";" + str(tile_pos[1])
                if tile_loc in self.tilemap.tilemap:
                    if self.tilemap.tilemap[tile_loc]['type'] in (l[0] for l in self.levers):
                        self.levers_ids.remove(self.tilemap.tilemap[tile_loc]["id"])
                    if self.tilemap.tilemap[tile_loc]['type'] in (d[0] for d in self.doors):
                        self.doors_ids.remove(self.tilemap.tilemap[tile_loc]["id"])
                    if self.tilemap.tilemap[tile_loc]['type'] in ["teleporter", "progressive_teleporter"]:
                        self.tps_ids.remove(self.tilemap.tilemap[tile_loc]["id"])
                    if self.tilemap.tilemap[tile_loc]['type'] in (b[0] for b in self.buttons):
                        self.buttons_ids.remove(self.tilemap.tilemap[tile_loc]["id"])
                    del self.tilemap.tilemap[tile_loc]
                for tile in self.tilemap.offgrid_tiles.copy():
                    tile_img = self.assets[tile['type']][tile['variant']]
                    tile_r = pygame.Rect(tile['pos'][0] - self.scroll[0],
                                         tile['pos'][1] - self.scroll[1],
                                         tile_img.get_width(),
                                         tile_img.get_height())
                    if tile_r.collidepoint(mpos):
                        self.tilemap.offgrid_tiles.remove(tile)

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
                            self.assets = self.base_assets | load_tiles(self.get_environment(self.level))
                            self.assets.update(load_doors('editor', self.get_environment(self.level)))
                            self.assets.update(load_activators(self.get_environment(self.level)))
                            self.tile_list = list(self.assets)
                            self.levers_ids = set()
                            self.doors_ids = set()
                            self.buttons_ids = set()
                            self.tps_ids = set()
                            self.tile_group = 0
                            self.tile_variant = 0
                    if event.key == pygame.K_LEFT:
                        if self.level > 0:
                            self.tilemap.save('data/maps/' + str(self.level) + '.json')
                            self.level -= 1
                            try:
                                self.tilemap.load('data/maps/' + str(self.level) + '.json')
                                self.scroll = [0, 0]
                            except FileNotFoundError:
                                pass
                            self.assets = self.base_assets | load_tiles(self.get_environment(self.level))
                            self.assets.update(load_doors('editor', self.get_environment(self.level)))
                            self.assets.update(load_activators(self.get_environment(self.level)))
                            self.tile_list = list(self.assets)
                            self.levers_ids = set()
                            self.doors_ids = set()
                            self.buttons_ids = set()
                            self.tps_ids = set()
                            self.tile_group = 0
                            self.tile_variant = 0
                    if event.key == pygame.K_DOWN:
                        self.zoom = self.zoom*2
                        self.display = pygame.Surface((480*self.zoom, 288*self.zoom))
                    if event.key == pygame.K_UP:
                        self.zoom = self.zoom/2
                        self.display = pygame.Surface((480*self.zoom, 288*self.zoom))

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