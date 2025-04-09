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
        self.selected_language = self.languages[1]

        # Add keyboard layout option
        self.keyboard_layout = "AZERTY"  # Default keyboard layout

        self.dropdown_expanded = False
        self.dragging_volume = False
        self.options_visible = False

        self.BUTTON_WIDTH = 200
        self.BUTTON_HEIGHT = 50
        self.KNOB_RADIUS = 8

        # Définir des rectangles initiaux, ils seront mis à jour plus tard
        self.slider_rect = py.Rect(50, 100, 200, 5)
        self.dropdown_rect = py.Rect(50, 150, 200, 30)
        self.keyboard_button_rect = py.Rect(50, 250, 200, 40)

        py.font.init()
        self.control_font = load_game_font(size=24)
        self.keyboard_font = load_game_font(size=20)
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
            "highlight": (255, 255, 255, 50),  # Couleur de surlignage semi-transparente
            "overlay": (0, 0, 0, 200),
            "dimmed": (255, 255, 255, 80)  # Couleur pour les options désactivées
        }

    def capture_background(self):
        self.original_background = self.screen.copy()

    def _get_centered_buttons(self, current_screen_size):
        buttons = {}

        if self.options_visible:
            # Centre le bouton "BACK"
            button_x = (current_screen_size[0] - self.BUTTON_WIDTH) // 2
            buttons["BACK"] = py.Rect(button_x, current_screen_size[1] - 90, self.BUTTON_WIDTH, self.BUTTON_HEIGHT)
        else:
            button_x = (current_screen_size[0] - self.BUTTON_WIDTH) // 2

            # Updated to include 2 more buttons (SAVE and LOAD)
            total_button_height = self.BUTTON_HEIGHT * 5  # Changed from 3 to 5
            total_spacing = 20 * 4  # Changed from 2 to 4
            total_content_height = total_button_height + total_spacing

            start_y = (current_screen_size[1] - total_content_height) // 2

            top_image = load_image("Opera_senza_titolo 1.png")
            bottom_image = load_image("Opera_senza_titolo 2.png")

            top_image_x = (current_screen_size[0] - top_image.get_width()) // 2
            top_image_y = start_y - top_image.get_height() - 20

            buttons["RESUME"] = py.Rect(button_x, start_y, self.BUTTON_WIDTH, self.BUTTON_HEIGHT)
            buttons["SAVE"] = py.Rect(button_x, start_y + self.BUTTON_HEIGHT + 20, self.BUTTON_WIDTH,
                                      self.BUTTON_HEIGHT)
            buttons["LOAD"] = py.Rect(button_x, start_y + (self.BUTTON_HEIGHT + 20) * 2, self.BUTTON_WIDTH,
                                      self.BUTTON_HEIGHT)
            buttons["OPTIONS"] = py.Rect(button_x, start_y + (self.BUTTON_HEIGHT + 20) * 3, self.BUTTON_WIDTH,
                                         self.BUTTON_HEIGHT)
            buttons["QUIT"] = py.Rect(button_x, start_y + (self.BUTTON_HEIGHT + 20) * 4, self.BUTTON_WIDTH,
                                      self.BUTTON_HEIGHT)

            bottom_image_x = (current_screen_size[0] - bottom_image.get_width()) // 2
            bottom_image_y = buttons["QUIT"].bottom + 10

            self.top_image = top_image
            self.bottom_image = bottom_image
            self.top_image_pos = (top_image_x, top_image_y)
            self.bottom_image_pos = (bottom_image_x, bottom_image_y)

        return buttons

    def _draw_buttons(self, buttons):
        # Ne pas traiter les clics sur les boutons si le dropdown est étendu
        if self.dropdown_expanded and self.options_visible:
            for text, rect in buttons.items():
                label = self.button_font.render(text, True, self.COLORS["dimmed"])
                text_width = label.get_width()
                text_height = label.get_height()
                text_x = rect.x + (rect.width - text_width) // 2
                text_y = rect.y + (rect.height - text_height) // 2
                self.screen.blit(label, (text_x, text_y))
            return

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

        # Ne pas afficher le contrôle du volume si le dropdown est étendu
        if self.dropdown_expanded:
            return 0

        mouse_pos = py.mouse.get_pos()
        is_hovered = self.slider_rect.collidepoint(mouse_pos) or \
                     py.Rect(self.slider_rect.x - 10, self.slider_rect.y - 10,
                             self.slider_rect.width + 20, self.slider_rect.height + 20).collidepoint(mouse_pos)

        # Dessiner le texte du titre
        vol_text = self.control_font.render("Volume:", True, self.COLORS["white"])
        self.screen.blit(vol_text, (self.slider_rect.x, self.slider_rect.centery - vol_text.get_height() // 2))

        # Calculer la position du slider après le texte
        slider_start_x = self.slider_rect.x + vol_text.get_width() + 20
        slider_width = self.slider_rect.width
        slider_y = self.slider_rect.centery

        # Mettre à jour la position du rectangle du slider
        self.slider_rect = py.Rect(slider_start_x, slider_y - 2, slider_width, 4)

        # Dessiner le fond du slider
        py.draw.rect(self.screen, self.COLORS["dark_gray"], self.slider_rect, border_radius=2)

        if is_hovered:
            highlight_rect = py.Rect(self.slider_rect.x - 5, self.slider_rect.y - 5,
                                     self.slider_rect.width + 10, self.slider_rect.height + 10)
            highlight_surface = py.Surface((highlight_rect.width, highlight_rect.height), py.SRCALPHA)
            py.draw.rect(highlight_surface, self.COLORS["highlight"],
                         (0, 0, highlight_rect.width, highlight_rect.height), border_radius=4)
            self.screen.blit(highlight_surface, (highlight_rect.x, highlight_rect.y))

        # Calculer la position du bouton
        knob_x = self.slider_rect.x + int(self.volume * self.slider_rect.width)
        py.draw.circle(self.screen, self.COLORS["white"],
                       (knob_x, self.slider_rect.centery),
                       self.KNOB_RADIUS)

        # Afficher le pourcentage à côté du slider
        percent_text = self.control_font.render(f"{int(self.volume * 100)}%", True, self.COLORS["white"])
        self.screen.blit(percent_text,
                         (self.slider_rect.right + 10, self.slider_rect.centery - percent_text.get_height() // 2))

        return knob_x

    def _draw_language_dropdown(self):
        if not self.options_visible:
            return []

        mouse_pos = py.mouse.get_pos()

        # Dessiner le texte du titre
        lang_title = self.control_font.render("Language:", True, self.COLORS["white"])
        self.screen.blit(lang_title, (self.dropdown_rect.x, self.dropdown_rect.centery - lang_title.get_height() // 2))

        # Calculer la position du dropdown après le texte
        dropdown_start_x = self.dropdown_rect.x + lang_title.get_width() + 20
        dropdown_width = self.dropdown_rect.width
        dropdown_y = self.dropdown_rect.y
        dropdown_height = self.dropdown_rect.height

        # Mettre à jour la position du rectangle du dropdown
        self.dropdown_rect = py.Rect(dropdown_start_x, dropdown_y, dropdown_width, dropdown_height)

        is_hovered = self.dropdown_rect.collidepoint(mouse_pos)

        if is_hovered:
            highlight_rect = py.Rect(self.dropdown_rect.x - 5, self.dropdown_rect.y - 5,
                                     self.dropdown_rect.width + 10, self.dropdown_rect.height + 10)
            highlight_surface = py.Surface((highlight_rect.width, highlight_rect.height), py.SRCALPHA)
            py.draw.rect(highlight_surface, self.COLORS["highlight"],
                         (0, 0, highlight_rect.width, highlight_rect.height), border_radius=4)
            self.screen.blit(highlight_surface, (highlight_rect.x, highlight_rect.y))

        # Dessiner le fond du dropdown avec des bords arrondis au lieu d'utiliser Surface
        py.draw.rect(self.screen, (70, 70, 70), self.dropdown_rect, border_radius=4)

        # Dessiner le texte de la langue sélectionnée
        lang_text = self.control_font.render(self.selected_language, True, self.COLORS["white"])
        text_x = self.dropdown_rect.x + (self.dropdown_rect.width - lang_text.get_width()) // 2
        text_y = self.dropdown_rect.centery - lang_text.get_height() // 2
        self.screen.blit(lang_text, (text_x, text_y))

        # Dessiner une petite flèche pour indiquer qu'il s'agit d'un menu déroulant
        arrow_points = [
            (self.dropdown_rect.right - 15, self.dropdown_rect.centery - 3),
            (self.dropdown_rect.right - 5, self.dropdown_rect.centery - 3),
            (self.dropdown_rect.right - 10, self.dropdown_rect.centery + 5)
        ]
        py.draw.polygon(self.screen, self.COLORS["white"], arrow_points)

        option_rects = []
        if self.dropdown_expanded:
            total_height = len(self.languages) * self.dropdown_rect.height
            dropdown_y = self.dropdown_rect.y + self.dropdown_rect.height

            # Dessiner directement le rectangle avec des bords arrondis
            py.draw.rect(self.screen, (50, 50, 50),
                         (self.dropdown_rect.x, dropdown_y, self.dropdown_rect.width, total_height),
                         border_radius=4)

            # Créer une liste pour stocker les rectangles des options
            option_rects = []

            # Dessiner chaque option
            for i, lang in enumerate(self.languages):
                option_rect = py.Rect(
                    self.dropdown_rect.x,
                    dropdown_y + i * self.dropdown_rect.height,
                    self.dropdown_rect.width,
                    self.dropdown_rect.height
                )
                option_rects.append(option_rect)

                is_option_hovered = option_rect.collidepoint(mouse_pos)

                if is_option_hovered:
                    py.draw.rect(self.screen, (80, 80, 80), option_rect, border_radius=4)
                    option_text = self.control_font.render(lang, True, (255, 255, 255))
                else:
                    option_text = self.control_font.render(lang, True, self.COLORS["white"])

                text_x = option_rect.x + (option_rect.width - option_text.get_width()) // 2
                text_y = option_rect.centery - option_text.get_height() // 2
                self.screen.blit(option_text, (text_x, text_y))

        return option_rects

    def _draw_keyboard_button(self):
        """Draw the AZERTY/QWERTY toggle button"""
        if not self.options_visible:
            return False

        if self.dropdown_expanded:
            return False

        mouse_pos = py.mouse.get_pos()

        keyboard_title = self.control_font.render("Keyboard Layout:", True, self.COLORS["white"])
        self.screen.blit(keyboard_title, (self.keyboard_button_rect.x,
                                          self.keyboard_button_rect.centery - keyboard_title.get_height() // 2))

        button_start_x = self.keyboard_button_rect.x + keyboard_title.get_width() + 20
        button_width = self.keyboard_button_rect.width
        button_y = self.keyboard_button_rect.y
        button_height = self.keyboard_button_rect.height

        self.keyboard_button_rect = py.Rect(button_start_x, button_y, button_width, button_height)

        is_hovered = self.keyboard_button_rect.collidepoint(mouse_pos)

        if is_hovered:
            highlight_rect = py.Rect(self.keyboard_button_rect.x - 5, self.keyboard_button_rect.y - 5,
                                     self.keyboard_button_rect.width + 10, self.keyboard_button_rect.height + 10)
            highlight_surface = py.Surface((highlight_rect.width, highlight_rect.height), py.SRCALPHA)
            py.draw.rect(highlight_surface, self.COLORS["highlight"],
                         (0, 0, highlight_rect.width, highlight_rect.height), border_radius=4)
            self.screen.blit(highlight_surface, (highlight_rect.x, highlight_rect.y))

        # Dessiner le fond du bouton
        keyboard_bg = py.Surface((button_width, button_height), py.SRCALPHA)
        py.draw.rect(keyboard_bg, (70, 70, 70, 200), (0, 0, button_width, button_height), border_radius=4)
        self.screen.blit(keyboard_bg, (self.keyboard_button_rect.x, self.keyboard_button_rect.y))

        # Dessiner le texte du bouton
        button_text = self.keyboard_font.render(self.keyboard_layout, True, self.COLORS["white"])
        text_x = self.keyboard_button_rect.x + (self.keyboard_button_rect.width - button_text.get_width()) // 2
        text_y = self.keyboard_button_rect.centery - button_text.get_height() // 2
        self.screen.blit(button_text, (text_x, text_y))

        return is_hovered

    def _handle_button_click(self, buttons, mouse_pos):
        # Ne pas réagir aux clics si le dropdown est étendu
        if self.dropdown_expanded and self.options_visible:
            return True

        for text, rect in buttons.items():
            if rect.collidepoint(mouse_pos):
                if text == "RESUME":
                    return False
                elif text == "SAVE":
                    # Ouvrir le menu de sauvegarde
                    self.save_menu()
                    return True
                elif text == "LOAD":
                    # Ouvrir le menu de chargement
                    self.load_menu()
                    return True
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
        if not self.options_visible or self.dropdown_expanded:
            return False

        knob_area = py.Rect(
            knob_x - self.KNOB_RADIUS,
            self.slider_rect.y - self.KNOB_RADIUS,
            self.KNOB_RADIUS * 2,
            self.KNOB_RADIUS * 2
        )

        if knob_area.collidepoint(mouse_pos) or self.slider_rect.collidepoint(mouse_pos):
            if self.slider_rect.collidepoint(mouse_pos):
                volume = (mouse_pos[0] - self.slider_rect.x) / self.slider_rect.width
                volume = max(0, min(1, volume))
                self.game.set_volume(volume)  # <-- On applique à la classe Game
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
                # Cliquer en dehors des options fermera le dropdown
                self.dropdown_expanded = False

    def _handle_keyboard_click(self, mouse_pos):
        if not self.options_visible or self.dropdown_expanded:
            return False

        if self.keyboard_button_rect.collidepoint(mouse_pos):
            # Toggle between AZERTY and QWERTY
            self.keyboard_layout = "QWERTY" if self.keyboard_layout == "AZERTY" else "AZERTY"

            # Mettre à jour également la disposition dans la classe Game
            self.game.keyboard_layout = self.keyboard_layout.lower()  # Convertir en minuscules pour correspondre à get_key_map

            return True

        return False

    def _handle_volume_drag(self, mouse_x):
        if not self.options_visible or self.dropdown_expanded:
            return

        constrained_x = max(self.slider_rect.left, min(mouse_x, self.slider_rect.right))

        self.volume = (constrained_x - self.slider_rect.x) / self.slider_rect.width
        self.volume = max(0, min(1, self.volume))
        self.game.set_volume(self.volume)


    def _update_options_positions(self, current_screen_size):
        # Positions centrées
        control_x = (current_screen_size[0] - 300) // 2
        panel_y = 50

        # Espacer les contrôles verticalement
        control_spacing = 60

        # Mettre à jour les positions des contrôles
        self.slider_rect = py.Rect(control_x, panel_y + 100, 200, 5)
        self.dropdown_rect = py.Rect(control_x, panel_y + 100 + control_spacing, 200, 30)
        self.keyboard_button_rect = py.Rect(control_x, panel_y + 100 + control_spacing * 2, 200, 40)

    def _draw_options_panel(self, current_screen_size):
        if not self.options_visible:
            return

        self._update_options_positions(current_screen_size)

        # Afficher le titre des options (rendre semi-transparent si le dropdown est étendu)
        options_title_color = self.COLORS["dimmed"] if self.dropdown_expanded else self.COLORS["white"]
        options_title = self.button_font.render("OPTIONS", True, options_title_color)
        self.screen.blit(options_title, (
            (current_screen_size[0] - options_title.get_width()) // 2,
            50
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

            # Afficher le panneau d'options si nécessaire
            if self.options_visible:
                self._draw_options_panel(current_screen_size)

            buttons = self._get_centered_buttons(current_screen_size)

            if not self.options_visible:
                if hasattr(self, 'bottom_image'):
                    self.screen.blit(self.top_image, self.bottom_image_pos)
                if hasattr(self, 'top_image'):
                    self.screen.blit(self.bottom_image, self.top_image_pos)

            self._draw_buttons(buttons)

            # Dessiner les contrôles dans l'ordre : d'abord le volume et le clavier
            # puis le dropdown des langues (qui sera au-dessus si ouvert)
            knob_x = self._draw_volume_control()
            self._draw_keyboard_button()
            option_rects = self._draw_language_dropdown()  # Dessiner le dropdown en dernier

            py.display.flip()

            for event in py.event.get():
                if event.type == py.QUIT:
                    py.quit()
                    sys.exit()

                elif event.type == py.VIDEORESIZE:
                    self.screen = py.display.set_mode((event.w, event.h), py.RESIZABLE)

                elif event.type == py.KEYDOWN:
                    if event.key == py.K_ESCAPE:
                        if self.dropdown_expanded:
                            self.dropdown_expanded = False
                        elif self.options_visible:
                            self.options_visible = False
                        else:
                            running = False

                elif event.type == py.MOUSEBUTTONDOWN:
                    mouse_pos = event.pos

                    # Si le dropdown est étendu, ne traiter que les clics liés au dropdown
                    if self.dropdown_expanded and self.options_visible:
                        self._handle_language_click(option_rects, mouse_pos)
                    else:
                        running = self._handle_button_click(buttons, mouse_pos)
                        if self.options_visible:
                            self.dragging_volume = self._handle_volume_click(knob_x, mouse_pos)
                            self._handle_language_click(option_rects, mouse_pos)
                            self._handle_keyboard_click(mouse_pos)

                elif event.type == py.MOUSEBUTTONUP:
                    self.dragging_volume = False

                elif event.type == py.MOUSEMOTION and self.dragging_volume and not self.dropdown_expanded:
                    self._handle_volume_drag(event.pos[0])

    def save_menu(self):
        """Affiche le menu de sauvegarde"""
        # Capture l'écran actuel
        current_screen = self.screen.copy()

        # Récupère la liste des sauvegardes existantes
        saves = self.game.save_system.list_saves()

        # Configure les slots de sauvegarde (1 à 3)
        slots = [1, 2, 3]
        save_rects = {}

        # Trouve quels slots sont déjà utilisés
        used_slots = {save["slot"]: save for save in saves}

        menu_running = True
        while menu_running:
            # Affiche l'écran de fond avec une superposition semi-transparente
            self.screen.blit(current_screen, (0, 0))
            overlay = py.Surface(self.screen.get_size(), py.SRCALPHA)
            overlay.fill((0, 0, 0, 200))  # Fond semi-transparent
            self.screen.blit(overlay, (0, 0))

            # Affiche le titre
            title = self.button_font.render("SAVE GAME", True, self.COLORS["white"])
            title_x = (self.screen.get_width() - title.get_width()) // 2
            self.screen.blit(title, (title_x, 50))

            # Affiche les slots de sauvegarde
            slot_y = 120
            slot_height = 80
            slot_width = 300
            spacing = 20

            for slot in slots:
                slot_rect = py.Rect(
                    (self.screen.get_width() - slot_width) // 2,
                    slot_y,
                    slot_width,
                    slot_height
                )
                save_rects[slot] = slot_rect

                # Vérifie si le slot est utilisé
                is_used = slot in used_slots
                slot_color = (60, 60, 100) if is_used else (60, 60, 60)

                # Dessine le fond du slot
                py.draw.rect(self.screen, slot_color, slot_rect, border_radius=5)

                # Dessine le texte du slot
                if is_used:
                    save_data = used_slots[slot]
                    # Format du texte: "Slot X - Date - HP: XX"
                    slot_text = f"Slot {slot} - {save_data['date']}"
                    hp_text = f"HP: {save_data['player_hp']} - Enemies: {save_data['enemy_count']}"

                    slot_label = self.control_font.render(slot_text, True, self.COLORS["white"])
                    hp_label = self.control_font.render(hp_text, True, self.COLORS["white"])

                    self.screen.blit(slot_label, (slot_rect.x + 10, slot_rect.y + 10))
                    self.screen.blit(hp_label, (slot_rect.x + 10, slot_rect.y + 40))
                else:
                    slot_text = f"Slot {slot} - Empty"
                    slot_label = self.control_font.render(slot_text, True, self.COLORS["white"])
                    self.screen.blit(slot_label,
                                     (slot_rect.x + 10, slot_rect.y + (slot_height - slot_label.get_height()) // 2))

                slot_y += slot_height + spacing

            # Bouton Retour
            back_rect = py.Rect(
                (self.screen.get_width() - 200) // 2,
                slot_y + 20,
                200,
                50
            )
            py.draw.rect(self.screen, (80, 80, 80), back_rect, border_radius=5)
            back_text = self.button_font.render("BACK", True, self.COLORS["white"])
            back_x = back_rect.x + (back_rect.width - back_text.get_width()) // 2
            back_y = back_rect.y + (back_rect.height - back_text.get_height()) // 2
            self.screen.blit(back_text, (back_x, back_y))

            py.display.flip()

            # Gestion des événements
            for event in py.event.get():
                if event.type == py.QUIT:
                    py.quit()
                    sys.exit()
                elif event.type == py.KEYDOWN:
                    if event.key == py.K_ESCAPE:
                        menu_running = False
                elif event.type == py.MOUSEBUTTONDOWN:
                    mouse_pos = event.pos

                    # Vérifie si un slot a été cliqué
                    for slot, rect in save_rects.items():
                        if rect.collidepoint(mouse_pos):
                            # Sauvegarde dans ce slot
                            if self.game.save_game(slot):
                                # Rafraîchit la liste des sauvegardes
                                saves = self.game.save_system.list_saves()
                                used_slots = {save["slot"]: save for save in saves}

                    # Vérifie si le bouton Retour a été cliqué
                    if back_rect.collidepoint(mouse_pos):
                        menu_running = False

    def load_menu(self):
        """Affiche le menu de chargement"""
        # Capture l'écran actuel
        current_screen = self.screen.copy()

        # Récupère la liste des sauvegardes existantes
        saves = self.game.save_system.list_saves()

        # S'il n'y a pas de sauvegardes, affiche un message
        if not saves:
            no_saves_menu = True
            while no_saves_menu:
                self.screen.blit(current_screen, (0, 0))
                overlay = py.Surface(self.screen.get_size(), py.SRCALPHA)
                overlay.fill((0, 0, 0, 200))
                self.screen.blit(overlay, (0, 0))

                message = self.button_font.render("No saves found", True, self.COLORS["white"])
                msg_x = (self.screen.get_width() - message.get_width()) // 2
                msg_y = (self.screen.get_height() - message.get_height()) // 2
                self.screen.blit(message, (msg_x, msg_y))

                back_rect = py.Rect(
                    (self.screen.get_width() - 200) // 2,
                    msg_y + 80,
                    200,
                    50
                )
                py.draw.rect(self.screen, (80, 80, 80), back_rect, border_radius=5)
                back_text = self.button_font.render("BACK", True, self.COLORS["white"])
                back_x = back_rect.x + (back_rect.width - back_text.get_width()) // 2
                back_y = back_rect.y + (back_rect.height - back_text.get_height()) // 2
                self.screen.blit(back_text, (back_x, back_y))

                py.display.flip()

                for event in py.event.get():
                    if event.type == py.QUIT:
                        py.quit()
                        sys.exit()
                    elif event.type == py.KEYDOWN:
                        if event.key == py.K_ESCAPE:
                            no_saves_menu = False
                    elif event.type == py.MOUSEBUTTONDOWN:
                        if back_rect.collidepoint(event.pos):
                            no_saves_menu = False
            return

        # Prépare les rectangles pour chaque sauvegarde
        save_rects = {}

        menu_running = True
        while menu_running:
            self.screen.blit(current_screen, (0, 0))
            overlay = py.Surface(self.screen.get_size(), py.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            self.screen.blit(overlay, (0, 0))

            # Affiche le titre
            title = self.button_font.render("LOAD GAME", True, self.COLORS["white"])
            title_x = (self.screen.get_width() - title.get_width()) // 2
            self.screen.blit(title, (title_x, 50))

            # Affiche les sauvegardes disponibles
            save_y = 120
            save_height = 80
            save_width = 300
            spacing = 20

            for save in saves:
                save_rect = py.Rect(
                    (self.screen.get_width() - save_width) // 2,
                    save_y,
                    save_width,
                    save_height
                )
                save_rects[save["slot"]] = save_rect

                # Dessine le fond de la sauvegarde
                py.draw.rect(self.screen, (60, 80, 100), save_rect, border_radius=5)

                # Dessine les informations de la sauvegarde
                slot_text = f"Slot {save['slot']} - {save['date']}"
                hp_text = f"HP: {save['player_hp']} - Enemies: {save['enemy_count']}"

                slot_label = self.control_font.render(slot_text, True, self.COLORS["white"])
                hp_label = self.control_font.render(hp_text, True, self.COLORS["white"])

                self.screen.blit(slot_label, (save_rect.x + 10, save_rect.y + 10))
                self.screen.blit(hp_label, (save_rect.x + 10, save_rect.y + 40))

                save_y += save_height + spacing

            # Bouton Retour
            back_rect = py.Rect(
                (self.screen.get_width() - 200) // 2,
                save_y + 20,
                200,
                50
            )
            py.draw.rect(self.screen, (80, 80, 80), back_rect, border_radius=5)
            back_text = self.button_font.render("BACK", True, self.COLORS["white"])
            back_x = back_rect.x + (back_rect.width - back_text.get_width()) // 2
            back_y = back_rect.y + (back_rect.height - back_text.get_height()) // 2
            self.screen.blit(back_text, (back_x, back_y))

            py.display.flip()

            # Gestion des événements
            for event in py.event.get():
                if event.type == py.QUIT:
                    py.quit()
                    sys.exit()
                elif event.type == py.KEYDOWN:
                    if event.key == py.K_ESCAPE:
                        menu_running = False
                elif event.type == py.MOUSEBUTTONDOWN:
                    mouse_pos = event.pos

                    # Vérifie si une sauvegarde a été cliquée
                    for slot, rect in save_rects.items():
                        if rect.collidepoint(mouse_pos):
                            # Charge cette sauvegarde
                            if self.game.load_game(slot):
                                menu_running = False

                    # Vérifie si le bouton Retour a été cliqué
                    if back_rect.collidepoint(mouse_pos):
                        menu_running = False

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