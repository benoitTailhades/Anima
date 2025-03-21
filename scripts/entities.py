import pygame
import random

class PhysicsEntity:
    def __init__(self, game, e_type, pos, size):
        self.game = game
        self.type = e_type
        self.pos = list(pos)
        self.size = size
        self.velocity = [0, 0]

    def rect(self):
        return pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])

    def update_coords(self, tilemap, movement = (0, 0)):
        frame_movement = (movement[0] + self.velocity[0], movement[1] + self.velocity[1])

        self.pos[0] += movement[0]
        entity_rect = self.rect()
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if frame_movement[0] > 0:
                    entity_rect.right = rect.left
                if frame_movement[0] < 0:
                    entity_rect.left = rect.right
                self.pos[0] = entity_rect.x




        self.pos[1] += movement[1]
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if frame_movement[1] > 0:
                    entity_rect.bottom = rect.top
                if frame_movement[1] < 0:
                    entity_rect.top = rect.bottom
                self.pos[1] = entity_rect.y



        self.velocity[1] = min(5, self.velocity[1] + 0.1)

    def render(self, surf):
        surf.blit(self.game.assets['player'], self.pos)


def blur(surface, span):
    for i in range(span):
        surface = pygame.transform.smoothscale(surface, (surface.get_width() // 2, surface.get_height() // 2))
        surface = pygame.transform.smoothscale(surface, (surface.get_width() * 2, surface.get_height() * 2))
    return surface


def message_display(surface, message, auteur, font, couleur):
    texte = font.render(message, True, couleur)
    auteur_texte = font.render(f"- {auteur}", True, couleur)

    surface_rect = surface.get_rect()
    texte_rect = texte.get_rect(center=(surface_rect.centerx, surface_rect.centery - 20))
    auteur_rect = auteur_texte.get_rect(center=(surface_rect.centerx, surface_rect.centery + 20))

    surface.blit(texte, texte_rect)
    surface.blit(auteur_texte, auteur_rect)


def death_animation(screen):
    clock = pygame.time.Clock()
    pygame.font.init()
    font = pygame.font.Font(None, 36)

    citations = {
        "Lingagu ligaligali wasa.": "Giannini Loic",

    }

    message, auteur = random.choice(list(citations.items()))

    screen_copy = screen.copy()

    for blur_intensity in range(1,6):
        blurred_screen = blur(screen_copy, blur_intensity)
        screen.blit(blurred_screen, (0, 0))
        message_display(screen, message, auteur, font, (255, 255, 255))
        pygame.display.flip()
        clock.tick(15)

    pygame.time.delay(2500)


def player_death(self,screen):
    death_animation(screen)
    self.player.pos[0] = 100
    self.player.pos[1] = 0
