import pygame
import time
import math
import random

from scripts.entities import Enemy, PhysicsEntity

import pygame
import time
import math
import random

from scripts.entities import Enemy, PhysicsEntity, deal_dmg, deal_knockback
from scripts.display import screen_shake, move_visual


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

        if self.is_attacked and not self.hit:
            if time.time() - self.game.player_last_attack_time >= self.game.player_attack_time:
                deal_dmg(self.game, 'player', self)
                self.stunned = True
                self.hit = True
                self.last_stun_time = time.time()

        if not self.game.holding_attack and (not("attack" in self.game.player.action) or self.game.player.animation.done) :
            self.hit = False

        if self.is_attacking and not self.stunned:
            deal_dmg(self.game, self, 'player', self.attack_dmg, self.attack_time)
            if self.is_dealing_damage:
                self.game.player.velocity = list(deal_knockback(self, self.game.player, 4))
                self.game.player.is_stunned = True
                self.game.player.stunned_by = self
                self.game.player.last_stun_time = time.time()
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
            else:
                # Add stun animation/movement here
                movement = deal_knockback(self.game.player, self, 0.05)
                PhysicsEntity.update(self, tilemap, movement=movement)
                self.flip = self.player_x < self.enemy_x
                self.animations(movement)
                return  # Skip the rest of the normal update logic

        self.update_phase()
        PhysicsEntity.update(self, tilemap, movement=movement)

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
            speed = 1 * self.current_phase_data['speed']

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
                self.set_action("jump")
            except KeyError:
                # If jump_up animation doesn't exist
                pass
        else:
            # Falling part of jump
            try:
                self.set_action("jump")
            except KeyError:
                # If jump_down animation doesn't exist
                pass

        return False  # Still moving

