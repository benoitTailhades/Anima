import pygame as py
import sys

py.init()
screen = py.display.set_mode(((1200,720)))
py.display.set_caption("Anima")

BG = py.image.load("../assets/images/menubacck.jpg")

def menu_principal_screen():
    screen.blit(BG,(0,0))
    menu_mouse_pos = py.mouse.get_pos()
    play_button = ("PLAY")

def play_screen():
    l, L = 800, 600
    BLUE, WHITE = (0, 100, 200), (255, 255, 255)
    screen = py.display.set_mode((l, L))
    py.display.set_caption("Anima")

    playing = True
    while playing:
        for event in py.event.get():
            if event.type == py.QUIT:
                playing = False

        screen.fill(WHITE)
        py.display.update()

menu_principal_screen()

py.quit()





