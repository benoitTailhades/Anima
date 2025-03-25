import pygame as py
import sys
import numpy as np
import cv2
from scripts.utils import load_images


class Menu:
    """
    Classe qui gère le menu du jeu avec des options comme la reprise,
    les options (volume, langue) et la possibilité de quitter.
    """

    def __init__(self, game):
        self.game = game
        self.screen = game.screen
        self.original_background = None

        # Paramètres utilisateur
        self.volume = 0.5
        self.languages = ["Français", "English", "Español"]
        self.selected_language = self.languages[0]

        # États
        self.dropdown_expanded = False
        self.dragging_volume = False
        self.options_visible = False

        # Constantes
        self.BUTTON_WIDTH = 200
        self.BUTTON_HEIGHT = 50
        self.KNOB_RADIUS = 8

        # Position des éléments d'options (initialisés avec des valeurs par défaut)
        self.slider_rect = py.Rect(50, 100, 200, 5)
        self.dropdown_rect = py.Rect(50, 150, 200, 30)

        # Initialisation de la police
        py.font.init()
        self.control_font = py.font.Font(None, 24)
        self.button_font = py.font.Font(None, 36)

        # Couleurs
        self.COLORS = {
            "white": (255, 255, 255),
            "black": (0, 0, 0),
            "light_gray": (220, 220, 220),
            "medium_gray": (200, 200, 200),
            "dark_gray": (160, 160, 160),
            "overlay": (0, 0, 0, 150)
        }

    def capture_background(self):
        """Capture l'écran actuel comme arrière-plan du menu"""
        self.original_background = self.screen.copy()

    def _get_centered_buttons(self, current_screen_size):

        buttons = {}

        # Si les options sont visibles, ne pas afficher les autres boutons
        if self.options_visible:
            # Bouton RETOUR placé en bas à gauche du panneau d'options
            buttons["RETOUR"] = py.Rect(50, current_screen_size[1] - 80, self.BUTTON_WIDTH, self.BUTTON_HEIGHT)
        else:
            # Affichage normal des boutons centrés
            button_x = (current_screen_size[0] - self.BUTTON_WIDTH) // 2

            buttons["RESUME"] = py.Rect(button_x, 150, self.BUTTON_WIDTH, self.BUTTON_HEIGHT)
            buttons["OPTIONS"] = py.Rect(button_x, 210, self.BUTTON_WIDTH, self.BUTTON_HEIGHT)
            buttons["QUIT"] = py.Rect(button_x, 270, self.BUTTON_WIDTH, self.BUTTON_HEIGHT)

        return buttons

    def _draw_buttons(self, buttons):
        """
        Dessine les boutons du menu.

        Args:
            buttons: Dictionnaire des boutons à dessiner
        """
        for text, rect in buttons.items():
            # Couleur du bouton (plus claire si survolé)
            color = self.COLORS["medium_gray"] if rect.collidepoint(py.mouse.get_pos()) else self.COLORS["white"]

            # Dessiner le bouton et son texte
            py.draw.rect(self.screen, color, rect, border_radius=10)
            label = self.button_font.render(text, True, self.COLORS["black"])
            self.screen.blit(label, (
                rect.x + (rect.width - label.get_width()) // 2,
                rect.y + (rect.height - label.get_height()) // 2
            ))

    def _draw_volume_control(self):

        if not self.options_visible:
            return 0

        # Calcul de la position du bouton
        knob_x = self.slider_rect.x + int(self.volume * self.slider_rect.width)

        # Dessiner le slider et le bouton
        py.draw.rect(self.screen, self.COLORS["dark_gray"], self.slider_rect, border_radius=2)
        py.draw.circle(self.screen, self.COLORS["white"],
                       (knob_x, self.slider_rect.centery),
                       self.KNOB_RADIUS)

        # Afficher le texte du volume
        vol_text = self.control_font.render(f"Volume: {int(self.volume * 100)}%", True, self.COLORS["white"])
        self.screen.blit(vol_text, (self.slider_rect.x, self.slider_rect.y - 25))

        return knob_x

    def _draw_language_dropdown(self):
        """
        Dessine le menu déroulant de sélection de langue si les options sont visibles.

        Returns:
            list: Liste des rectangles des options de langue, vide si le menu n'est pas ouvert
        """
        if not self.options_visible:
            return []

        # Dessiner le menu déroulant principal
        py.draw.rect(self.screen, self.COLORS["dark_gray"], self.dropdown_rect, border_radius=5)
        lang_text = self.control_font.render(self.selected_language, True, self.COLORS["black"])
        self.screen.blit(lang_text, (self.dropdown_rect.x + 10, self.dropdown_rect.y + 5))

        # Afficher le titre "Language"
        lang_title = self.control_font.render("Language:", True, self.COLORS["white"])
        self.screen.blit(lang_title, (self.dropdown_rect.x, self.dropdown_rect.y - 25))

        # Si le menu est ouvert, afficher les options
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

                # Couleur de l'option (plus claire si survolée)
                color = self.COLORS["medium_gray"] if option_rect.collidepoint(py.mouse.get_pos()) else self.COLORS[
                    "light_gray"]

                # Dessiner l'option et son texte
                py.draw.rect(self.screen, color, option_rect, border_radius=5)
                option_text = self.control_font.render(lang, True, self.COLORS["black"])
                self.screen.blit(option_text, (option_rect.x + 10, option_rect.y + 5))

            return option_rects
        return []

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
                elif text == "RETOUR":
                    self.options_visible = False
                    return True
        return True

    def _handle_volume_click(self, knob_x, mouse_pos):
        """
        Gère les clics sur le contrôle de volume.

        Args:
            knob_x: Position X du bouton de volume
            mouse_pos: Position de la souris lors du clic

        Returns:
            bool: True si l'utilisateur a commencé à faire glisser le bouton
        """
        if not self.options_visible:
            return False

        knob_area = py.Rect(
            knob_x - self.KNOB_RADIUS,
            self.slider_rect.y,
            self.KNOB_RADIUS * 2,
            self.slider_rect.height
        )

        if knob_area.collidepoint(mouse_pos) or self.slider_rect.collidepoint(mouse_pos):
            # Si clic sur le slider, déplacer directement le volume
            if self.slider_rect.collidepoint(mouse_pos):
                self.volume = (mouse_pos[0] - self.slider_rect.x) / self.slider_rect.width
                self.volume = max(0, min(1, self.volume))
            return True
        return False

    def _handle_language_click(self, option_rects, mouse_pos):
        """
        Gère les clics sur le menu déroulant des langues.

        Args:
            option_rects: Liste des rectangles des options
            mouse_pos: Position de la souris lors du clic
        """
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
                # Clic en dehors des options, on ferme le menu
                self.dropdown_expanded = False

    def _handle_volume_drag(self, mouse_x):
        """
        Gère le glissement du bouton de volume.

        Args:
            mouse_x: Position X de la souris
        """
        if not self.options_visible:
            return

        # Limiter la position X entre le début et la fin du slider
        constrained_x = max(self.slider_rect.left, min(mouse_x, self.slider_rect.right))

        # Mettre à jour le volume (valeur entre 0 et 1)
        self.volume = (constrained_x - self.slider_rect.x) / self.slider_rect.width
        self.volume = max(0, min(1, self.volume))  # S'assurer que le volume reste entre 0 et 1

    def _update_options_positions(self, current_screen_size):
        """
        Met à jour les positions des éléments d'options en fonction de la taille de l'écran.

        Args:
            current_screen_size: Taille actuelle de l'écran
        """
        # Définir un panneau pour les options sur le côté gauche
        panel_width = 250
        panel_height = current_screen_size[1] - 100  # Hauteur presque pleine
        panel_x = 50  # Position à gauche
        panel_y = 50  # Un peu d'espace en haut

        # Mise à jour des positions des contrôles
        control_x = panel_x + 25
        self.slider_rect = py.Rect(control_x, panel_y + 100, 200, 5)
        self.dropdown_rect = py.Rect(control_x, panel_y + 200, 200, 30)

        return panel_x, panel_y, panel_width, panel_height

    def _draw_options_panel(self, current_screen_size):
        """
        Dessine le panneau d'options s'il est visible.

        Args:
            current_screen_size: Taille actuelle de l'écran
        """
        if not self.options_visible:
            return

        # Mettre à jour les positions des éléments d'options
        panel_x, panel_y, panel_width, panel_height = self._update_options_positions(current_screen_size)

        # Dessiner le panneau
        panel_rect = py.Rect(panel_x, panel_y, panel_width, panel_height)
        py.draw.rect(self.screen, (40, 40, 40, 220), panel_rect, border_radius=10)

        # Titre du panneau
        options_title = self.button_font.render("OPTIONS", True, self.COLORS["white"])
        self.screen.blit(options_title, (
            panel_x + (panel_width - options_title.get_width()) // 2,
            panel_y + 20
        ))

    def menu_display(self):
        """
        Affiche le menu principal et gère les interactions utilisateur.
        """
        # Assurez-vous que l'arrière-plan est capturé avant d'afficher le menu
        self.capture_background()

        running = True
        while running:
            current_screen_size = self.screen.get_size()

            # ---- Rendu de l'arrière-plan ----
            if self.original_background is not None:
                # Redimensionner l'arrière-plan à la taille actuelle de la fenêtre
                scaled_bg = py.transform.scale(self.original_background, current_screen_size)
                self.screen.blit(scaled_bg, (0, 0))
            else:
                # Solution de secours si l'arrière-plan n'est pas capturé
                self.screen.fill(self.COLORS["black"])

            # Créer un overlay semi-transparent
            overlay = py.Surface(current_screen_size, py.SRCALPHA)
            overlay.fill(self.COLORS["overlay"])
            self.screen.blit(overlay, (0, 0))

            # ---- Rendu des éléments d'interface ----
            # Dessiner le panneau d'options s'il est visible
            if self.options_visible:
                self._draw_options_panel(current_screen_size)

            # Obtenir et dessiner les boutons appropriés
            buttons = self._get_centered_buttons(current_screen_size)
            self._draw_buttons(buttons)

            # Dessiner les contrôles d'options s'ils sont visibles
            knob_x = self._draw_volume_control()
            option_rects = self._draw_language_dropdown()

            # Mettre à jour l'affichage
            py.display.flip()

            # ---- Gestion des événements ----
            for event in py.event.get():
                if event.type == py.QUIT:
                    py.quit()
                    sys.exit()

                elif event.type == py.VIDEORESIZE:
                    self.screen = py.display.set_mode((event.w, event.h), py.RESIZABLE)

                elif event.type == py.KEYDOWN:
                    if event.key == py.K_ESCAPE:
                        if self.options_visible:
                            # Si les options sont visibles, les fermer d'abord
                            self.options_visible = False
                        else:
                            # Sinon, quitter le menu
                            running = False

                elif event.type == py.MOUSEBUTTONDOWN:
                    mouse_pos = event.pos

                    # Gestion des clics sur les boutons
                    running = self._handle_button_click(buttons, mouse_pos)

                    # Si les options sont visibles, gérer les clics sur les contrôles d'options
                    if self.options_visible:
                        # Gestion du clic sur le contrôle de volume
                        self.dragging_volume = self._handle_volume_click(knob_x, mouse_pos)

                        # Gestion du clic sur la sélection de langue
                        self._handle_language_click(option_rects, mouse_pos)

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
    while running:
        ret, frame = cap.read()
        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_id)
            continue

        frame = cv2.flip(frame, 1)
        frame = cv2.resize(frame, (1000, 600))  #
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

        py.display.flip()
        py.time.wait(50)

    cap.release()
    py.quit()