import pygame
import time
import os

def run_sound(path, volume=0.5):#basically takes as a parameter a path and volume. Play the sound with a loop. It uses the pyame mixer
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

def load_sounds(entity, sound_paths):#useful function to load sounds. And very useful for debugging when loading sounds

    for sound_key, path in sound_paths.items():
        if sound_key in entity.sounds and path:
            try:
                entity.sounds[sound_key] = pygame.mixer.Sound(path)
            except Exception as e:
                print(f"Erreur lors du chargement du son '{sound_key}': {e}")

def set_game_volume(game, volume):
    game.volume = max(0, min(1, volume))
    if game.background_music:
        game.background_music.set_volume(game.volume)
