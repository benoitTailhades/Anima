import pygame as py
import sys


class Menu:
    def __init__(self, game):
        self.game = game
        self.screen = game.screen
        self.background = None

    def capture_background(self):
        """ Capture l'écran actuel du jeu pour l'afficher en arrière-plan du menu """
        self.background = self.screen.copy()

    def draw_gradient(self, screen, color1, color2):
        width, height = screen.get_size()
        for y in range(height):
            r = color1[0] + (color2[0] - color1[0]) * y // height
            g = color1[1] + (color2[1] - color1[1]) * y // height
            b = color1[2] + (color2[2] - color1[2]) * y // height
            py.draw.line(screen, (r, g, b, 150), (0, y), (width, y))

    def option_menu(self):
        py.init()
        screen = py.display.set_mode((1000, 600), py.RESIZABLE)
        py.display.set_caption("Menu Options")

        font = py.font.Font(None, 36)

        WHITE = (255, 255, 255)
        LIGHT_GRAY = (220, 220, 220)
        GRAY = (160, 160, 160)
        DARK_GRAY = (80, 80, 80)
        BLACK = (0, 0, 0)
        BLUE = (50, 130, 230)

        slider_rect = py.Rect(250, 200, 500, 10)
        knob_radius = 15
        volume = 0.5
        knob_x = slider_rect.x + int(volume * slider_rect.width)
        knob_y = slider_rect.y + slider_rect.height // 2
        dragging = False

        languages = ["Français ", "English ", "Español "]
        selected_language = languages[0]
        dropdown_rect = py.Rect(350, 300, 300, 40)
        dropdown_expanded = False
        back_button = py.Rect(400, 450, 200, 50)

        while True:
            screen.fill(WHITE)
            self.draw_gradient(screen, (30, 144, 255), (100, 200, 255))

            for event in py.event.get():
                if event.type == py.QUIT:
                    py.quit()
                    sys.exit()

                elif event.type == py.MOUSEBUTTONDOWN:
                    mouse_pos = event.pos
                    if back_button.collidepoint(mouse_pos):
                        return
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
                        knob_x = max(slider_rect.x, min(mouse_x, slider_rect.x + slider_rect.width))
                        volume = (knob_x - slider_rect.x) / slider_rect.width

            py.draw.rect(screen, GRAY, slider_rect, border_radius=5)
            py.draw.circle(screen, BLACK, (knob_x, knob_y), knob_radius)
            vol_text = font.render(f"Volume : {int(volume * 100)}%", True, BLACK)
            screen.blit(vol_text, (slider_rect.x, slider_rect.y - 40))

            py.draw.rect(screen, GRAY, dropdown_rect, border_radius=5)
            lang_text = font.render(f"Langue : {selected_language}", True, BLACK)
            screen.blit(lang_text, (dropdown_rect.x + 10, dropdown_rect.y + 5))

            if dropdown_expanded:
                for i, lang in enumerate(languages):
                    option_rect = py.Rect(dropdown_rect.x, dropdown_rect.y + (i + 1) * dropdown_rect.height, dropdown_rect.width, dropdown_rect.height)
                    py.draw.rect(screen, LIGHT_GRAY, option_rect, border_radius=5)
                    option_text = font.render(lang, True, BLACK)
                    screen.blit(option_text, (option_rect.x + 10, option_rect.y + 5))
                    py.draw.rect(screen, DARK_GRAY, option_rect, 2, border_radius=5)

            py.draw.rect(screen, GRAY, back_button, border_radius=5)
            back_text = font.render("Back", True, BLACK)
            screen.blit(back_text, (back_button.x + 75, back_button.y + 10))

            py.display.flip()

    def menu_display(self):
        self.capture_background()
        font = py.font.Font(None, 50)
        buttons = {
            "RESUME": py.Rect(400, 200, 200, 60),
            "OPTION": py.Rect(400, 280, 200, 60),
            "QUIT": py.Rect(400, 360, 200, 60)
        }
        overlay = py.Surface(self.screen.get_size(), py.SRCALPHA)
        overlay.fill((0, 0, 0, 150))

        running = True
        while running:
            self.screen.blit(self.background, (0, 0))
            self.screen.blit(overlay, (0, 0))

            for text, rect in buttons.items():
                color = (200, 200, 200) if rect.collidepoint(py.mouse.get_pos()) else (255, 255, 255)
                py.draw.rect(self.screen, color, rect, border_radius=20)
                label = font.render(text, True, (0, 0, 0))
                self.screen.blit(label, (rect.x + (rect.width - label.get_width()) // 2, rect.y + 10))

            for text, rect in buttons.items():
                color = (200, 200, 200) if rect.collidepoint(py.mouse.get_pos()) else (255, 255, 255)
                py.draw.rect(self.screen, color, rect, border_radius=20)
                label = font.render(text, True, (0, 0, 0))
                self.screen.blit(label, (rect.x + (rect.width - label.get_width()) // 2, rect.y + 10))

            py.display.flip()

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
                                self.option_menu()
                            elif text == "RESUME":
                                running = False