class FirstBoss(Boss):
    def __init__(self, game, boss_type, pos, size, hp, attack_info):
        super().__init__(game, boss_type, pos, size, hp, attack_info)
        self.vine_attack_cycle_time = 2
        self.last_vine_attack = time.time()
        self.vines = []
        self.available_vines_positions = [(x*16, 576) for x in range(-2, 29)]
        self.available_summoned_entities_pos = [(x*16, 336) for x in range(-2, 29)
                                                if x not in {1,2,3,4,8,9,10,18,19,20,23,24,25,26}]
        self.bottom = True
        self.time_bottom = 3
        self.last_time_bottom = 0
        self.vines_cyles = 0
        self.vines_rendered = False
        self.vine_warning_time = 100
        self.phases = {
            1: {'threshold': 1.0, 'speed': 1.0, 'vines_speed': 100, 'max_cycles': 3},
            2: {'threshold': 0.5, 'speed': 1.0, 'vines_speed': 40, 'max_cycles': 6, 'amount_of_enemies': 5},
        }
        self.started = False

        # Introduction action attributes
        self.intro_sequence_started = False
        self.intro_complete = False
        self.intro_start_time = 0
        self.intro_duration = 6  # Duration in seconds for the intro animation

    def update(self, tilemap, movement=(0, 0)):
        self.start_condition = self.game.player.is_on_floor()
        if self.start_condition and not self.started:
            self.intro_start_time = time.time()
        if not self.game.cutscene and not self.started:
            self.game.cutscene = True

        if self.started or self.start_condition:
            self.started = True
            if not self.intro_complete:
                if time.time() - self.intro_start_time <= self.intro_duration:
                    move_visual(self.game, 0.1, self.pos)
                    if not self.pos[0] > 336:
                        self.animation.update()
                        self.pos[1] = 608
                        movement = (movement[0] + 0.5, movement[1])
                        frame_movement = (movement[0] + self.velocity[0], movement[1] + self.velocity[1])
                        self.pos[0] += frame_movement[0]
                        self.pos[1] += frame_movement[1]
                        self.animations(movement)
                    elif not self.flip:
                        movement = (movement[0], movement[1] - 2)
                        if self.pos[1] < 560:
                            self.flip = True
                            super().update(tilemap, movement)

                        else:
                            self.animation.update()
                            frame_movement = (movement[0] + self.velocity[0], movement[1] + self.velocity[1])
                            self.pos[0] += frame_movement[0]
                            self.pos[1] += frame_movement[1]
                            self.animations(movement)
                    else:
                        if self.collisions["down"]:
                            screen_shake(self.game, 32)
                            self.intro_complete = True

                        super().update(tilemap, movement)
                else:
                    self.intro_complete = True
                    self.game.moving_visual = False
            else:
                if not self.hp <= 0:
                    self.game.cutscene = False

                    if time.time() - self.last_time_bottom >= self.time_bottom:
                        if not self.has_performed_initial_jump and self.bottom:
                            if not self.is_jumping:
                                self.current_destination = (144, 480)
                                self.last_dest = self.current_destination
                                print("Starting initial jump to:", self.current_destination)

                            if self.current_destination is not None:
                                reached = self.move_to(self.current_destination, jump_height=100)

                                if reached:
                                    screen_shake(self.game, 16)
                                    print('Reached initial position')
                                    self.current_destination = None
                                    self.has_performed_initial_jump = True
                                    self.bottom = False
                                    # Next action after reaching position
                                    # For example, start attacking the player
                        else:
                            # Behavior after first jump is complete (attack patterns, etc.)
                            # For example:
                            if not self.is_jumping and time.time() - self.last_attack_time > 3.0 and self.vines_cyles != self.phases[self.phase]["max_cycles"]:
                                # Maybe jump to a new position
                                possible_positions = [(144, 480), (32, 496), (304, 496), (384, 480)]
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
                                    screen_shake(self.game, 16)
                                    print('Reached new position')
                                    self.current_destination = None
                                    # Maybe start an attack sequence

                    if self.vines_cyles == self.phases[self.phase]["max_cycles"] and len(self.vines) == 0:
                        if self.rect().colliderect(self.game.player.rect()):
                            self.is_attacking = True

                        if not self.bottom:
                            self.current_destination = (208, 608)
                            print("Starting initial jump to:", self.current_destination)
                            self.last_time_bottom = time.time()

                        if self.current_destination is not None:
                            reached = self.move_to(self.current_destination, jump_height=100)

                            if reached:
                                screen_shake(self.game, 32)
                                print('Reached bottom')
                                self.bottom = True
                                self.is_attacking = False
                                self.current_destination = None
                                self.vines_cyles = 0

                    if time.time() - self.last_vine_attack >= self.vine_attack_cycle_time and len(
                            self.vines) == 0 and not self.bottom:
                            for i in range(13):
                                selected_pos = random.choice(self.available_vines_positions)
                                self.vines.append(Vine((16, 48), selected_pos, 5, 10, self.phases[self.phase]["vines_speed"], self.game))
                                self.available_vines_positions.remove(selected_pos)
                            self.available_vines_positions = [(x * 16, 576) for x in range(-2, 29)]

                    if self.phase == 2:
                        if len(self.game.enemies) == 0:
                            for i in range(self.phases[2]["amount_of_enemies"]):
                                selected_pos = random.choice(self.available_summoned_entities_pos)
                                self.game.enemies.append(Enemy(self.game, "picko", selected_pos, (16, 16), 100,
                                                      {"attack_distance" : 20,
                                                       "attack_dmg": 5,
                                                       "attack_time": 2}))
                                self.available_summoned_entities_pos.remove(selected_pos)
                            self.available_summoned_entities_pos = [(x*16, 336) for x in range(-2, 29)
                                                                    if x not in {1,2,3,4,8,9,10,18,19,20,23,24,25,26}]

                    for vine in self.vines:
                        vine.update()
                        vine.render(self.game.display, (int(self.game.scroll[0]), int(self.game.scroll[1])))
                        if not self.vines_rendered:
                            self.vines_cyles += 1
                            self.vines_rendered = True
                        if vine.action == 'retreat' and vine.animation.done:
                            if len(self.vines) == 1:
                                self.last_vine_attack = time.time()
                                self.vines_rendered = False
                            self.vines.remove(vine)

                    if self.bottom:
                        self.set_action("charge")
                        if time.time() - self.last_time_bottom >= self.time_bottom:
                            self.bottom = False
                    else:
                        self.is_attacking = self.rect().colliderect(self.game.player.rect())

                else:
                    self.game.doors[0].open()
                super().update(tilemap, movement)

    def animations(self, movement):

        animation_running = False

        if self.stunned:
            self.set_action("hit")
            animation_running = True

        if not self.is_attacking and not animation_running:
            if movement[0] != 0:
                if self.flip:
                    self.set_action("run/left")
                else:
                    self.set_action("run/right")
            elif self.action != "charge":
                self.set_action("idle")

