# scripts/boss.py
import pygame
import time
import math
import random

from scripts.entities import PhysicsEntity


class Boss(PhysicsEntity):
    def __init__(self, game, pos, size, max_hp=500, dmg=30):
        super().__init__(game, 'boss', pos, size)
        self.max_hp = max_hp
        self.hp = max_hp
        self.dmg = dmg
        self.phase = 1
        self.phases = {
            1: {'threshold': 1.0, 'speed': 1.0, 'attack_cooldown': 2.0},
            2: {'threshold': 0.7, 'speed': 1.5, 'attack_cooldown': 1.5},
            3: {'threshold': 0.4, 'speed': 2.0, 'attack_cooldown': 1.0},
            4: {'threshold': 0.2, 'speed': 2.5, 'attack_cooldown': 0.5}
        }
        self.current_phase_data = self.phases[self.phase]
        self.last_attack_time = 0
        self.last_stun_time = 0
        self.stunned = False
        self.stun_duration = 0
        self.attack_range = 60
        self.aggro_range = 200
        self.has_aggro = False
        self.movement_speed = 1.5
        self.next_phase_timer = 0
        self.transitioning_phase = False

        # Attack patterns
        self.attack_patterns = []
        self.current_attack = None

    def update_phase(self):
        hp_percentage = self.hp / self.max_hp
        for phase_num, phase_data in sorted(self.phases.items(), key=lambda x: x[1]['threshold'], reverse=True):
            if hp_percentage <= phase_data['threshold']:
                if self.phase != phase_num:
                    self.transition_to_phase(phase_num)
                break

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

    def check_player_in_range(self, player):
        boss_center = self.rect().center
        player_center = player.rect().center

        dx = player_center[0] - boss_center[0]
        dy = player_center[1] - boss_center[1]
        distance = math.sqrt(dx * dx + dy * dy)

        if distance <= self.aggro_range:
            self.has_aggro = True
            return distance <= self.attack_range, distance
        else:
            self.has_aggro = False
            return False, distance

    def try_attack(self, player):
        current_time = time.time()
        if current_time - self.last_attack_time >= self.current_phase_data['attack_cooldown']:
            self.last_attack_time = current_time
            self.execute_attack(player)
            return True
        return False

    def execute_attack(self, player):
        # Base attack behavior - override in subclasses
        self.set_action('attack')
        # Deal damage if player is in range
        in_range, _ = self.check_player_in_range(player)
        if in_range and not self.stunned:
            self.game.deal_dmg(self, "player", self.dmg)

    def take_damage(self, damage):
        self.hp -= damage
        # Flash or damage animation
        self.set_action('hit')
        # Check if phase should change
        self.update_phase()
        if self.hp <= 0:
            self.set_action('death')

    def stun(self, duration=0.5):
        self.stunned = True
        self.last_stun_time = time.time()
        self.stun_duration = duration

    def move_towards_player(self, player):
        if self.stunned or self.transitioning_phase:
            return [0, 0]

        # Calculate direction to player
        boss_center = self.rect().center
        player_center = player.rect().center

        dx = player_center[0] - boss_center[0]
        dy = player_center[1] - boss_center[1]

        # Normalize the direction
        distance = max(1, math.sqrt(dx * dx + dy * dy))
        direction_x = dx / distance
        direction_y = dy / distance

        movement_speed = self.movement_speed * self.current_phase_data['speed']

        return [direction_x * movement_speed, 0]  # Only move horizontally for simplicity

    def update(self, tilemap, movement=(0, 0)):
        # Check if stunned
        if self.stunned:
            current_time = time.time()
            if current_time - self.last_stun_time >= self.stun_duration:
                self.stunned = False
                self.set_action('idle')

        # Check if transitioning between phases
        if self.transitioning_phase:
            if time.time() - self.next_phase_timer >= 1.5:  # Phase transition duration
                self.transitioning_phase = False
                self.set_action('idle')

        # Update current phase based on HP
        self.update_phase()

        # Act based on phase and state
        if not self.stunned and not self.transitioning_phase:
            player = self.game.player
            in_attack_range, distance = self.check_player_in_range(player)

            if self.has_aggro:
                if in_attack_range:
                    self.try_attack(player)
                    movement = [0, 0]  # Stop moving when attacking
                else:
                    movement = self.move_towards_player(player)
            else:
                # Default idle behavior when not aggroed
                movement = [0, 0]
                self.set_action('idle')

        # Apply physics and animations
        super().update(tilemap, movement)

    def render(self, surf, offset=(0, 0)):
        # Render boss
        super().render(surf, offset)

        # Render health bar
        bar_width = 50
        bar_height = 5
        health_percentage = max(0, self.hp / self.max_hp)
        health_width = bar_width * health_percentage

        # Position health bar above boss
        health_pos = (self.pos[0] - offset[0], self.pos[1] - offset[1] - 10)

        # Draw background (black)
        pygame.draw.rect(surf, (0, 0, 0), (health_pos[0], health_pos[1], bar_width, bar_height))

        # Draw health (red for phase 1, orange for phase 2, yellow for phase 3, green for phase 4)
        health_colors = {
            1: (255, 0, 0),  # Red
            2: (255, 165, 0),  # Orange
            3: (255, 255, 0),  # Yellow
            4: (0, 255, 0)  # Green
        }

        pygame.draw.rect(surf, health_colors.get(self.phase, (255, 0, 0)),
                         (health_pos[0], health_pos[1], health_width, bar_height))


