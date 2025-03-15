import pygame

import os

BASE_IMG_PATH = "assets/images/"

def load_image(path, size=None):
    img = pygame.image.load(BASE_IMG_PATH + path)
    img.set_colorkey((0, 0, 0))
    if size:
        img = pygame.transform.scale(img, size)  # Resize image if size is provided
    return img

def load_images(path, tile_size=None):
    images = []
    for img_name in sorted(os.listdir(BASE_IMG_PATH + path)):
        images.append(load_image(path + '/' + img_name, (tile_size, tile_size) if tile_size else None))
    return images

def round_up(x):
    return int(x) + 1 if x % 1 != 0 and x > 0 else int(x)

class Animation:
    def __init__(self, images, img_dur = 5, loop = True):
        self.images = images
        self.loop = loop
        self.img_duration = img_dur
        self.done = False
        self.frame = 0

    def copy(self):
        return Animation(self.images, self.img_duration, self.loop)

    def update(self):
        if self.loop:
            self.frame = (self.frame + 1) % (self.img_duration * len(self.images))
        else:
            self.frame = min(self.frame + 1, self.img_duration * len(self.images) - 1)
            if self.frame >= self.img_duration * len(self.images) - 1:
                self.done = True


    def img(self):
        return self.images[int(self.frame / self.img_duration)]


