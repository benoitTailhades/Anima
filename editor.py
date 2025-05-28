import sys
import pygame
import json
from scripts.utils import load_images, load_tiles, load_doors, load_activators
from scripts.tilemap import Tilemap

RENDER_SCALE = 2.0
SIDEBAR_WIDTH = 200


class Editor:
    def __init__(self):
        pygame.init()

        pygame.display.set_caption("Editor")
        self.screen_width = 960 + SIDEBAR_WIDTH
        self.screen_height = 576
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)
        self.display = pygame.Surface((480, 288))
        self.sidebar = pygame.Surface((SIDEBAR_WIDTH, self.screen_height))

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
        for env in self.environments:
            self.doors += [(door, 0) for door in load_doors('editor', env) if "door" in door]
            self.levers += [(lever, 0) for lever in load_activators(env) if "lever" in lever]
            self.buttons += [(button, 0) for button in load_activators(env) if "button" in button]
            self.teleporters += [(tp, 0) for tp in load_activators(env) if "teleporter" in tp]

        self.assets = self.base_assets | load_tiles(self.get_environment(self.level))
        self.assets.update(load_doors('editor', self.get_environment(self.level)))
        self.assets.update(load_activators(self.get_environment(self.level)))

        self.movement = [False, False, False, False]

        self.tilemap = Tilemap(self, self.tile_size)

        try:
            self.tilemap.load('data/maps/' + str(self.level) + '.json')
        except FileNotFoundError:
            pass

        self.scroll = [0, 0]

        # Organize assets into categories
        self.categories = self.organize_assets()
        self.category_names = list(self.categories.keys())
        self.current_category = 0
        self.selected_tile = 0
        # NEW: Track current variant for each asset
        self.current_variants = {}  # Will store current variant for each asset type

        self.levers_ids = set()
        self.doors_ids = set()
        self.buttons_ids = set()
        self.tps_ids = set()

        self.zoom = 1
        self.clicking = False
        self.right_clicking = False
        self.shift = False
        self.ongrid = True

        # Sidebar scrolling
        self.sidebar_scroll = 0
        self.sidebar_item_height = 40

        # Font for UI
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)

    def organize_assets(self):
        """Organize assets into logical categories"""
        categories = {
            "Tiles": [],
            "Doors": [],
            "Levers": [],
            "Buttons": [],
            "Teleporters": [],
            "Spawners": [],
            "Transition": [],
            "Throwable": []
        }

        for asset_name in self.assets:
            if any(door[0] == asset_name for door in self.doors):
                categories["Doors"].append(asset_name)
            elif any(lever[0] == asset_name for lever in self.levers):
                categories["Levers"].append(asset_name)
            elif any(button[0] == asset_name for button in self.buttons):
                categories["Buttons"].append(asset_name)
            elif any(tp[0] == asset_name for tp in self.teleporters):
                categories["Teleporters"].append(asset_name)
            elif "spawners" in asset_name:
                # NEW: Expand spawners into individual variants
                if asset_name in self.assets:
                    for variant_idx in range(len(self.assets[asset_name])):
                        spawner_item = f"{asset_name}_{variant_idx}"
                        categories["Spawners"].append(spawner_item)
                else:
                    categories["Spawners"].append(asset_name)
            elif "transition" in asset_name:
                categories["Transition"].append(asset_name)
            elif "throwable" in asset_name:
                categories["Throwable"].append(asset_name)
            else:
                categories["Tiles"].append(asset_name)

        # Remove empty categories
        return {k: v for k, v in categories.items() if v}

    def get_current_tile_info(self):
        """Get current selected tile type and variant"""
        if not self.category_names:
            return None, 0

        current_category_name = self.category_names[self.current_category]
        current_category_items = self.categories[current_category_name]

        if not current_category_items:
            return None, 0

        if self.selected_tile >= len(current_category_items):
            self.selected_tile = 0

        selected_item = current_category_items[self.selected_tile]

        # NEW: Handle spawner variants as separate items
        if current_category_name == "Spawners" and "_" in selected_item:
            # This is a spawner variant item (e.g., "spawners_0", "spawners_1")
            parts = selected_item.rsplit("_", 1)
            if len(parts) == 2 and parts[1].isdigit():
                tile_type = parts[0]  # "spawners"
                variant = int(parts[1])  # 0, 1, 2, etc.
                return tile_type, variant

        # For all other items, use the existing variant system
        tile_type = selected_item

        # Get current variant for this tile type (except spawners which are handled above)
        if tile_type not in self.current_variants:
            self.current_variants[tile_type] = 0

        # Make sure variant is valid for this asset
        if tile_type in self.assets:
            max_variants = len(self.assets[tile_type])
            if self.current_variants[tile_type] >= max_variants:
                self.current_variants[tile_type] = 0

        return tile_type, self.current_variants[tile_type]

    def cycle_variant(self, direction=1):
        """Cycle through variants of the current tile type"""
        # NEW: Don't allow variant cycling for spawners (they're handled as separate items)
        current_category_name = self.category_names[self.current_category]
        if current_category_name == "Spawners":
            return  # Skip variant cycling for spawners

        tile_type, current_variant = self.get_current_tile_info()
        if tile_type and tile_type in self.assets:
            max_variants = len(self.assets[tile_type])
            if max_variants > 1:
                self.current_variants[tile_type] = (current_variant + direction) % max_variants

    def render_sidebar(self):
        """Render the sidebar with categories and items"""
        # Recreate sidebar surface with current screen height
        self.sidebar = pygame.Surface((SIDEBAR_WIDTH, self.screen_height))
        self.sidebar.fill((40, 40, 40))

        if not self.category_names:
            return

        current_category_name = self.category_names[self.current_category]
        current_category_items = self.categories[current_category_name]

        # Draw category title
        category_text = self.font.render(current_category_name, True, (255, 255, 255))
        self.sidebar.blit(category_text, (10, 10))

        # Draw category navigation
        nav_y = 40
        if len(self.category_names) > 1:
            nav_text = self.small_font.render("Mouse wheel: Switch category", True, (200, 200, 200))
            self.sidebar.blit(nav_text, (10, nav_y))
            nav_y += 20

        # NEW: Show variant info for current selection (but not for spawners)
        if current_category_name != "Spawners":
            tile_type, current_variant = self.get_current_tile_info()
            if tile_type and tile_type in self.assets:
                max_variants = len(self.assets[tile_type])
                if max_variants > 1:
                    variant_text = self.small_font.render(
                        f"Variant: {current_variant + 1}/{max_variants} (A/E to cycle)",
                        True, (200, 200, 200))
                    self.sidebar.blit(variant_text, (10, nav_y))
                    nav_y += 20

        # Draw items in current category
        items_start_y = nav_y + 10
        visible_items = (self.screen_height - items_start_y) // self.sidebar_item_height

        for i, item in enumerate(current_category_items):
            item_y = items_start_y + i * self.sidebar_item_height - self.sidebar_scroll

            if item_y < items_start_y - self.sidebar_item_height or item_y > self.screen_height:
                continue

            # Highlight selected item
            item_rect = pygame.Rect(5, item_y, SIDEBAR_WIDTH - 10, self.sidebar_item_height - 2)
            if i == self.selected_tile:
                pygame.draw.rect(self.sidebar, (80, 120, 200), item_rect)
            else:
                pygame.draw.rect(self.sidebar, (60, 60, 60), item_rect)

            pygame.draw.rect(self.sidebar, (100, 100, 100), item_rect, 1)

            # Draw item preview if possible
            try:
                # NEW: Handle spawner variant items
                if current_category_name == "Spawners" and "_" in item:
                    parts = item.rsplit("_", 1)
                    if len(parts) == 2 and parts[1].isdigit():
                        base_asset = parts[0]  # "spawners"
                        variant_idx = int(parts[1])  # 0, 1, 2, etc.

                        if base_asset in self.assets and variant_idx < len(self.assets[base_asset]):
                            preview_img = self.assets[base_asset][variant_idx].copy()
                            # Scale preview to fit
                            max_size = self.sidebar_item_height - 8
                            if preview_img.get_width() > max_size or preview_img.get_height() > max_size:
                                scale_factor = min(max_size / preview_img.get_width(),
                                                   max_size / preview_img.get_height())
                                new_size = (int(preview_img.get_width() * scale_factor),
                                            int(preview_img.get_height() * scale_factor))
                                preview_img = pygame.transform.scale(preview_img, new_size)

                            preview_x = 8
                            preview_y = item_y + (self.sidebar_item_height - preview_img.get_height()) // 2
                            self.sidebar.blit(preview_img, (preview_x, preview_y))

                        # Draw spawner variant name
                        text_x = 8 + max_size + 8
                        item_name = f"Spawner {variant_idx + 1}"

                # Handle regular items
                elif item in self.assets and len(self.assets[item]) > 0:
                    # Show current variant for the selected item, first variant for others
                    variant_to_show = 0
                    if i == self.selected_tile and item in self.current_variants:
                        variant_to_show = self.current_variants[item]

                    if variant_to_show < len(self.assets[item]):
                        preview_img = self.assets[item][variant_to_show].copy()
                        # Scale preview to fit
                        max_size = self.sidebar_item_height - 8
                        if preview_img.get_width() > max_size or preview_img.get_height() > max_size:
                            scale_factor = min(max_size / preview_img.get_width(),
                                               max_size / preview_img.get_height())
                            new_size = (int(preview_img.get_width() * scale_factor),
                                        int(preview_img.get_height() * scale_factor))
                            preview_img = pygame.transform.scale(preview_img, new_size)

                        preview_x = 8
                        preview_y = item_y + (self.sidebar_item_height - preview_img.get_height()) // 2
                        self.sidebar.blit(preview_img, (preview_x, preview_y))

                    # Draw item name with variant count (except for spawners)
                    text_x = 8 + max_size + 8
                    item_name = item
                    if current_category_name != "Spawners" and len(self.assets[item]) > 1:
                        item_name += f" ({len(self.assets[item])})"
                else:
                    text_x = 12
                    item_name = item

                item_text = self.small_font.render(item_name, True, (255, 255, 255))
                text_y = item_y + (self.sidebar_item_height - item_text.get_height()) // 2
                self.sidebar.blit(item_text, (text_x, text_y))

            except (KeyError, IndexError):
                # Fallback to just text
                item_text = self.small_font.render(item, True, (255, 255, 255))
                text_y = item_y + (self.sidebar_item_height - item_text.get_height()) // 2
                self.sidebar.blit(item_text, (12, text_y))

    def handle_sidebar_click(self, pos):
        """Handle clicks on the sidebar"""
        main_area_width = self.screen_width - SIDEBAR_WIDTH
        if pos[0] < main_area_width:  # Click is not on sidebar
            return False

        sidebar_x = pos[0] - main_area_width
        sidebar_y = pos[1]

        if not self.category_names:
            return True

        current_category_items = self.categories[self.category_names[self.current_category]]

        items_start_y = 80  # Adjust based on your layout
        clicked_item = (sidebar_y + self.sidebar_scroll - items_start_y) // self.sidebar_item_height

        if 0 <= clicked_item < len(current_category_items):
            self.selected_tile = clicked_item

        return True

    def get_environment(self, level):
        for environment in self.environments:
            if level in self.environments[environment]:
                return environment

    def run(self):
        while True:
            # Clear displays
            self.display.fill((0, 0, 0))

            # Handle movement
            self.scroll[0] += (self.movement[1] - self.movement[0]) * 8
            self.scroll[1] += (self.movement[3] - self.movement[2]) * 8
            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))

            # Render tilemap
            self.tilemap.render(self.display, offset=render_scroll)
            self.tilemap.render_over(self.display, offset=render_scroll)

            # Get current tile
            tile_type, tile_variant = self.get_current_tile_info()

            if tile_type and tile_type in self.assets:
                current_tile_img = self.assets[tile_type][tile_variant].copy()
                current_tile_img.set_alpha(100)

                # Calculate mouse position (only for main display area)
                mpos = pygame.mouse.get_pos()
                main_area_width = self.screen_width - SIDEBAR_WIDTH
                if mpos[0] < main_area_width:  # Only if mouse is over main area
                    # Scale mouse position to account for display scaling
                    scale_x = (960) / (self.screen.get_size()[0] - SIDEBAR_WIDTH)
                    scale_y = 576 / (self.screen.get_size()[1])
                    mpos = ((mpos[0] / RENDER_SCALE) * scale_x * self.zoom,
                            (mpos[1] / RENDER_SCALE) * scale_y * self.zoom)
                    tile_pos = (int((mpos[0] + self.scroll[0]) // self.tilemap.tile_size),
                                int((mpos[1] + self.scroll[1]) // self.tilemap.tile_size))

                    # Update ID sets
                    for lever in self.tilemap.extract(self.levers, keep=True):
                        self.levers_ids.add(lever['id'])

                    for door in self.tilemap.extract(self.doors, keep=True):
                        self.doors_ids.add(door['id'])

                    for tp in self.tilemap.extract(self.teleporters, keep=True):
                        self.tps_ids.add(tp['id'])

                    for button in self.tilemap.extract(self.buttons, keep=True):
                        self.buttons_ids.add(button['id'])

                    # Show preview
                    if self.ongrid:
                        self.display.blit(current_tile_img, (tile_pos[0] * self.tilemap.tile_size - self.scroll[0],
                                                             tile_pos[1] * self.tilemap.tile_size - self.scroll[1]))
                    else:
                        self.display.blit(current_tile_img, mpos)

                    # Handle placing tiles
                    if self.clicking and self.ongrid:
                        if tile_type in (l[0] for l in self.levers):
                            iD = int(input("Enter the lever id: "))
                            while iD in self.levers_ids:
                                print("id already used")
                                iD = int(input("Enter the lever id: "))
                            self.levers_ids.add(iD)
                            self.tilemap.tilemap[str(tile_pos[0]) + ";" + str(tile_pos[1])] = {
                                'type': tile_type,
                                'variant': tile_variant,
                                'pos': tile_pos,
                                'id': iD}

                        elif tile_type in (d[0] for d in self.doors):
                            iD = int(input("Enter the door id: "))
                            while iD in self.doors_ids:
                                print("id already used")
                                iD = int(input("Enter the door id: "))
                            self.doors_ids.add(iD)
                            self.tilemap.tilemap[str(tile_pos[0]) + ";" + str(tile_pos[1])] = {
                                'type': tile_type,
                                'variant': tile_variant,
                                'pos': tile_pos,
                                'id': iD}

                        elif tile_type in (b[0] for b in self.buttons):
                            iD = int(input("Enter the button id: "))
                            while iD in self.buttons_ids:
                                print("id already used")
                                iD = int(input("Enter the button id: "))
                            self.buttons_ids.add(iD)
                            self.tilemap.tilemap[str(tile_pos[0]) + ";" + str(tile_pos[1])] = {
                                'type': tile_type,
                                'variant': tile_variant,
                                'pos': tile_pos,
                                'id': iD}

                        elif tile_type in (tp[0] for tp in self.teleporters):
                            iD = int(input("Enter the tp id: "))
                            while iD in self.tps_ids:
                                print("id already used")
                                iD = int(input("Enter the tp id: "))
                            self.tps_ids.add(iD)
                            self.tilemap.tilemap[str(tile_pos[0]) + ";" + str(tile_pos[1])] = {
                                'type': tile_type,
                                'variant': tile_variant,
                                'pos': tile_pos,
                                'id': iD}

                        elif tile_type == "transition":
                            direction = int(input("Enter the destination level: "))
                            self.tilemap.tilemap[str(tile_pos[0]) + ";" + str(tile_pos[1])] = {
                                'type': tile_type,
                                'variant': tile_variant,
                                'pos': tile_pos,
                                'destination': direction}

                        else:
                            self.tilemap.tilemap[str(tile_pos[0]) + ";" + str(tile_pos[1])] = {
                                'type': tile_type,
                                'variant': tile_variant,
                                'pos': tile_pos}

                    # Handle removing tiles
                    if self.right_clicking and mpos[0] < main_area_width:
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

                # Show current tile in corner
                self.display.blit(current_tile_img, (5, 5))

            # Render sidebar
            self.render_sidebar()

            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    # Check if click is on sidebar
                    if self.handle_sidebar_click(pygame.mouse.get_pos()):
                        continue

                    # Handle main area clicks
                    if event.button == 1:
                        self.clicking = True
                        main_area_width = self.screen_width - SIDEBAR_WIDTH
                        if not self.ongrid and pygame.mouse.get_pos()[0] < main_area_width:
                            mpos = pygame.mouse.get_pos()
                            scale_x = main_area_width / 480
                            scale_y = self.screen_height / 288
                            mpos = (mpos[0] / scale_x, mpos[1] / scale_y)
                            tile_type, tile_variant = self.get_current_tile_info()
                            if tile_type:
                                self.tilemap.offgrid_tiles.append({'type': tile_type,
                                                                   'variant': tile_variant,
                                                                   'pos': (
                                                                       mpos[0] + self.scroll[0],
                                                                       mpos[1] + self.scroll[1])})
                    if event.button == 3:
                        self.right_clicking = True

                    # Mouse wheel for category switching
                    if event.button == 4:  # Scroll up
                        self.current_category = (self.current_category - 1) % len(self.category_names)
                        self.selected_tile = 0
                    if event.button == 5:  # Scroll down
                        self.current_category = (self.current_category + 1) % len(self.category_names)
                        self.selected_tile = 0

                if event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        self.clicking = False
                    if event.button == 3:
                        self.right_clicking = False

                if event.type == pygame.KEYDOWN:
                    # NEW: Add variant cycling controls (disabled for spawners)
                    if event.key == pygame.K_a:  # Previous variant
                        self.cycle_variant(-1)
                    if event.key == pygame.K_e:  # Next variant
                        self.cycle_variant(1)

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

                            self.assets = self.base_assets | load_tiles(self.get_environment(self.level))
                            self.assets.update(load_doors('editor', self.get_environment(self.level)))
                            self.assets.update(load_activators(self.get_environment(self.level)))
                            self.categories = self.organize_assets()
                            self.category_names = list(self.categories.keys())
                            self.levers_ids = set()
                            self.doors_ids = set()
                            self.buttons_ids = set()
                            self.tps_ids = set()
                            self.current_category = 0
                            self.selected_tile = 0
                            # NEW: Reset variants when changing levels
                            self.current_variants = {}

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
                            self.categories = self.organize_assets()
                            self.category_names = list(self.categories.keys())
                            self.levers_ids = set()
                            self.doors_ids = set()
                            self.buttons_ids = set()
                            self.tps_ids = set()
                            self.current_category = 0
                            self.selected_tile = 0
                            # NEW: Reset variants when changing levels
                            self.current_variants = {}

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
                        print("saved")
                    if event.key == pygame.K_c:
                        mpos = pygame.mouse.get_pos()
                        main_area_width = self.screen_width - SIDEBAR_WIDTH
                        if mpos[0] < main_area_width:
                            scale_x = main_area_width / 480
                            scale_y = self.screen_height / 288
                            mpos = (mpos[0] / scale_x, mpos[1] / scale_y)
                            tile_pos = (int((mpos[0] + self.scroll[0]) // self.tilemap.tile_size),
                                        int((mpos[1] + self.scroll[1]) // self.tilemap.tile_size))
                            print((tile_pos[0] * 16, tile_pos[1] * 16))

                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_q:
                        self.movement[0] = False
                    if event.key == pygame.K_d:
                        self.movement[1] = False
                    if event.key == pygame.K_z:
                        self.movement[2] = False
                    if event.key == pygame.K_s:
                        self.movement[3] = False
                        self.ongrid = not self.ongrid
                    if event.key == pygame.K_t:
                        self.tilemap.autotile()
                    if event.key == pygame.K_LSHIFT:
                        self.shift = True
                    if event.key == pygame.K_o:
                        self.tilemap.save('data/maps/' + str(self.level) + '.json')
                        print("saved")
                    if event.key == pygame.K_c:
                        mpos = pygame.mouse.get_pos()
                        main_area_width = self.screen_width - SIDEBAR_WIDTH
                        if mpos[0] < main_area_width:
                            scale_x = main_area_width / 480
                            scale_y = self.screen_height / 288
                            mpos = (mpos[0] / scale_x, mpos[1] / scale_y)
                            tile_pos = (int((mpos[0] + self.scroll[0]) // self.tilemap.tile_size),
                                        int((mpos[1] + self.scroll[1]) // self.tilemap.tile_size))
                            print((tile_pos[0] * 16, tile_pos[1] * 16))

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
                    # Update screen dimensions
                    self.screen_width = max(event.w, 480 + SIDEBAR_WIDTH)  # Minimum width
                    self.screen_height = max(event.h, 288)  # Minimum height
                    self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)

            # Calculate main area dimensions for scaling
            main_area_width = self.screen_width - SIDEBAR_WIDTH

            # Blit everything to screen
            scaled_display = pygame.transform.scale(self.display, (main_area_width, self.screen_height))
            self.screen.blit(scaled_display, (0, 0))
            self.screen.blit(self.sidebar, (main_area_width, 0))

            pygame.display.update()
            self.clock.tick(60)


Editor().run()