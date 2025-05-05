import time
import pygame
import json
import os


def load_game_font(font_name=None, size=36):

    try:
        return pygame.font.SysFont('Times New Roman', size, bold=True)
    except Exception:
        try:
            times_path = os.path.join(os.path.dirname(__file__), 'fonts', 'TimesNewRoman-Bold.ttf')
            if os.path.exists(times_path):
                return pygame.font.Font(times_path, size)
        except Exception:
            pass

    FALLBACK_FONTS = [
        'DejaVuSans-Bold.ttf',
        'FreeMono.ttf',
        'LiberationMono-Bold.ttf'
    ]

    for fallback in FALLBACK_FONTS:
        try:
            path = os.path.join(os.path.dirname(__file__), 'fonts', fallback)
            if os.path.exists(path):
                return pygame.font.Font(path, size)
        except Exception:
            pass

    return pygame.font.SysFont('serif', size, bold=True)


def load_game_texts():
    try:
        with open("data/texts.json", "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception as e:
        print(f"Erreur lors du chargement des textes: {e}")
        return {}


def display_text_above_player(game, text_key, duration=2.0, color=(255, 255, 255), offset_y=-20):
    level_str = str(game.level)
    if level_str in game.game_texts and text_key in game.game_texts[level_str]:
        text = game.game_texts[level_str][text_key]

        game.floating_texts[text_key] = {
            'text': text,
            'color': color,
            'end_time': time.time() + duration,
            'offset_y': offset_y,
            'opacity': 255
        }
    else:
        print(f"Texte non trouvé: niveau {level_str}, clé {text_key}")


def update_floating_texts(game, render_scroll):
    current_time = time.time()
    for text_key in game.floating_texts.copy():
        text_data = game.floating_texts[text_key]
        remaining_time = text_data['end_time'] - current_time
        if remaining_time + 1 < 0.5:
            game.floating_texts[text_key]['opacity'] = int(255 * (remaining_time / 0.5))

        player_x = game.player.rect().centerx - render_scroll[0]
        player_y = game.player.rect().top - render_scroll[1] + text_data['offset_y']

        try:
            font = load_game_font(size=14)
        except:
            font = pygame.font.Font(None, 18)

        text_surface = font.render(text_data['text'], True, text_data['color'])
        text_surface.set_alpha(text_data['opacity'])

        shadow_surface = font.render(text_data['text'], True, (0, 0, 0))
        shadow_surface.set_alpha(text_data['opacity'] * 0.7)

        text_rect = text_surface.get_rect(center=(player_x, player_y))
        shadow_rect = shadow_surface.get_rect(center=(player_x + 1, player_y + 1))

        game.display.blit(shadow_surface, shadow_rect)
        game.display.blit(text_surface, text_rect)

        if remaining_time <= 0:
            game.floating_text_shown = False
            del game.floating_texts[text_key]
        else:
            game.floating_text_shown = True