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
        print(f"Attempting to play sound: {path}")

        if not os.path.exists(path):
            print(f"Sound file not found: {path}")
            return None

        if not pygame.mixer.get_init():
            print("Initializing pygame mixer...")
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
            time.sleep(0.1)

        print("Loading sound file...")
        background_sound = pygame.mixer.Sound(path)

        print(f"Setting volume to: {volume}")
        background_sound.set_volume(volume)

        print("Playing sound...")
        background_sound.play(loops=-1, fade_ms=5000)

        print("Sound started successfully")
        return background_sound

    except Exception as e:
        print(f"Sound error: {e}")
        return None