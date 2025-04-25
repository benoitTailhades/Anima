import pygame

def generate_fog(surface, color=(220, 230, 240), opacity=40):
    fog_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    fog_surface.fill((*color, opacity))
    surface.blit(fog_surface, (0, 0))