class MeleeBoss(Boss):
    def __init__(self, game, pos, size, max_hp=400, dmg=35):
        super().__init__(game, pos, size, max_hp, dmg)
        self.type = 'melee_boss'  # Change asset prefix
        self.attack_range = 40  # Shorter range for melee
        self.dash_speed = 4.0
        self.dash_duration = 0.5
        self.dash_cooldown = 3.0
        self.last_dash_time = 0
        self.is_dashing = False
        self.dash_start_time = 0
        self.dash_direction = 1

        # Override phases for a melee boss
        self.phases = {
            1: {'threshold': 1.0, 'speed': 1.0, 'attack_cooldown': 2.0},
            2: {'threshold': 0.7, 'speed': 1.3, 'attack_cooldown': 1.8},
            3: {'threshold': 0.4, 'speed': 1.6, 'attack_cooldown': 1.2, 'combo_attacks': True},
            4: {'threshold': 0.2, 'speed': 2.0, 'attack_cooldown': 0.8, 'combo_attacks': True, 'ground_pound': True}
        }
        self.current_phase_data = self.phases[self.phase]

        # Combo attack variables
        self.combo_count = 0
        self.max_combo = 3
        self.combo_timer = 0

    def execute_attack(self, player):
        # Check if we should do a combo attack
        combo_attacks = self.current_phase_data.get('combo_attacks', False)
        ground_pound = self.current_phase_data.get('ground_pound', False)

        # Select attack type based on phase and distance
        player_dist = math.sqrt((player.pos[0] - self.pos[0]) ** 2 + (player.pos[1] - self.pos[1]) ** 2)

        if ground_pound and random.random() < 0.2 and self.collisions['down']:
            # Do a ground pound attack (phase 4)
            self.set_action('ground_pound')
            self.velocity[1] = -5  # Jump up
            # Will create shockwave when landing (check in update method)
        elif combo_attacks and (self.combo_count > 0 or random.random() < 0.4):
            # Do a combo attack
            if self.combo_count == 0:
                self.combo_timer = time.time()

            self.combo_count = (self.combo_count + 1) % self.max_combo
            self.set_action('attack_combo_' + str(self.combo_count))

            # Deal damage if player is in range
            in_range, _ = self.check_player_in_range(player)
            if in_range:
                self.game.deal_dmg(self, "player", self.dmg * (1 + self.combo_count * 0.2))
                # Knockback increases with combo
                knockback = self.game.deal_knockback(self, player, 3 + self.combo_count)
                player.velocity[0] += knockback[0]
                player.velocity[1] += knockback[1]
        elif player_dist > self.attack_range and random.random() < 0.3 and time.time() - self.last_dash_time > self.dash_cooldown:
            # Do a dash attack
            self.set_action('dash')
            self.is_dashing = True
            self.dash_start_time = time.time()
            self.last_dash_time = time.time()
            self.dash_direction = 1 if player.pos[0] > self.pos[0] else -1
        else:
            # Do a normal attack
            self.set_action('attack')
            in_range, _ = self.check_player_in_range(player)
            if in_range:
                self.game.deal_dmg(self, "player", self.dmg)
                knockback = self.game.deal_knockback(self, player, 2.0)
                player.velocity[0] += knockback[0]
                player.velocity[1] += knockback[1]

    def update(self, tilemap, movement=(0, 0)):
        # Update combo timer
        if self.combo_count > 0 and time.time() - self.combo_timer > 1.5:
            self.combo_count = 0

        # Handle dashing state
        if self.is_dashing:
            dash_elapsed = time.time() - self.dash_start_time
            if dash_elapsed < self.dash_duration:
                movement = [self.dash_direction * self.dash_speed, 0]

                # Check for player collision during dash
                player_rect = self.game.player.rect()
                if self.rect().colliderect(player_rect):
                    self.game.deal_dmg(self, "player", self.dmg * 1.5)
                    knockback = self.game.deal_knockback(self, self.game.player, 4.0)
                    self.game.player.velocity[0] += knockback[0]
                    self.game.player.velocity[1] += knockback[1]
            else:
                self.is_dashing = False
                self.set_action('idle')

        # Handle ground pound landing
        if self.action == 'ground_pound' and self.collisions['down'] and self.velocity[1] >= 0:
            # Create shockwave effect
            self.set_action('ground_pound_impact')
            # Damage player if they're on the ground and within range
            player = self.game.player
            if (abs(player.pos[0] - self.pos[0]) < 100 and
                    abs(player.pos[1] - self.pos[1]) < 50 and
                    player.collisions['down']):
                self.game.deal_dmg(self, "player", self.dmg * 2)
                # Strong upward knockback
                player.velocity[1] = -6

            # Add particles for visual effect
            for i in range(10):
                velocity = [random.uniform(-2, 2), random.uniform(-3, -1)]
                self.game.particles.append(
                    self.game.Particle(self.game, 'dust',
                                       (self.pos[0] + self.size[0] // 2, self.pos[1] + self.size[1]),
                                       velocity=velocity, frame=random.randint(0, 7))
                )

        # Call the parent update method
        super().update(tilemap, movement)