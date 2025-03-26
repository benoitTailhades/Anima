import pygame
import random


class PhysicsEntity:
    def __init__(self, game, e_type, pos, size):
        self.game = game
        self.type = e_type
        self.pos = list(pos)
        self.size = size
        self.velocity = [0, 0]
        self.collisions = {'up': False, 'down': False, 'right': False, 'left': False}

        self.action = ''
        self.anim_offset = (-3, -3)
        self.flip = False
        self.set_action('idle')

        self.last_movement = [0, 0]

    def rect(self):
        return pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])

    def set_action(self, action):
        if action != self.action:
            self.action = action
            self.animation = self.game.assets[self.type + '/' + self.action].copy()

    def update(self, tilemap, movement=(0, 0)):
        self.collisions = {'up': False, 'down': False, 'right': False, 'left': False}

        frame_movement = (movement[0] + self.velocity[0], movement[1] + self.velocity[1])

        self.pos[0] += frame_movement[0]
        entity_rect = self.rect()
        for rect in tilemap.physics_rects_around(self.pos, self.size):
            if entity_rect.colliderect(rect):
                if frame_movement[0] > 0:
                    entity_rect.right = rect.left
                    self.collisions['right'] = True
                if frame_movement[0] < 0:
                    entity_rect.left = rect.right
                    self.collisions['left'] = True
                self.pos[0] = entity_rect.x

        self.pos[1] += frame_movement[1]
        entity_rect = self.rect()
        for rect in tilemap.physics_rects_under(self.pos, self.size):
            if entity_rect.colliderect(rect):
                if frame_movement[1] > 0:
                    entity_rect.bottom = rect.top
                    self.collisions['down'] = True
                self.pos[1] = entity_rect.y
        for rect in tilemap.physics_rects_around(self.pos, self.size):
            if entity_rect.colliderect(rect):
                if frame_movement[1] < 0:
                    entity_rect.top = rect.bottom
                    self.collisions['up'] = True
            self.pos[1] = entity_rect.y

        if movement[0] > 0:
            self.flip = False
        if movement[0] < 0:
            self.flip = True

        self.last_movement = movement

        self.velocity[1] = min(5, self.velocity[1] + 0.1)

        if self.collisions['down'] or self.collisions['up']:
            self.velocity[1] = 0

        self.animation.update()

    def render(self, surf, offset=(0, 0)):
        surf.blit(pygame.transform.flip(self.animation.img(), self.flip, False),
                  (self.pos[0] - offset[0] + self.anim_offset[0], self.pos[1] - offset[1] + self.anim_offset[1]))


class Enemy(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'enemy', pos, size)

        self.walking = 0

    def update(self, tilemap, movement=(0, 0)):
        if self.walking:
            if tilemap.solid_check((self.rect().centerx + (-7 if self.flip else 7), self.pos[1] + 23)):
                if self.collisions['right'] or self.collisions['left']:
                    self.flip = not self.flip
                else:
                    movement = (movement[0] - 0.5 if self.flip else 0.5, movement[1])
                self.walking = max(0, self.walking - 1)
            else:
                self.flip = not self.flip
        elif random.random() < 0.01:
            self.walking = random.randint(30, 120)

        super().update(tilemap, movement=movement)

        if movement[0] != 0:
            self.set_action("run")
        else:
            self.set_action("idle")

    def render(self, surf, offset=(0, 0)):
        super().render(surf, offset=offset)


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

    for blur_intensity in range(1, 6):
        blurred_screen = blur(screen_copy, blur_intensity)
        screen.blit(blurred_screen, (0, 0))
        message_display(screen, message, auteur, font, (255, 255, 255))
        pygame.display.flip()
        clock.tick(15)

    pygame.time.delay(2500)


def player_death(game, screen, spawn_pos):
    death_animation(screen)
    game.player.pos[0] = spawn_pos[0]
    game.player.pos[1] = spawn_pos[1]
