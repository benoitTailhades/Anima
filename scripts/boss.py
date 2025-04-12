# scripts/boss.py
import pygame
import time
import math
import random

from scripts.entities import Enemy, PhysicsEntity

import pygame
import time
import math
import random

from scripts.entities import Enemy, PhysicsEntity


class Boss(Enemy):
    def __init__(self, game, boss_type, pos, size, hp, attack_info):
        super().__init__(game, boss_type, pos, size, hp, attack_info)
        self.max_hp = hp
        self.phase = 1
        self.phases = {
            1: {'threshold': 1.0, 'speed': 1.0, 'attack_cooldown': 2.0},
            2: {'threshold': 0.5, 'speed': 1.5, 'attack_cooldown': 1.5},
        }
        self.current_phase_data = self.phases[self.phase]
        self.next_phase_timer = 0
        self.transitioning_phase = False

        # Jump and movement variables
        self.is_jumping = False
        self.current_destination = None
        self.has_performed_initial_jump = False  # Track if we've done the initial jump

        # Attack patterns
        self.attack_patterns = []
        self.current_attack = None

    def update(self, tilemap, movement=(0, 0)):
        self.player_x = self.game.player.rect().centerx
        self.enemy_x = self.rect().centerx
        self.enemy_y = self.rect().centery
        self.is_attacked = (self.game.attacking
                            and self.distance_with_player() <= self.game.player_attack_dist
                            and self.player_looking_at_entity()
                            and not self.is_attacked)

        if self.hp <= 0:
            self.animation.update()
            return

        if self.is_attacked:
            if time.time() - self.game.player_last_attack_time >= 0.3:
                self.game.deal_dmg('player', self)
                self.stunned = True
                self.last_stun_time = time.time()
                print(self.hp)

        if self.is_attacking and not self.stunned:
            self.game.deal_dmg(self, 'player', self.attack_dmg, self.attack_time)
            if self.is_dealing_damage:
                self.game.player.velocity = list(self.game.deal_knockback(self, self.game.player, 4))
                self.game.player.is_stunned = True
                self.game.player.stunned_by = self
                self.game.player.last_stun_time = time.time()

        # Handle stun state first
        if self.stunned:
            self.is_chasing = False
            self.is_attacking = False

            # Calculate time since stun started
            stun_elapsed = time.time() - self.last_stun_time
            stun_duration = 0.5

            if stun_elapsed >= stun_duration:
                self.stunned = False
            else:
                # Add stun animation/movement here
                movement = self.game.deal_knockback(self.game.player, self, 0.4)
                PhysicsEntity.update(self, tilemap, movement=movement)
                self.flip = self.player_x < self.enemy_x
                self.animations(movement)
                return  # Skip the rest of the normal update logic

        self.update_phase()

        if self.distance_with_player() > self.attack_distance and self.is_attacking:
            self.is_attacking = False

        # Only update animations if not jumping (handled in move_to)
        if not self.is_jumping:
            self.animations(movement)

    def update_phase(self):
        hp_percentage = self.hp / self.max_hp
        for phase_nb, phase_data in self.phases.items():  # Fixed the iteration syntax
            if hp_percentage <= phase_data['threshold']:
                if self.phase < phase_nb:  # Changed condition to trigger when phases are different
                    self.transition_to_phase(phase_nb)

    def transition_to_phase(self, new_phase):
        if new_phase in self.phases:
            print(f"Boss transitioning from phase {self.phase} to phase {new_phase}")
            self.phase = new_phase
            self.current_phase_data = self.phases[new_phase]
            self.transitioning_phase = True
            self.next_phase_timer = time.time()
            # Play transition animation
            #self.set_action('phase_transition')
            # Could trigger special effects, sounds, etc.

    def move_to(self, target_pos, speed=None, jump_height=80):
        # Initialize movement tracking variables if first call
        if not self.is_jumping:
            self.is_jumping = True
            self.move_progress = 0.0
            self.move_start_pos = (self.pos[0], self.pos[1])
            print("Starting jump from", self.move_start_pos, "to", target_pos)

        if speed is None:
            speed = 0.8 * self.current_phase_data['speed']

        # Increment progress based on speed
        self.move_progress += 0.02 * speed

        # Cap progress at 1.0 (100%)
        if self.move_progress >= 1.0:
            # Set exact position and reset progress
            self.pos[0] = target_pos[0] - self.size[0] / 2
            self.pos[1] = target_pos[1] - self.size[1] / 2
            self.velocity = [0, 0]  # Reset velocity
            self.is_jumping = False  # End the jumping state
            self.move_progress = 0.0
            self.set_action("idle")  # Return to idle animation
            print("Jump completed")
            return True  # Destination reached

        # Calculate horizontal movement (linear)
        target_x = target_pos[0] - self.size[0] / 2
        distance_x = target_x - self.move_start_pos[0]
        new_x = self.move_start_pos[0] + (distance_x * self.move_progress)

        # Calculate vertical movement (parabolic)
        target_y = target_pos[1] - self.size[1] / 2
        distance_y = target_y - self.move_start_pos[1]

        # Parabolic arc: y = ax² + bx + c
        # At x=0: y=start_y, at x=1: y=target_y, at x=0.5: y=start_y-jump_height

        # Calculate parabola coefficients
        a = 2 * (self.move_start_pos[1] + target_y - 2 * (self.move_start_pos[1] - jump_height))
        b = -3 * self.move_start_pos[1] - target_y + 4 * (self.move_start_pos[1] - jump_height)
        c = self.move_start_pos[1]

        # Calculate y position on parabola
        t = self.move_progress
        new_y = a * (t * t) + b * t + c

        # Calculate movement from current position to new position
        movement_x = new_x - self.pos[0]
        movement_y = new_y - self.pos[1]

        # Set position directly to follow the parabolic path
        self.pos[0] = new_x
        self.pos[1] = new_y

        # Update flip based on horizontal movement direction
        if movement_x < 0:
            self.flip = True
        elif movement_x > 0:
            self.flip = False

        # Create a movement tuple for animation updates
        movement = (movement_x, movement_y)

        # Set appropriate animation based on jump phase
        if self.move_progress < 0.5:
            # Rising part of jump
            try:
                self.set_action("jump_up")
            except KeyError:
                # If jump_up animation doesn't exist
                pass
        else:
            # Falling part of jump
            try:
                self.set_action("jump_down")
            except KeyError:
                # If jump_down animation doesn't exist
                pass

        return False  # Still moving

