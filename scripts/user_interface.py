import pygame as py
import sys

def option_menu():
    py.init()
    screen = py.display.set_mode((1000, 600), py.RESIZABLE)
    py.display.set_caption("Menu Options")

    font = py.font.Font(None, 36)


    WHITE = (255, 255, 255)
    LIGHT_GRAY = (220, 220, 220)
    GRAY = (160, 160, 160)
    DARK_GRAY = (80, 80, 80)
    BLUE = (50, 130, 230)
    BLACK = (0, 0, 0)


    slider_rect = py.Rect(150, 150, 500, 10)
    knob_radius = 15
    volume = 0.5
    knob_x = slider_rect.x + int(volume * slider_rect.width)
    knob_y = slider_rect.y + slider_rect.height // 2
    dragging = False


    languages = ["Français 🇫🇷", "English 🇬🇧", "Español 🇪🇸", "Deutsch 🇩🇪"]
    selected_language = languages[0]
    dropdown_rect = py.Rect(150, 300, 300, 40)
    dropdown_expanded = False

    while True:
        for event in py.event.get():
            if event.type == py.QUIT:
                py.quit()
                sys.exit()

            elif event.type == py.MOUSEBUTTONDOWN:
                mouse_pos = event.pos


                knob_area = py.Rect(knob_x - knob_radius, knob_y - knob_radius, knob_radius * 2, knob_radius * 2)
                if knob_area.collidepoint(mouse_pos) or slider_rect.collidepoint(mouse_pos):
                    dragging = True

                if dropdown_rect.collidepoint(mouse_pos):
                    dropdown_expanded = not dropdown_expanded
                elif dropdown_expanded:
                    for i, lang in enumerate(languages):

                        option_rect = py.Rect(dropdown_rect.x, dropdown_rect.y + (i + 1) * dropdown_rect.height,
                                               dropdown_rect.width, dropdown_rect.height)
                        if option_rect.collidepoint(mouse_pos):
                            selected_language = lang
                            dropdown_expanded = False
                            break
                    else:
                        dropdown_expanded = False

            elif event.type == py.MOUSEBUTTONUP:
                dragging = False

            elif event.type == py.MOUSEMOTION:
                if dragging:
                    mouse_x, _ = event.pos

                    new_x = max(slider_rect.x, min(mouse_x, slider_rect.x + slider_rect.width))
                    knob_x = new_x

                    volume = (knob_x - slider_rect.x) / slider_rect.width


        screen.fill(WHITE)
        py.draw.rect(screen, GRAY, slider_rect, border_radius=5)

        py.draw.circle(screen, BLACK, (knob_x, knob_y), knob_radius)


        vol_text = font.render(f"Volume : {int(volume * 100)}%", True, BLACK)
        screen.blit(vol_text, (slider_rect.x, slider_rect.y - 40))

        py.draw.rect(screen, GRAY, dropdown_rect, border_radius=5)

        lang_text = font.render(f"Langue : {selected_language}", True, BLACK)
        screen.blit(lang_text, (dropdown_rect.x + 10, dropdown_rect.y + 5))


        arrow = "▲" if dropdown_expanded else "▼"
        arrow_text = font.render(arrow, True, BLACK)
        screen.blit(arrow_text, (dropdown_rect.right - 40, dropdown_rect.y + 5))

        if dropdown_expanded:
            for i, lang in enumerate(languages):

                option_rect = py.Rect(dropdown_rect.x, dropdown_rect.y + (i + 1) * dropdown_rect.height,
                                       dropdown_rect.width, dropdown_rect.height)
                py.draw.rect(screen, LIGHT_GRAY, option_rect, border_radius=5)
                option_text = font.render(lang, True, BLACK)
                screen.blit(option_text, (option_rect.x + 10, option_rect.y + 5))  # Afficher le texte de l'option
                py.draw.rect(screen, DARK_GRAY, option_rect, 2, border_radius=5)  # Dessiner un contour en gris foncé autour de l'option

        py.display.flip()  # Mettre à jour l'affichage de la fenêtre avec tous les changements graphiques



def menu():
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
                            sys.exit()
                        elif text == "OPTION":
                            option_menu()  # Placeholder
                        elif text == "RESUME":
                            running = False  # Placeholder