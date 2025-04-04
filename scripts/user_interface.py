import pygame as py
import sys
import numpy as np
import cv2
import os
from scripts.sound import run_sound
from scripts.utils import load_images, load_image, load_game_font


class Menu:

    def __init__(self, game):
        self.game = game
        self.screen = game.screen
        self.original_background = None

        self.volume = 0.5
        self.languages = ["Français", "English", "Español"]
        self.selected_language = self.languages[0]

        # Add keyboard layout option
        self.keyboard_layout = "AZERTY"  # Default keyboard layout

        self.dropdown_expanded = False
        self.dragging_volume = False
        self.options_visible = False

        self.BUTTON_WIDTH = 200
        self.BUTTON_HEIGHT = 50
        self.KNOB_RADIUS = 8

        self.slider_rect = py.Rect(50, 100, 200, 5)
        self.dropdown_rect = py.Rect(50, 150, 200, 30)
        # Add keyboard toggle button rect - initial position, will be updated later
        self.keyboard_button_rect = py.Rect(50, 250, 200, 40)

        py.font.init()
        self.control_font = load_game_font(size=24)
        self.keyboard_font = load_game_font(size=20)  # Smaller font for keyboard button
        self.button_font = load_game_font(size=36)
        self.hover_image = load_image("Opera_senza_titolo.png")
        self.hover2_image = py.transform.flip(load_image("Opera_senza_titolo.png"), True, False)

        self.button_font.set_bold(True)

        self.COLORS = {
            "white": (255, 255, 255),
            "black": (0, 0, 0),
            "light_gray": (220, 220, 220),
            "medium_gray": (200, 200, 200),
            "dark_gray": (160, 160, 160),
            "overlay": (0, 0, 0, 200)
        }

    def capture_background(self):
        self.original_background = self.screen.copy()

    def _get_centered_buttons(self, current_screen_size):
        buttons = {}

        if self.options_visible:
            buttons["BACK"] = py.Rect(70, current_screen_size[1] - 90, self.BUTTON_WIDTH, self.BUTTON_HEIGHT)
        else:
            button_x = (current_screen_size[0] - self.BUTTON_WIDTH) // 2

            total_button_height = self.BUTTON_HEIGHT * 3
            total_spacing = 20 * 2
            total_content_height = total_button_height + total_spacing

            start_y = (current_screen_size[1] - total_content_height) // 2

            top_image = load_image("Opera_senza_titolo 1.png")
            bottom_image = load_image("Opera_senza_titolo 2.png")

            top_image_x = (current_screen_size[0] - top_image.get_width()) // 2
            top_image_y = start_y - top_image.get_height() - 20

            buttons["RESUME"] = py.Rect(button_x, start_y, self.BUTTON_WIDTH, self.BUTTON_HEIGHT)
            buttons["OPTIONS"] = py.Rect(button_x, start_y + self.BUTTON_HEIGHT + 20, self.BUTTON_WIDTH,
                                         self.BUTTON_HEIGHT)
            buttons["QUIT"] = py.Rect(button_x, start_y + (self.BUTTON_HEIGHT + 20) * 2, self.BUTTON_WIDTH,
                                      self.BUTTON_HEIGHT)

            bottom_image_x = (current_screen_size[0] - bottom_image.get_width()) // 2
            bottom_image_y = buttons["QUIT"].bottom + 10

            self.top_image = top_image
            self.bottom_image = bottom_image
            self.top_image_pos = (top_image_x, top_image_y)
            self.bottom_image_pos = (bottom_image_x, bottom_image_y)

        return buttons

    def _draw_buttons(self, buttons):
        mouse_pos = py.mouse.get_pos()
        for text, rect in buttons.items():
            label = self.button_font.render(text, True, self.COLORS["light_gray"])
            text_width = label.get_width()
            text_height = label.get_height()

            text_color = self.COLORS["light_gray"]

            if rect.collidepoint(mouse_pos):
                text_color = (255, 255, 255)

            text_x = rect.x + (rect.width - text_width) // 2
            text_y = rect.y + (rect.height - text_height) // 2

            label = self.button_font.render(text, True, text_color)
            self.screen.blit(label, (text_x, text_y))

            if rect.collidepoint(mouse_pos):
                image_x = text_x - self.hover_image.get_width() - 5
                image_y = rect.y + (rect.height - self.hover_image.get_height()) // 2
                self.screen.blit(self.hover_image, (image_x, image_y))

                image_x2 = text_x + text_width + 5
                image_y2 = rect.y + (rect.height - self.hover2_image.get_height()) // 2
                self.screen.blit(self.hover2_image, (image_x2, image_y2))

    def _draw_volume_control(self):

        if not self.options_visible:
            return 0

        knob_x = self.slider_rect.x + int(self.volume * self.slider_rect.width)

        py.draw.rect(self.screen, self.COLORS["dark_gray"], self.slider_rect, border_radius=2)
        py.draw.circle(self.screen, self.COLORS["white"],
                       (knob_x, self.slider_rect.centery),
                       self.KNOB_RADIUS)

        vol_text = self.control_font.render(f"Volume: {int(self.volume * 100)}%", True, self.COLORS["white"])
        self.screen.blit(vol_text, (self.slider_rect.x, self.slider_rect.y - 25))

        return knob_x

    def _draw_language_dropdown(self):

        if not self.options_visible:
            return []

        py.draw.rect(self.screen, self.COLORS["dark_gray"], self.dropdown_rect, border_radius=5)
        lang_text = self.control_font.render(self.selected_language, True, self.COLORS["black"])
        self.screen.blit(lang_text, (self.dropdown_rect.x + 10, self.dropdown_rect.y + 5))

        lang_title = self.control_font.render("Language:", True, self.COLORS["white"])
        self.screen.blit(lang_title, (self.dropdown_rect.x, self.dropdown_rect.y - 25))

        if self.dropdown_expanded:
            option_rects = []
            for i, lang in enumerate(self.languages):
                option_rect = py.Rect(
                    self.dropdown_rect.x,
                    self.dropdown_rect.y + (i + 1) * self.dropdown_rect.height,
                    self.dropdown_rect.width,
                    self.dropdown_rect.height
                )
                option_rects.append(option_rect)

                color = self.COLORS["medium_gray"] if option_rect.collidepoint(py.mouse.get_pos()) else self.COLORS[
                    "light_gray"]

                py.draw.rect(self.screen, color, option_rect, border_radius=5)
                option_text = self.control_font.render(lang, True, self.COLORS["black"])
                self.screen.blit(option_text, (option_rect.x + 10, option_rect.y + 5))

            return option_rects
        return []

    def _draw_keyboard_button(self):
        """Draw the AZERTY/QWERTY toggle button"""
        if not self.options_visible:
            return False

        mouse_pos = py.mouse.get_pos()
        is_hovered = self.keyboard_button_rect.collidepoint(mouse_pos)

        # Draw button background
        button_color = self.COLORS["medium_gray"] if is_hovered else self.COLORS["dark_gray"]
        py.draw.rect(self.screen, button_color, self.keyboard_button_rect, border_radius=5)

        # Draw button text with smaller font
        button_text = self.keyboard_font.render(f"Keyboard: {self.keyboard_layout}", True, self.COLORS["black"])
        text_x = self.keyboard_button_rect.x + 5
        text_y = self.keyboard_button_rect.y + (self.keyboard_button_rect.height - button_text.get_height()) // 2
        self.screen.blit(button_text, (text_x, text_y))

        # Draw label
        keyboard_title = self.control_font.render("Keyboard Layout:", True, self.COLORS["white"])
        self.screen.blit(keyboard_title, (self.keyboard_button_rect.x, self.keyboard_button_rect.y - 25))

        return is_hovered

    def _handle_button_click(self, buttons, mouse_pos):
        for text, rect in buttons.items():
            if rect.collidepoint(mouse_pos):
                if text == "RESUME":
                    return False
                elif text == "OPTIONS":
                    self.options_visible = True
                    return True
                elif text == "QUIT":
                    py.quit()
                    sys.exit()
                elif text == "BACK":
                    self.options_visible = False
                    return True
        return True

    def _handle_volume_click(self, knob_x, mouse_pos):

        if not self.options_visible:
            return False

        knob_area = py.Rect(
            knob_x - self.KNOB_RADIUS,
            self.slider_rect.y,
            self.KNOB_RADIUS * 2,
            self.slider_rect.height
        )

        if knob_area.collidepoint(mouse_pos) or self.slider_rect.collidepoint(mouse_pos):
            if self.slider_rect.collidepoint(mouse_pos):
                self.volume = (mouse_pos[0] - self.slider_rect.x) / self.slider_rect.width
                self.volume = max(0, min(1, self.volume))
            return True
        return False

    def _handle_language_click(self, option_rects, mouse_pos):

        if not self.options_visible:
            return

        if self.dropdown_rect.collidepoint(mouse_pos):
            self.dropdown_expanded = not self.dropdown_expanded
        elif self.dropdown_expanded:
            for i, option_rect in enumerate(option_rects):
                if option_rect.collidepoint(mouse_pos):
                    self.selected_language = self.languages[i]
                    self.dropdown_expanded = False
                    break
            else:
                self.dropdown_expanded = False

    def _handle_keyboard_click(self, mouse_pos):
        if not self.options_visible:
            return False

        if self.keyboard_button_rect.collidepoint(mouse_pos):
            # Toggle between AZERTY and QWERTY
            self.keyboard_layout = "QWERTY" if self.keyboard_layout == "AZERTY" else "AZERTY"

            # Mettre à jour également la disposition dans la classe Game
            self.game.keyboard_layout = self.keyboard_layout.lower()  # Convertir en minuscules pour correspondre à get_key_map

            return True

        return False

    def _handle_volume_drag(self, mouse_x):

        if not self.options_visible:
            return

        constrained_x = max(self.slider_rect.left, min(mouse_x, self.slider_rect.right))

        self.volume = (constrained_x - self.slider_rect.x) / self.slider_rect.width
        self.volume = max(0, min(1, self.volume))

    def _update_options_positions(self, current_screen_size):

        panel_width = 250
        panel_height = current_screen_size[1] - 100
        panel_x = 50
        panel_y = 50

        control_x = panel_x + 25
        self.slider_rect = py.Rect(control_x, panel_y + 100, 200, 5)
        self.dropdown_rect = py.Rect(control_x, panel_y + 200, 200, 30)

        # Calculate max dropdown height when expanded
        dropdown_expanded_height = len(self.languages) * self.dropdown_rect.height

        # Position keyboard button below dropdown with enough space to avoid collision
        keyboard_y = self.dropdown_rect.y + dropdown_expanded_height + 70  # Add padding to avoid collision
        self.keyboard_button_rect = py.Rect(control_x, keyboard_y, 200, 40)

        return panel_x, panel_y, panel_width, panel_height

    def _draw_options_panel(self, current_screen_size):
        if not self.options_visible:
            return

        panel_x, panel_y, panel_width, panel_height = self._update_options_positions(current_screen_size)

        panel_surface = py.Surface((panel_width, panel_height), py.SRCALPHA)

        panel_color = (20, 20, 20, 200)

        py.draw.rect(panel_surface, panel_color, (0, 0, panel_width, panel_height), border_radius=10)

        self.screen.blit(panel_surface, (panel_x, panel_y))

        options_title = self.button_font.render("OPTIONS", True, self.COLORS["white"])
        self.screen.blit(options_title, (
            panel_x + (panel_width - options_title.get_width()) // 2,
            panel_y + 20
        ))

    def menu_display(self):

        self.capture_background()

        running = True
        while running:
            current_screen_size = self.screen.get_size()

            if self.original_background is not None:
                scaled_bg = py.transform.scale(self.original_background, current_screen_size)
                self.screen.blit(scaled_bg, (0, 0))
            else:
                self.screen.fill(self.COLORS["black"])

            overlay = py.Surface(current_screen_size, py.SRCALPHA)
            overlay.fill(self.COLORS["overlay"])
            self.screen.blit(overlay, (0, 0))

            if self.options_visible:
                self._draw_options_panel(current_screen_size)

            buttons = self._get_centered_buttons(current_screen_size)

            if not self.options_visible:
                if hasattr(self, 'bottom_image'):
                    self.screen.blit(self.top_image, self.bottom_image_pos)
                if hasattr(self, 'top_image'):
                    self.screen.blit(self.bottom_image, self.top_image_pos)

            self._draw_buttons(buttons)

            knob_x = self._draw_volume_control()
            option_rects = self._draw_language_dropdown()
            # Draw the keyboard layout toggle button
            self._draw_keyboard_button()

            py.display.flip()

            for event in py.event.get():
                if event.type == py.QUIT:
                    py.quit()
                    sys.exit()

                elif event.type == py.VIDEORESIZE:
                    self.screen = py.display.set_mode((event.w, event.h), py.RESIZABLE)

                elif event.type == py.KEYDOWN:
                    if event.key == py.K_ESCAPE:
                        if self.options_visible:
                            self.options_visible = False
                        else:
                            running = False

                elif event.type == py.MOUSEBUTTONDOWN:
                    mouse_pos = event.pos
                    running = self._handle_button_click(buttons, mouse_pos)

                    if self.options_visible:
                        self.dragging_volume = self._handle_volume_click(knob_x, mouse_pos)
                        self._handle_language_click(option_rects, mouse_pos)
                        # Handle keyboard button click
                        self._handle_keyboard_click(mouse_pos)

                elif event.type == py.MOUSEBUTTONUP:
                    self.dragging_volume = False

                elif event.type == py.MOUSEMOTION and self.dragging_volume:
                    self._handle_volume_drag(event.pos[0])

def start_menu():
    py.init()
    screen = py.display.set_mode((1000, 600), py.NOFRAME)
    font = py.font.Font(None, 24)
    font.set_italic(True)
    text = font.render("Click anywhere to start", True, (255, 255, 255))
    text_rect = text.get_rect(center=(500, 580))

    cap = cv2.VideoCapture("assets/images/start_video.mp4")
    frame_id = -5
    running = True
    sound_running = False
    while running:
        ret, frame = cap.read()
        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_id)
            continue

        frame = cv2.flip(frame, 1)
        frame = cv2.resize(frame, (1000, 600))
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = np.rot90(frame)
        frame = py.surfarray.make_surface(frame)

        screen.blit(frame, (0, 0))
        screen.blit(text, text_rect)

        for event in py.event.get():
            if event.type == py.QUIT:
                running = False
            elif event.type == py.MOUSEBUTTONDOWN:
                running = False
        if not sound_running:
            run_sound(
                "assets/sounds/GV2space-ambient-music-interstellar-space-journey-8wlwxmjrzj8_MDWW6nat.wav")
            sound_running = True

        py.display.flip()
        py.time.wait(50)

    cap.release()
    py.quit()