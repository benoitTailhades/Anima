import time

import pygame
import random
import math

class PhysicsEntity:
    def __init__(self, game, e_type, pos, size):
        self.game = game
        self.type = e_type
        self.pos = list(pos)
        self.size = size
        self.velocity = [0, 0]
        self.collisions = {'up': False, 'down': False, 'right': False, 'left': False}

        self.action = ''
        self.flip = False
        try:
            self.set_action('idle')
        except AttributeError:
            pass

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
                  (self.pos[0] - offset[0], self.pos[1] - offset[1]))

class Enemy(PhysicsEntity):
    def __init__(self, game, enemy_type, pos, size, hp, attack_info):
        super().__init__(game, 'enemy', pos, size)

        self.walking = 0
        self.enemy_type = enemy_type

        self.attack_distance = attack_info["attack_distance"]
        self.vision_distance = 100
        self.is_attacking = False
        self.is_chasing = False
        self.player_x = self.game.player.rect().centerx
        self.enemy_x = self.rect().centerx
        self.enemy_y = self.rect().centery
        self.last_attack_time = 0
        self.attack_dmg = attack_info["attack_dmg"]
        self.attack_time = attack_info["attack_time"]
        self.is_dealing_damage = False
        self.hp = hp
        self.hit = False
        self.stunned = False
        self.last_stun_time = 0
        self.is_attacked = False
        self.animation = self.game.assets[self.enemy_type + '/idle'].copy()

    def update(self, tilemap, movement=(0, 0)):
        self.player_x = self.game.player.rect().centerx
        self.enemy_x = self.rect().centerx
        self.is_attacked = (self.game.attacking
                            and self.distance_with_player() <= self.game.player_attack_dist
                            and self.player_looking_at_entity()
                            and not self.is_attacked)

        if self.hp <= 0:
            self.animation.update()
            return

        if self.is_attacked:
            self.is_attacking = True
            self.is_chasing = True
            if time.time() - self.game.player_last_attack_time >= 0.3:
                self.game.deal_dmg('player', self)
                self.stunned = True
                self.last_stun_time = time.time()

        if self.is_attacking and not self.stunned:
            self.game.deal_dmg(self, 'player', self.attack_dmg, self.attack_time)
            self.is_dealing_damage = False

        # Handle stun state first
        if self.stunned:
            self.is_chasing = False
            self.is_attacking = False

            # Calculate time since stun started
            stun_elapsed = time.time() - self.last_stun_time
            stun_duration = 0.5

            if stun_elapsed >= stun_duration:
                self.stunned = False
                self.is_attacking = True
                self.is_chasing = True

            else:
                # Add stun animation/movement here
                movement = self.game.deal_knockback(self.game.player, self, 1.5)
                super().update(tilemap, movement=movement)
                self.flip = self.player_x < self.enemy_x
                self.animations(movement)
                return  # Skip the rest of the normal update logic

        # Regular (non-stunned) behavior continues below
        if self.walking:
            if tilemap.solid_check((self.rect().centerx + (-7 if self.flip else 7), self.pos[1] + 23)):
                if self.collisions['right'] or self.collisions['left']:
                    self.flip = not self.flip
                else:
                    movement = (movement[0] - 0.5 if self.flip else 0.5, movement[1])
                self.walking = max(0, self.walking - 1)
            else:
                self.flip = not self.flip
                self.is_attacking = False
                self.is_chasing = False

        elif not (self.is_attacking or self.is_chasing):
            rand = random.random()
            if rand < 0.01:
                self.walking = random.randint(30, 120)

        if self.distance_with_player() <= self.vision_distance:
            if tilemap.solid_check((self.rect().centerx + (-7 if self.flip else 7), self.pos[1] + 23)):
                if (self.check_if_player_close(self.vision_distance, not self.is_chasing)
                        or (not self.game.player.is_on_floor() and self.is_chasing)):
                    if self.check_if_player_close(self.vision_distance, not self.is_chasing):
                        if self.player_x < self.enemy_x:
                            self.flip = True
                        elif self.player_x > self.enemy_x:
                            self.flip = False
                    if not self.is_attacking:
                        self.is_chasing = True
                        movement = (movement[0] - 1 if self.flip else 1, movement[1])
                else:
                    self.is_chasing = False

                if self.check_if_player_close(self.attack_distance, False) or (
                        not self.game.player.is_on_floor() and self.is_attacking):
                    self.walking = 0
                    self.is_attacking = True
                    self.is_chasing = True
            else:
                self.flip = not self.flip
                self.is_attacking = False
                self.is_chasing = False

        if self.distance_with_player() > self.attack_distance and self.is_attacking:
            self.is_attacking = False

        if self.distance_with_player() > self.vision_distance and self.is_chasing:
            self.is_chasing = False

        super().update(tilemap, movement=movement)
        self.animations(movement)

    def set_action(self, action):
        if action != self.action:
            self.action = action
            self.animation = self.game.assets[self.enemy_type + '/' + self.action].copy()

    def check_if_player_close(self, vision_distance, mono_direction=True):
        if (not(self.game.tilemap.between_check(self.game.player.pos, self.pos))
                and self.game.player.pos[1]+self.game.player.size[1] == int(self.pos[1] + self.size[1])):
            if abs(self.player_x - self.enemy_x) <= vision_distance:
                if mono_direction:
                    if self.flip and self.player_x < self.enemy_x:
                        return True
                    if not self.flip and self.player_x > self.enemy_x:
                        return True
                else:
                    return True
        return False

    def distance_with_player(self):
        return math.sqrt((self.enemy_x - self.player_x) ** 2 + (
                    (self.pos[1] + self.size[1]) - (self.game.player.pos[1] + self.game.player.size[1])) ** 2)

    def player_looking_at_entity(self):
        if (not (self.game.tilemap.between_check(self.game.player.pos, self.pos))
                and self.game.player.pos[1] + self.game.player.size[1] == int(self.pos[1] + self.size[1])):
            if self.pos[0] + self.size[0] >= self.player_x >= self.pos[0]:
                return True
            elif self.game.player.last_direction == 1:
                return self.enemy_x > self.player_x
            elif self.game.player.last_direction == -1:
                return self.enemy_x < self.player_x

    def render(self, surf, offset=(0, 0)):
        surf.blit(self.animation.img(),(self.pos[0] - offset[0], self.pos[1] - offset[1]))

    def animations(self, movement):

        animation_running = False

        if self.stunned:
            self.set_action("hit")
            animation_running = True

        if self.is_attacking and not animation_running and not self.stunned:
            if self.action != "attack":
                self.set_action("attack")
            animation_running = True

        if not self.is_attacking and not animation_running:
            if movement[0] != 0:
                if self.flip:
                    self.set_action("run/left")
                else:
                    self.set_action("run/right")
            else:
                self.set_action("idle")


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
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                return

        blurred_screen = blur(screen_copy, blur_intensity)
        screen.blit(blurred_screen, (0, 0))
        message_display(screen, message, auteur, font, (255, 255, 255))
        pygame.display.flip()
        clock.tick(15)

    start_time = pygame.time.get_ticks()
    while pygame.time.get_ticks() - start_time < 2500:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                return
        clock.tick(30)

def player_death(game, screen, spawn_pos, spawn_level):
    game.levels[game.level]["enemies"] = game.enemies.copy()
    game.levels[game.level]["bosses"] = game.bosses.copy()
    game.levels[game.level]["levers"] = game.levers.copy()
    game.levels[game.level]["tilemap"] = game.tilemap.tilemap.copy()

    death_animation(screen)
    game.load_level(spawn_level)
    if game.in_boss_level:
        game.level = spawn_level
    game.player.pos[0] = spawn_pos[0]
    game.player.pos[1] = spawn_pos[1]