import pygame
import os

from numpy.f2py.crackfortran import skipfuncs

BASE_IMG_PATH = "assets/images/"

def load_image(path, size=None):
    img = pygame.image.load(BASE_IMG_PATH + path)
    img.set_colorkey((0, 0, 0))
    if size:
        img = pygame.transform.scale(img, size)  # Resize image if size is provided
    return img

def load_images(path, tile_size=None):
    images = []
    if type(tile_size) is not tuple and tile_size:
        tile_size = (tile_size, tile_size)
    for img_name in sorted(os.listdir(BASE_IMG_PATH + path)):
        images.append(load_image(path + '/' + img_name, (tile_size[0], tile_size[1]) if tile_size else None))
    return images

def round_up(x):
    return int(x) + 1 if x % 1 != 0 and x > 0 else int(x)

def display_bg(surf, img, pos):
    n = pos[0]//img.get_width()
    if pos[0] - n*img.get_width() > 0:
        surf.blit(img, (pos[0] - n* img.get_width(), pos[1]))
        surf.blit(img, (pos[0] - (n+1)*img.get_width() - 1, pos[1]))

    elif pos[0] + n*img.get_width() < 0:
        surf.blit(img, (pos[0] + (n+1)*img.get_width(), pos[1]))
        surf.blit(img, (pos[0] + n* img.get_width(), pos[1]))

def load_tiles():
    tiles = {}
    for tile in sorted(os.listdir(BASE_IMG_PATH + 'tiles')):
        tiles[tile] = load_images('tiles/'+ tile)
    return tiles

def load_entities(e_info):
    tiles = {}
    for ent in sorted(os.listdir(BASE_IMG_PATH + 'entities/')):
        if ent not in ("player", "melee_boss"):
            for tile in sorted(os.listdir(BASE_IMG_PATH + 'entities/' + ent)):
                for animation in sorted(os.listdir(BASE_IMG_PATH + 'entities/' + ent + '/' + tile)):
                    if animation in e_info[tile]["left/right"]:
                        for direction in sorted(os.listdir(BASE_IMG_PATH + 'entities/' + ent + '/' + tile + '/' + animation)):
                            tiles[tile + '/' + animation + '/' + direction] = Animation(load_images('entities/' + ent + '/' +
                                                                                                    tile + '/' +
                                                                                                    animation + '/' +
                                                                                                    direction),
                                                                                        img_dur=e_info[tile]["img_dur"][animation],
                                                                                        loop=e_info[tile]["loop"][animation])
                    else:
                        tiles[tile+'/'+animation] = Animation(load_images('entities/' + ent + '/' + tile + '/' + animation),
                                                              img_dur=e_info[tile]["img_dur"][animation],
                                                              loop=e_info[tile]["loop"][animation])
    return tiles

def load_player():
    return {'player/idle': Animation(load_images('entities/player/idle'), img_dur=12),
            'player/run/right': Animation(load_images('entities/player/run/right'), img_dur=3),
            'player/run/left': Animation(load_images('entities/player/run/left'), img_dur=3),
            'player/jump/right': Animation(load_images('entities/player/jump/right'), img_dur=3, loop=False),
            'player/jump/left': Animation(load_images('entities/player/jump/left'), img_dur=3, loop=False),
            'player/jump/top': Animation(load_images('entities/player/jump/top'), img_dur=3, loop=False),
            'player/falling/right': Animation(load_images('entities/player/falling/right'), img_dur=3, loop=True),
            'player/falling/left': Animation(load_images('entities/player/falling/left'), img_dur=3, loop=True),
            'player/falling/vertical': Animation(load_images('entities/player/falling/vertical'), img_dur=3, loop=True),
            'player/dash/right': Animation(load_images('entities/player/dash/right'), img_dur=3, loop=False),
            'player/dash/left': Animation(load_images('entities/player/dash/left'), img_dur=3, loop=False),
            'player/dash/top': Animation(load_images('entities/player/dash/top'), img_dur=3, loop=False),
            'player/wall_slide/right': Animation(load_images('entities/player/wall_slide/right'), img_dur=3,loop=False),
            'player/wall_slide/left': Animation(load_images('entities/player/wall_slide/left'), img_dur=3, loop=False),
            'player/attack/right': Animation(load_images('entities/player/attack/right'), img_dur=2, loop=False),
            'player/attack/left': Animation(load_images('entities/player/attack/left'), img_dur=2, loop=False)}

class Animation:
    def __init__(self, images, img_dur = 5, loop = True):
        self.images = images
        self.loop = loop
        self.img_duration = img_dur
        self.done = False
        self.frame = 0

    def copy(self):#will be very useful for the screen.copy when displaying the menu
        return Animation(self.images, self.img_duration, self.loop)

    def update(self):
        if self.loop > 0:
            self.frame = (self.frame + 1) % (self.img_duration * len(self.images))
            if type(self.loop) in (int, float):
                self.loop -= (1/int(self.img_duration * len(self.images)))

        else:
            self.frame = min(self.frame + 1, self.img_duration * len(self.images) - 1)
            if self.frame >= self.img_duration * len(self.images) - 1:
                self.done = True

    def img(self):
        return self.images[int(self.frame / self.img_duration)]


def load_game_font(font_name=None, size=36):

    RECOMMENDED_FONTS = [
        'DejaVuSans-Bold.ttf',
        'FreeMono.ttf',
        'LiberationMono-Bold.ttf'
    ]
    font_paths = [
        os.path.join(os.path.dirname(__file__), 'fonts', font_name) if font_name else None,*[os.path.join(os.path.dirname(__file__), 'fonts', f) for f in RECOMMENDED_FONTS]
    ]
    for path in font_paths:
        try:
            if path and os.path.exists(path):
                return pygame.font.Font(path, size)
        except:
            pass
    return pygame.font.SysFont('monospace', size, bold=True)




