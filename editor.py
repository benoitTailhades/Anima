import sys

import pygame

import json

from scripts.utils import load_images, load_tiles, load_doors, load_activators
from scripts.tilemap import Tilemap
from scripts.button import Button
from scripts.activators import load_activators_actions

RENDER_SCALE = 2.0
SIDEBAR_WIDTH = 200
UNDERBAR_HEIGHT = 200


class Editor:
    def __init__(self):
        pygame.init()

        pygame.display.set_caption("Editor")
        self.screen_width = 960 + SIDEBAR_WIDTH
        self.screen_height = 576
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)
        self.display = pygame.Surface((480, 288))

        self.clock = pygame.time.Clock()

        self.tile_size = 16

        self.base_assets = {
            'spawners': load_images('spawners'),
            'transition': load_images('transition'),
            'throwable': load_images('entities/elements/blue_rock/intact'),
        }

        self.environments = {"green_cave": (0, 1, 2),
                             "blue_cave": (3, 4)}

        self.level = 0

        self.base_assets.update(load_doors('editor', self.get_environment(self.level)))
        self.doors = []
        self.levers = []
        self.buttons = []
        self.teleporters = []
        self.categories = {}
        self.activators = {}
        self.activators_types = {}
        for env in self.environments:
            self.doors += [(door, 0) for door in load_doors('editor', env) if "door" in door]
            self.levers += [(lever, 0) for lever in load_activators(env) if "lever" in lever]
            self.buttons += [(button, 0) for button in load_activators(env) if "button" in button]
            self.teleporters += [(tp, 0) for tp in load_activators(env) if "teleporter" in tp]

        self.assets = self.base_assets | load_tiles(self.get_environment(self.level))
        self.assets.update(load_doors('editor', self.get_environment(self.level)))
        self.assets.update(load_activators(self.get_environment(self.level)))
        self.get_categories()
        self.category_changed = False
        self.activators_categories_shown = False
        self.current_activator_category = "All"
        self.selected_activator = None
        self.selected_activator_type = None
        self.edited_info = None
        self.edited_value = None

        self.infos_per_type_per_category = {"Levers": {"visual_and_door":
                                                         {"visual_duration" : int,
                                                          "door_id": int},
                                                       "test":
                                                            {"info 1": int,
                                                             "info 2": str}
                                                       },
                                   "Teleporters": {"normal_tp":
                                                       {"dest" : str,
                                                        "time":int},
                                                   "progressive_tp":
                                                       {"dest" : str,
                                                        "time":int}
                                                       },
                                   "Buttons": {"improve_tp_progress":
                                                 {"amount" : int,
                                                  "tp_id": int}
                                             }
                                   }
        self.types_per_categories = {t : set(self.infos_per_type_per_category[t].keys()) for t in self.infos_per_type_per_category}
        print(self.types_per_categories)

        self.movement = [False, False, False, False]

        self.tilemap = Tilemap(self, self.tile_size)

        try:
            self.tilemap.load('data/maps/' + str(self.level) + '.json')
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
        self.activators_ids = {"Levers": self.levers_ids,
                               "Buttons": self.buttons_ids,
                               "Teleporters": self.tps_ids}

        self.zoom = 1
        self.edit_properties_mode_on = False
        self.holding_i = False
        self.window_mode = False
        self.showing_properties_window = False
        self.get_activators()

        self.clicking = False
        self.right_clicking = False
        self.shift = False
        self.ongrid = True

        # Font for UI
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)

    def get_environment(self, level):
        for environment in self.environments:
            if level in self.environments[environment]:
                return environment

    def render_sidebar(self):
        #LOGIC
        if self.category_changed and not self.clicking:
            self.category_changed = False
        mpos = (pygame.mouse.get_pos()[0] - (self.screen.get_size()[0] - SIDEBAR_WIDTH), pygame.mouse.get_pos()[1])

        # SIDEBAR
        self.sidebar = pygame.Surface((SIDEBAR_WIDTH, self.screen_height))
        self.sidebar.fill((40, 40, 40))

        # HEAD
        next_category = Button(SIDEBAR_WIDTH - 40, 5, 24, 24, self.clicking)
        previous_category = Button(20, 5, 24, 24, self.clicking)
        if not self.category_changed:
            if next_category.pressed(mpos):
                self.current_category = (self.current_category + 1) % len(self.categories.keys())
                self.category_changed = True
            if previous_category.pressed(mpos):
                self.current_category = (self.current_category - 1) % len(self.categories.keys())
                self.category_changed = True
            self.current_category_name = list(self.categories.keys())[self.current_category]

        category_text = self.font.render(self.current_category_name, True, (255, 255, 255))
        self.sidebar.blit(category_text, ((SIDEBAR_WIDTH - category_text.get_width())/2, 10))

        next_category.draw(self.sidebar, (50, 50, 50), mpos)
        previous_category.draw(self.sidebar, (50, 50, 50), mpos)

        pygame.draw.line(self.sidebar, (0,0,0), (10, 30), (SIDEBAR_WIDTH - 10, 30))

        # ELEMENTS
        pos = [10, 50]
        for element in self.categories[self.current_category_name]:
            category_text = self.small_font.render(element if self.current_category_name != "Entities" else str(self.categories["Entities"].index(element)), True, (255, 255, 255))
            button = Button(pos[0], pos[1] - 5, SIDEBAR_WIDTH - 20, 34, self.clicking)
            button.draw(self.sidebar, (30, 30, 30), mpos)
            self.sidebar.blit(category_text, (pos[0] + 34, pos[1] + 5))
            self.sidebar.blit(pygame.transform.scale(self.assets[element][0] if self.current_category_name != "Entities" else element, (24,24)), pos)
            if button.pressed(mpos):
                if self.current_category_name != "Entities":
                    self.tile_group = self.tile_list.index(element)
                    self.tile_variant = 0
                else:
                    self.tile_group = 0
                    self.tile_variant = self.categories["Entities"].index(element)
            pos[1] += 40

    def move_visual_to(self, pos):
        scale_x = 960 / (self.screen.get_size()[0] - SIDEBAR_WIDTH)
        scale_y = 576 / (self.screen.get_size()[1])
        self.scroll[0] = pos[0]*16 - ((self.screen_width-SIDEBAR_WIDTH)*scale_x)//(2*int(RENDER_SCALE *self.zoom))
        self.scroll[1] = pos[1]*16 - self.screen_height*scale_y//(2*int(RENDER_SCALE *self.zoom))

    def render_underbar(self):
        mpos = (pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1] - (self.screen.get_size()[1] - UNDERBAR_HEIGHT))

        self.underbar = pygame.Surface((self.screen.get_size()[0] - SIDEBAR_WIDTH, UNDERBAR_HEIGHT))
        self.underbar.fill((35, 35, 35))

        category_text = self.font.render(self.current_activator_category, True, (255, 255, 255))
        category_button = Button(20, 10, 100, 20, self.clicking)

        activators = self.activators[self.current_activator_category] if self.current_activator_category != "All" else \
        self.activators["Levers"] | self.activators["Teleporters"] | self.activators["Buttons"]
        r = c = 0
        cell_width = 150
        cell_h_offset = 15
        cell_height = 40
        cell_v_offset = 50

        for activator in activators:
            act_button = Button(cell_h_offset + (cell_width+cell_h_offset)*c, cell_v_offset + (cell_height+10)*r, cell_width, cell_height, self.clicking)
            if self.activators_categories_shown:
                act_button.activated = False
            act_button.draw(self.underbar, (60, 60, 60), mpos)
            info_r = 0
            for info in ["id", "pos"]:
                info_name = self.small_font.render(info+":", True, (255, 255, 255))
                info_value = self.small_font.render(str(activators[activator][info]), True, (255, 255, 255))
                self.underbar.blit(info_name, (20 + (cell_width+cell_h_offset) * c, cell_v_offset+5 + (cell_height+10) * r + 18*info_r))
                self.underbar.blit(info_value, (20 + (cell_width+cell_h_offset) * c + info_name.get_width() + 2, cell_v_offset+5 + (cell_height+10) * r + 18*info_r))
                info_r += 1
            c += 1
            if cell_h_offset + (cell_width+cell_h_offset) * c + cell_width > self.underbar.get_width():
                c = 0
                r += 1
            if act_button.pressed(mpos):
                self.move_visual_to(activators[activator]["pos"])

        category_button.draw(self.underbar, (50, 50, 50), mpos)
        self.underbar.blit(category_text, ((140 - category_text.get_width())/2, 13))

        if self.activators_categories_shown:
            categories = ["All", "Levers", "Teleporters", "Buttons"]
            categories.remove(self.current_activator_category)
            for category in categories:
                c_text = self.font.render(category, True, (255, 255, 255))
                c_button = Button(20, 10 + 20*(categories.index(category)+1), 100, 20, self.clicking)
                c_button.draw(self.underbar, (50, 50, 50), mpos)
                self.underbar.blit(c_text, ((140 - c_text.get_width())/2, 13 + 20*(categories.index(category)+1)))
                if c_button.pressed(mpos):
                    self.current_activator_category = category

        if category_button.pressed(mpos):
            self.activators_categories_shown = True
        elif self.clicking:
            self.activators_categories_shown = False

    def set_window_mode(self):
        if not self.window_mode:
            self.default_bg = self.screen.copy()
            self.window_mode = True

    def update_window_mode_bg(self):
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))

        scaled_bg = pygame.transform.scale(self.default_bg, self.screen.get_size())
        self.screen.blit(scaled_bg, (0, 0))
        self.screen.blit(overlay, (0, 0))

    def render_info_window(self):
        self.properties_window = pygame.Surface((280, 250))
        self.properties_window.fill((35, 35, 35))
        window_pos = ((self.screen_width-self.properties_window.get_width())/2,
                      (self.screen_height-self.properties_window.get_height())/2)
        mpos = (pygame.mouse.get_pos()[0] - window_pos[0], pygame.mouse.get_pos()[1] - window_pos[1])

        cell_h_offset = 20
        cell_v_offset = 70
        row_offset = 30
        info_r = 0
        infos = self.selected_activator["infos"].copy()
        pos_txt = self.font.render("pos" + ":", True, (255, 255, 255))
        pos_val = self.font.render(str(infos["pos"]), True, (255, 255, 255))
        self.properties_window.blit(pos_txt, (self.properties_window.get_width() - pos_val.get_width() - pos_txt.get_width() - 12, 10))
        self.properties_window.blit(pos_val, (self.properties_window.get_width() - pos_val.get_width() - 10, 10))
        del infos["pos"]
        for info in infos:
            info_name = self.font.render(info + ":", True, (255, 255, 255))
            info_value = self.font.render(self.edited_value if self.edited_info == info else
                                          str(self.selected_activator["infos"][info]), True, (255, 255, 255))
            value_rect = Button(cell_h_offset + info_name.get_width() + 2,
                                     cell_v_offset + 5 + row_offset * info_r,
                                      max(info_value.get_width(), 9), info_value.get_height(), self.clicking)
            if value_rect.pressed(mpos) and not self.edited_info:
                self.edited_info = info
                self.edited_value = str(self.selected_activator["infos"][info])
                print('modifing: ' + self.edited_info)
                print('value: ' + self.edited_value)
            if self.edited_info:
                value_rect.activated = False
            value_rect.draw(self.properties_window, (0, 50, 200), mpos)
            self.properties_window.blit(info_name, (
            cell_h_offset , cell_v_offset + 5 + row_offset * info_r))
            self.properties_window.blit(info_value, (cell_h_offset + info_name.get_width() + 2,
                                            cell_v_offset + 5 + row_offset * info_r))
            self.properties_window.blit(pygame.transform.scale(self.selected_activator["image"], (48, 48)), (5, 0))
            info_r += 1

    def save_edited_values(self):
        with open("data/activators.json", "r") as file:
            actions_data = json.load(file)
            activators = {}
            for activator_category in self.activators.copy():
                activators[activator_category.lower()] = {}
                for activator in self.activators[activator_category].copy():
                    infos = self.activators[activator_category][activator].copy()
                    del infos["id"]
                    activators[activator_category.lower()][self.activators[activator_category][activator]["id"]] = infos
            actions_data[str(self.level)] = activators.copy()
        with open("data/activators.json", "w") as f:
            json.dump(actions_data, f, indent=4)

    def get_categories(self):
        self.categories["Blocks"] = [b for b in list(load_tiles(self.get_environment(self.level)).keys()) if "decor" not in b]
        self.categories["Decor"] = [d for d in list(load_tiles(self.get_environment(self.level)).keys()) if "decor" in d]
        self.categories["Doors"] = load_doors('editor', self.get_environment(self.level))
        self.categories["Activators"] = load_activators(self.get_environment(self.level))
        self.categories["Entities"] = self.base_assets["spawners"].copy()
        self.current_category = 0
        self.current_category_name = list(self.categories.keys())[self.current_category]

    def get_activators(self):
        self.activators_types["All"] = set()
        for a in ["Levers", "Teleporters", "Buttons"]:
            self.activators_types[a] = set()
            self.activators[a] = {pos : {"id" : self.tilemap.tilemap[pos]["id"], "pos": self.tilemap.tilemap[pos]["pos"]} for pos in self.tilemap.tilemap if a.lower()[:-1] in self.tilemap.tilemap[pos]["type"]}
            for pos in self.tilemap.tilemap:
                if a.lower()[:-1] in self.tilemap.tilemap[pos]["type"]:
                    self.activators_types[a].add(self.tilemap.tilemap[pos]['type'])
            self.activators_types["All"] = self.activators_types["All"] | self.activators_types[a]
            activators_actions = load_activators_actions()
            for activator in self.activators[a]:
                id_l = self.activators[a][activator]["id"]
                #Systeme de ajout d'un nouveau activator
                for info in activators_actions[str(self.level)][a.lower()][str(id_l)]:
                    self.activators[a][activator][info] = activators_actions[str(self.level)][a.lower()][str(id_l)].copy()[info]

    def run(self):
        while True:
            self.display.fill((0, 0, 0))


            self.scroll[0] += (self.movement[1] - self.movement[0]) * 8
            self.scroll[1] += (self.movement[3] - self.movement[2]) * 8
            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))

            self.tilemap.render(self.display, offset=render_scroll, mask_opacity=80 if self.edit_properties_mode_on else 255, exception=self.activators_types[self.current_activator_category])
            self.tilemap.render_over(self.display, offset=render_scroll, mask_opacity=80 if self.edit_properties_mode_on else 255, exception=self.activators_types[self.current_activator_category])

            current_tile_img = self.assets[self.tile_list[self.tile_group]][self.tile_variant].copy()
            current_tile_img.set_alpha(100)

            # Calculate mouse position (only for main display area)
            mpos = pygame.mouse.get_pos()
            main_area_width = self.screen_width - SIDEBAR_WIDTH
            main_area_height = self.screen_height - UNDERBAR_HEIGHT if self.edit_properties_mode_on else self.screen_height
            if mpos[0] < main_area_width and mpos[1] < main_area_height:  # Only if mouse is over main area
                # Scale mouse position to account for display scaling
                scale_x = 960 / (self.screen.get_size()[0] - SIDEBAR_WIDTH)
                scale_y = 576 / (self.screen.get_size()[1])
                mpos = ((mpos[0] / RENDER_SCALE) * scale_x * self.zoom,
                        (mpos[1] / RENDER_SCALE) * scale_y * self.zoom)
                tile_pos = (int((mpos[0] + self.scroll[0]) // self.tilemap.tile_size),
                            int((mpos[1] + self.scroll[1]) // self.tilemap.tile_size))

            mpos_in_mainarea = mpos[0] < main_area_width and mpos[1] < main_area_height

            for lever in self.tilemap.extract(self.levers, keep=True):
                self.levers_ids.add(lever['id'])

            for door in self.tilemap.extract(self.doors, keep=True):
                self.doors_ids.add(door['id'])

            for tp in self.tilemap.extract(self.teleporters, keep=True):
                self.tps_ids.add(tp['id'])

            for button in self.tilemap.extract(self.buttons, keep=True):
                self.buttons_ids.add(button['id'])

            self.activators_ids = {"Levers": self.levers_ids,
                                   "Buttons": self.buttons_ids,
                                   "Teleporters": self.tps_ids}

            if mpos_in_mainarea:
                if not self.window_mode:
                    if not self.edit_properties_mode_on:
                        if self.ongrid:
                            self.display.blit(current_tile_img, (tile_pos[0] * self.tilemap.tile_size - self.scroll[0],
                                                                 tile_pos[1] * self.tilemap.tile_size - self.scroll[1]))
                        else:
                            self.display.blit(current_tile_img, mpos)
                    else:
                        tile_loc = str(tile_pos[0]) + ";" + str(tile_pos[1])
                        if tile_loc in self.tilemap.tilemap:
                            if self.tilemap.tilemap[tile_loc]["type"] in self.activators_types[self.current_activator_category] and not self.clicking:
                                element = self.tilemap.tilemap[tile_loc]["type"]
                                shining_image = self.assets[self.tile_list[self.tile_list.index(element)]][self.tilemap.tilemap[tile_loc]["variant"]].copy()
                                shining_image.fill((255, 255, 255, 100), special_flags=pygame.BLEND_ADD)
                                self.display.blit(shining_image, (tile_pos[0] * self.tilemap.tile_size - self.scroll[0],
                                                                 tile_pos[1] * self.tilemap.tile_size - self.scroll[1]))

            if self.clicking and self.ongrid and mpos_in_mainarea:
                if not self.window_mode:
                    if not self.edit_properties_mode_on:
                        if self.tile_list[self.tile_group] in (l[0] for l in self.levers):
                            t = self.tile_list[self.tile_group]
                            self.set_window_mode()
                            self.showing_properties_window = True
                            self.selected_activator_type = "Levers" if "lever" in t else "Buttons" if "button" in t else "Teleporters"
                            self.selected_activator = {"image": self.assets[t][0],
                                                       "infos": {"id": "", "type": ""}}
                            self.clicking = False
                            self.selected_activator["infos"]["pos"] = tile_pos

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

                        elif self.tile_list[self.tile_group] in (tp[0] for tp in self.teleporters):
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
                    else:
                        tile_loc = str(tile_pos[0]) + ";" + str(tile_pos[1])
                        if tile_loc in self.tilemap.tilemap:
                            t = self.tilemap.tilemap[tile_loc]["type"]
                            if t in self.activators_types[self.current_activator_category]:
                                self.set_window_mode()
                                self.showing_properties_window = True
                                self.selected_activator_type = "Levers" if "lever" in t else "Buttons" if "button" in t else "Teleporters"
                                self.selected_activator = {"image": self.assets[t][0], "infos":self.activators[self.selected_activator_type][tile_loc]}
                                self.clicking = False

            if self.right_clicking and mpos_in_mainarea:
                if not self.window_mode:
                    if not self.edit_properties_mode_on:
                        tile_loc = str(tile_pos[0]) + ";" + str(tile_pos[1])
                        if tile_loc in self.tilemap.tilemap:
                            if self.tilemap.tilemap[tile_loc]['type'] in (l[0] for l in self.levers):
                                self.levers_ids.remove(self.tilemap.tilemap[tile_loc]["id"])
                            if self.tilemap.tilemap[tile_loc]['type'] in (d[0] for d in self.doors):
                                self.doors_ids.remove(self.tilemap.tilemap[tile_loc]["id"])
                            if self.tilemap.tilemap[tile_loc]['type'] in (tp[0] for tp in self.teleporters):
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

            if not self.edit_properties_mode_on:
                self.display.blit(current_tile_img, (5, 5))

            self.render_sidebar()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if not self.window_mode:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if event.button == 1:
                            self.clicking = True
                            if not self.ongrid:
                                self.tilemap.offgrid_tiles.append({'type': self.tile_list[self.tile_group],
                                                                   'variant': self.tile_variant,
                                                                   'pos': (
                                                                   mpos[0] + self.scroll[0], mpos[1] + self.scroll[1])})
                        if event.button == 3:
                            self.right_clicking = True
                        if not self.shift and self.tile_group:
                            if event.button == 4:
                                self.tile_variant = (self.tile_variant - 1) % len(
                                    self.assets[self.tile_list[self.tile_group]])
                            if event.button == 5:
                                self.tile_variant = (self.tile_variant + 1) % len(
                                    self.assets[self.tile_list[self.tile_group]])
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_i and not self.holding_i:
                            self.edit_properties_mode_on = not self.edit_properties_mode_on
                            self.holding_i = True
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
                                self.get_categories()
                                self.get_activators()
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
                                self.get_categories()
                                self.get_activators()
                        if event.key == pygame.K_DOWN:
                            self.zoom = self.zoom * 2
                            self.display = pygame.Surface((480 * self.zoom, 288 * self.zoom))
                        if event.key == pygame.K_UP:
                            self.zoom = self.zoom / 2
                            self.display = pygame.Surface((480 * self.zoom, 288 * self.zoom))

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
                            self.save_edited_values()
                            print("saved")
                        if event.key == pygame.K_c:
                            print((tile_pos[0] * 16, tile_pos[1] * 16))
                    if event.type == pygame.KEYUP:
                        if event.key == pygame.K_i:
                            self.holding_i = False
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
                else:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if event.button == 1:
                            self.clicking = True
                        if event.button == 3:
                            self.right_clicking = True
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            if self.edited_info:
                                self.edited_info = None
                            elif (self.selected_activator["infos"]["type"] and
                                  (self.selected_activator["infos"][info] for info in self.infos_per_type_per_category[self.selected_activator_type][self.selected_activator["infos"]["type"]])):
                                self.window_mode = False
                            else:
                                print("All the infos have to be filled!")
                        if event.key == pygame.K_RETURN:
                            if self.edited_info:
                                if self.edited_value:
                                    if self.edited_info != "id" or self.edited_value not in self.activators_ids[self.selected_activator_type]:
                                        tile_loc = str(self.selected_activator["infos"]["pos"][0]) + ";" \
                                                             + str(self.selected_activator["infos"]["pos"][1])
                                        self.selected_activator["infos"][self.edited_info] = self.edited_value

                                        iD = int(self.selected_activator["infos"]["id"])
                                        self.levers_ids.add(iD)
                                        self.tilemap.tilemap[tile_loc] = \
                                            {
                                                'type': self.tile_list[self.tile_group],
                                                'variant': self.tile_variant,
                                                'pos': self.selected_activator["infos"]["pos"],
                                                'id': iD
                                            }

                                        if tile_loc not in self.activators[self.selected_activator_type]:
                                            self.activators[self.selected_activator_type][tile_loc] = {}

                                        pos = str(self.selected_activator["infos"]["pos"])
                                        tile_loc = pos[1:-1].replace(', ', ';')
                                        self.activators[self.selected_activator_type][tile_loc][self.edited_info] = self.edited_value
                                        self.tilemap.tilemap[tile_loc]["id"] = self.activators[self.selected_activator_type][tile_loc]["id"]
                                        self.edited_value = None
                                        self.edited_info = None
                                    else:
                                        print("id already used")
                                else:
                                    self.edited_info = None

                        if self.edited_info and 48 <= ord(self.edited_value[0] if len(
                                self.edited_value) else '0') <= 57:
                            if event.key == pygame.K_BACKSPACE:
                                self.edited_value = self.edited_value[:-1]
                            if 48 <= event.key <= 57:
                                if len(self.edited_value) < 3:
                                    self.edited_value = str(int(self.edited_value + chr(event.key)))
                                else:
                                    print("max id reached")


                if event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        self.clicking = False
                    if event.button == 3:
                        self.right_clicking = False
                if event.type == pygame.VIDEORESIZE:
                    # Update screen dimensions
                    self.screen_width = max(event.w, 480 + SIDEBAR_WIDTH)  # Minimum width
                    self.screen_height = max(event.h, 288 + UNDERBAR_HEIGHT)  # Minimum height
                    self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)

            # Calculate main area dimensions for scaling
            main_area_width = self.screen_width - SIDEBAR_WIDTH
            main_area_height = self.screen_height

            # Blit everything to screen
            if not self.window_mode:
                scaled_display = pygame.transform.scale(self.display, (main_area_width, main_area_height))
                self.screen.blit(scaled_display, (0, 0))
                self.screen.blit(self.sidebar, (main_area_width, 0))
                if self.edit_properties_mode_on:
                    self.render_underbar()
                    self.screen.blit(self.underbar, (0, main_area_height - UNDERBAR_HEIGHT))
            else:
                self.update_window_mode_bg()
                if self.showing_properties_window:
                    self.render_info_window()
                    self.screen.blit(self.properties_window, ((self.screen_width-self.properties_window.get_width())/2,
                                                              (self.screen_height-self.properties_window.get_height())/2))

            pygame.display.update()
            self.clock.tick(60)


Editor().run()