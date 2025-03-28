import pygame
import time


pygame.mixer.init()
def run_sound(path):
    background_menu = pygame.mixer.Sound(path)
    background_menu.play(1000,0,5000)
