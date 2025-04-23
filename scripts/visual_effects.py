import pygame



def generate_fog(surface, color=(220, 230, 240), opacity=40):
    """
    Generate a simple, plain fog overlay for the entire screen.

    Args:
        surface: The surface to draw the fog on
        color: Base color of the fog (RGB)
        opacity: Fog opacity (0-255)
    """
    # Create a surface the same size as the display with alpha channel
    fog_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)

    # Fill it with a semi-transparent color
    fog_surface.fill((*color, opacity))

    # Blit the fog surface onto the main surface
    surface.blit(fog_surface, (0, 0))