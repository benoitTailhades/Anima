import pygame as py

def menu():
    # Initialisation de Pygame
    py.init()
    screen = py.display.set_mode((1000, 600),py.RESIZABLE)
    py.display.set_caption("Menu")

    # Couleurs
    WHITE = (255, 255, 255)
    GRAY = (170, 170, 170)
    DARK_GRAY = (100, 100, 100)
    BLACK = (0, 0, 0)

    # Police
    font = py.font.Font(None, 40)


    buttons = {
        "RESUME": py.Rect(150, 100, 200, 50),
        "OPTION": py.Rect(150, 180, 200, 50),
        "QUIT": py.Rect(150, 260, 200, 50)
    }


    def draw_buttons():
        screen.fill(WHITE)

        for text, rect in buttons.items():
            color = DARK_GRAY if rect.collidepoint(py.mouse.get_pos()) else GRAY
            py.draw.rect(screen, color, rect, border_radius=10)
            label = font.render(text, True, BLACK)
            screen.blit(label, (rect.x + 50, rect.y + 10))

        py.display.flip()



    running = True
    while running:
        draw_buttons()

        for event in py.event.get():
            if event.type == py.QUIT:
                running = False
            elif event.type == py.MOUSEBUTTONDOWN and event.button == 1:
                for text, rect in buttons.items():
                    if rect.collidepoint(event.pos):
                        if text == "QUIT":
                            running = False
                        elif text == "OPTION":
                            print("Options menu")  # Placeholder
                        elif text == "RESUME":
                            print("Resume game")  # Placeholder