class SecondBoss(Boss):
    def __init__(self, game, boss_type, pos, size, hp, attack_info):
        super().__init__(game, boss_type, pos, size, hp, attack_info)
        self.phases = {
            1: {'threshold': 1.0, 'speed': 1.0},
            2: {'threshold': 0.5, 'speed': 1.0}
        }
        self.started = False
        self.teleporting = False

        # Introduction action attributes
        self.intro_sequence_started = False
        self.intro_complete = False
        self.intro_start_time = 0
        self.intro_duration = 6  # Duration in seconds for the intro animation

        self.initialize_laser_attributes()

    def teleport(self, pos):
        self.set_action("teleport")
        self.teleporting = True
        if self.animation.done:
            self.pos = pos.copy()

    def laser_attack(self):
        """
        Boss laser attack that:
        1. Moves to center position
        2. Creates a warning laser
        3. Intensifies the laser and deals damage
        4. Rotates the laser during the attack
        """
        # Constants for laser attack
        CENTER_POS = (208, 480)  # Center of the room
        LASER_WARMUP_TIME = 1.5  # Time in seconds for the warning phase
        LASER_ACTIVE_TIME = 3.0  # Time in seconds for active damage phase
        LASER_COOLDOWN = 1.0  # Time after laser finishes before next action
        LASER_DAMAGE = 10  # Damage per hit
        LASER_LENGTH = 400  # Length of the laser beam
        LASER_WIDTH = 16  # Width of the laser beam
        ROTATION_SPEED = 45  # Degrees per second

        # Initialize laser attack state if not already set
        if not hasattr(self, 'laser_state'):
            self.laser_state = 'moving'
            self.laser_start_time = time.time()
            self.laser_angle = 0
            self.laser_hit_cooldown = 0
            self.current_destination = CENTER_POS
            print("Starting laser attack - moving to center")

        current_time = time.time()
        elapsed_time = current_time - self.laser_start_time

        # State 1: Move to center position
        if self.laser_state == 'moving':
            if not self.is_jumping and self.current_destination is not None:
                # Start the jump to center
                reached = self.move_to(self.current_destination, jump_height=80)

                if reached:
                    print('Reached center position')
                    self.current_destination = None
                    self.laser_state = 'warning'
                    self.laser_start_time = current_time
                    self.set_action("laser_charge")  # Animation for charging laser
                    screen_shake(self.game, 8)  # Small screen shake when landing

        # State 2: Warning phase - laser is visible but not damaging
        elif self.laser_state == 'warning':
            if elapsed_time >= LASER_WARMUP_TIME:
                self.laser_state = 'active'
                self.laser_start_time = current_time
                self.set_action("laser_fire")  # Animation for firing laser
                screen_shake(self.game, 16)  # Stronger screen shake when laser activates

            # Render warning laser (thinner/different color)
            self.render_laser(alpha=128, width=LASER_WIDTH / 2, color=(255, 0, 0))

        # State 3: Active phase - laser deals damage and rotates
        elif self.laser_state == 'active':
            if elapsed_time >= LASER_ACTIVE_TIME:
                self.laser_state = 'cooldown'
                self.laser_start_time = current_time
                self.set_action("idle")  # Return to idle animation

            # Update laser angle
            self.laser_angle += ROTATION_SPEED * self.game.dt
            if self.laser_angle >= 360:
                self.laser_angle -= 360

            # Render active laser (full width/brightness)
            self.render_laser(alpha=255, width=LASER_WIDTH, color=(255, 50, 50))

            # Check for collision with player
            if current_time - self.laser_hit_cooldown >= 0.2:  # Hit cooldown of 0.2 seconds
                if self.check_laser_collision():
                    deal_dmg(self.game, self, 'player', LASER_DAMAGE, 0.1)
                    self.game.player.velocity = list(deal_knockback(self, self.game.player, 3))
                    self.game.player.is_stunned = True
                    self.game.player.stunned_by = self
                    self.game.player.last_stun_time = current_time
                    screen_shake(self.game, 12)
                    self.laser_hit_cooldown = current_time

        # State 4: Cooldown phase
        elif self.laser_state == 'cooldown':
            if elapsed_time >= LASER_COOLDOWN:
                # Reset laser attack state
                delattr(self, 'laser_state')
                self.last_attack_time = current_time  # Update the boss's last attack time

                # Choose next action or position
                print("Laser attack complete")
                return True  # Attack completed

        return False  # Attack still in progress

    def render_laser(self, alpha=255, width=16, color=(255, 0, 0)):
        """Render the laser beam with given properties"""
        # Calculate laser end position based on angle and length
        laser_length = 400
        center_x = self.rect().centerx - self.game.scroll[0]
        center_y = self.rect().centery - self.game.scroll[1]

        # Calculate end point of laser using trigonometry
        end_x = center_x + laser_length * math.cos(math.radians(self.laser_angle))
        end_y = center_y + laser_length * math.sin(math.radians(self.laser_angle))

        # Create a transparent surface for the laser
        laser_surf = pygame.Surface((800, 600), pygame.SRCALPHA)

        # Draw the laser beam with given properties
        pygame.draw.line(laser_surf, (*color, alpha), (center_x, center_y), (end_x, end_y), int(width))

        # Draw a glow effect around the laser
        glow_width = width * 2
        glow_color = (*color, alpha // 4)
        pygame.draw.line(laser_surf, glow_color, (center_x, center_y), (end_x, end_y), int(glow_width))

        # Blit the laser surface onto the game display
        self.game.display.blit(laser_surf, (0, 0))

    def check_laser_collision(self):
        """Check if the laser is colliding with the player"""
        # Get player rect adjusted for scroll
        player_rect = self.game.player.rect()
        player_x = player_rect.centerx
        player_y = player_rect.centery

        # Get laser source position (boss center)
        source_x = self.rect().centerx
        source_y = self.rect().centery

        # Calculate laser end position
        laser_length = 400
        end_x = source_x + laser_length * math.cos(math.radians(self.laser_angle))
        end_y = source_y + laser_length * math.sin(math.radians(self.laser_angle))

        # Simple line-circle collision detection
        # Check if the player (treated as a circle) is close enough to the laser line
        player_radius = (player_rect.width + player_rect.height) / 4  # Approximate player as circle

        # Calculate perpendicular distance from player to laser line
        # Using the formula for distance from point to line
        line_length = math.sqrt((end_x - source_x) ** 2 + (end_y - source_y) ** 2)
        if line_length == 0:
            return False

        # Calculate the normalized direction vector of the laser
        dx = (end_x - source_x) / line_length
        dy = (end_y - source_y) / line_length

        # Calculate the vector from source to player
        px = player_x - source_x
        py = player_y - source_y

        # Calculate the projection of player position onto the laser line
        projection = px * dx + py * dy

        # Check if the projection falls within the line segment
        if 0 <= projection <= line_length:
            # Calculate the perpendicular distance
            perp_x = source_x + projection * dx
            perp_y = source_y + projection * dy
            distance = math.sqrt((player_x - perp_x) ** 2 + (player_y - perp_y) ** 2)

            # Check if the distance is less than player radius (collision)
            return distance <= player_radius + self.laser_width / 2

        return False

    def update(self, tilemap, movement=(0, 0)):
        # Call the parent's update method first
        super().update(tilemap, movement)

        # Additional laser-specific updates if we're in laser attack mode
        if hasattr(self, 'laser_state') and self.hp > 0:
            # Continue the laser attack
            self.laser_attack()

    def initialize_laser_attributes(self):
        """Initialize attributes needed for laser attacks"""
        self.laser_cooldown = 5.0  # Time between laser attacks
        self.laser_width = 16  # Width of the laser beam
        self.can_use_laser = True  # Whether the boss can use the laser attack

    def update_attack(self):
        print("attack")


class Vine:
    def __init__(self, size, pos, attack_time, attack_dmg, warning_duration, game):
        self.game = game
        self.size = size
        self.pos = pos
        self.attack_time = attack_time
        self.last_attack_time = 0
        self.attack_dmg = attack_dmg
        self.warning_duration = warning_duration

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
            # attacking
            if self.animation.done:
                if self.rect().colliderect(self.game.player.rect()):
                    deal_dmg(self.game, self, 'player', self.attack_dmg, self.attack_time)

            if self.timer >= self.attack_time and self.animation.done:
                screen_shake(self.game, 16)
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

    def rect(self):
        return pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])

    def render(self, surf, offset):
        surf.blit(self.animation.img(), (self.pos[0] - offset[0], self.pos[1] - offset[1]))

    def is_finished(self):
        # Helper method to check if the vine has completed its sequence
        return self.state == 'done'