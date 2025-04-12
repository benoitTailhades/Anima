# scripts/boss.py
import pygame
import time
import math
import random

from scripts.entities import Enemy, PhysicsEntity


class Boss(Enemy):
    def __init__(self, game, boss_type, pos, size, hp, attack_info):
        super.__init__(game, boss_type, pos, size, hp, attack_info)
        self.max_hp = hp
        self.phase = 1
        self.phases = {
            1: {'threshold': 1.0, 'speed': 1.0, 'attack_cooldown': 2.0},
            2: {'threshold': 0.5, 'speed': 1.5, 'attack_cooldown': 1.5},
        }
        self.current_phase_data = self.phases[self.phase]
        self.next_phase_timer = 0
        self.transitioning_phase = False

        # Attack patterns
        self.attack_patterns = []
        self.current_attack = None

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
            self.game.player.is_stunned = True
            self.game.player.velocity = list(self.game.deal_knockback(self, self.game.player, 4))

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
                PhysicsEntity.update(self, tilemap, movement=movement)
                self.flip = self.player_x < self.enemy_x
                self.animations(movement)
                return  # Skip the rest of the normal update logic

        if self.distance_with_player() > self.attack_distance and self.is_attacking:
            self.is_attacking = False

        PhysicsEntity.update(self, tilemap, movement=movement)
        self.animations(movement)

    def update_phase(self):
        hp_percentage = self.hp / self.max_hp
        for phase_nb, phase_data in self.phases.keys(), self.phases.values():
            if hp_percentage <= phase_data['threshold']:
                if self.phase > phase_nb:
                    self.transition_to_phase(phase_nb)

    def transition_to_phase(self, new_phase):
        if new_phase in self.phases:
            print(f"Boss transitioning from phase {self.phase} to phase {new_phase}")
            self.phase = new_phase
            self.current_phase_data = self.phases[new_phase]
            self.transitioning_phase = True
            self.next_phase_timer = time.time()
            # Play transition animation
            self.set_action('phase_transition')
            # Could trigger special effects, sounds, etc.

    def move_to(self):
        pass