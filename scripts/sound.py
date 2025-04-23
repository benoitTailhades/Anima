import pygame
import time
import os

def run_sound(path, volume=0.5):
    """
    Initialize the mixer and play a sound file.

    Args:
        path (str): Path to the sound file
        volume (float): Initial volume (0.0 to 1.0)

    Returns:
        pygame.mixer.Sound | None: The sound object if successful, None otherwise
    """
    try:


        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
            time.sleep(0.1)

        background_sound = pygame.mixer.Sound(path)

        background_sound.set_volume(volume)

        background_sound.play(loops=-1, fade_ms=5000)

        return background_sound

    except Exception as e:
        print(f"Sound error: {e}")
        return None

def load_sounds(entity, sound_paths):
    """
    Charge les sons à partir des chemins fournis

    sound_paths doit être un dictionnaire avec les clés suivantes:
    - 'jump': son pour le saut
    - 'dash': son pour le dash
    - 'wall_jump': son pour le wall jump
    - 'land': son pour l'atterrissage
    - 'run': son pour la course
    - 'walk': son pour la marche
    - 'stun': son pour l'étourdissement
    """
    for sound_key, path in sound_paths.items():
        if sound_key in entity.sounds and path:
            try:
                entity.sounds[sound_key] = pygame.mixer.Sound(path)
            except Exception as e:
                print(f"Erreur lors du chargement du son '{sound_key}': {e}")