class FirstBoss(Boss):
    def __init__(self, game, boss_type, pos, size, hp, attack_info):
        super().__init__(game, boss_type, pos, size, hp, attack_info)

    def update(self, tilemap, movement=(0, 0)):
        super().update(tilemap, movement)

        # Phase 1 behavior - Jump to position once
        if self.phase == 1:
            if not self.stunned:
                if not self.has_performed_initial_jump:
                    if not self.is_jumping:
                        self.current_destination = (32, 464)
                        self.last_dest = self.current_destination
                        print("Starting initial jump to:", self.current_destination)

                    if self.current_destination is not None:
                        reached = self.move_to(self.current_destination, jump_height=100)

                        if reached:
                            print('Reached initial position')
                            self.current_destination = None
                            self.has_performed_initial_jump = True
                            # Next action after reaching position
                            # For example, start attacking the player
                else:
                    # Behavior after first jump is complete (attack patterns, etc.)
                    # For example:
                    if not self.is_jumping and time.time() - self.last_attack_time > 3.0:
                        # Maybe jump to a new position
                        possible_positions = [(32, 464), (144, 544), (304, 480)]
                        r = random.choice(possible_positions)
                        while r == self.last_dest:
                            r = random.choice(possible_positions)
                        self.current_destination = r
                        self.last_dest = self.current_destination
                        print("Starting new jump to:", self.current_destination)
                        self.last_attack_time = time.time()

                    if self.current_destination is not None:
                        reached = self.move_to(self.current_destination, jump_height=100)

                        if reached:
                            print('Reached new position')
                            self.current_destination = None
                            # Maybe start an attack sequence=]]=

    def update_animation(self, movement):
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

class Vine:
    def __init__(self, size, pos, attack_time, attack_dmg, game):
        self.game = game
        self.size = size
        self.pos = pos
        self.attack_time = attack_time
        self.attack_dmg = attack_dmg
        self.warning_duration = 10

        # Animation and state handling
        self.animation = self.game.assets['vine/warning'].copy()
        self.action = 'warning'

        # Timers for state management
        self.timer = 0
        self.state = 'warning'  # States: 'warning', 'attack', 'retreat', 'done'

    def update(self):
        # Update animation
        self.animation.update()

        # State machine logic
        self.timer += 1

        if self.state == 'warning':
            if self.timer >= self.warning_duration:
                self.set_action('attack')
                self.state = 'attack'
                self.timer = 0

        elif self.state == 'attack':
            if self.timer == 1:  # Just entered attack state
                # attacking
                self.deal_damage()

            if self.timer >= self.attack_time:
                self.set_action('retreat')
                self.state = 'retreat'
                self.timer = 0

        elif self.state == 'retreat':
            # Assuming retreat animation has a fixed duration
            retreat_duration = 10  # Adjust as needed
            if self.timer >= retreat_duration:
                self.state = 'done'
                self.timer = 0

        # Could add code here to remove the vine when 'done'

    def set_action(self, action):
        if action != self.action:
            self.action = action
            self.animation = self.game.assets['vine/' + self.action].copy()

    def render(self, surf, offset):
        surf.blit(self.animation.img(), (self.pos[0] - offset[0], self.pos[1] - offset[1]))

    def is_finished(self):
        # Helper method to check if the vine has completed its sequence
        return self.state == 'done'
