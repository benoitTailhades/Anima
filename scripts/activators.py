import pygame
import time
import json
import random
from scripts.particle import Particle
from scripts.display import move_visual, screen_shake

class Lever:
    def __init__(self, game, pos, size=(16, 16), i=0):#Define basic attributes, that will be useful to track multiple elements from the lever(Position, activated, etc)
        self.game = game
        self.pos = pos
        self.rect = pygame.Rect(pos[0], pos[1], size[0], size[1])
        self.state = 0
        self.last_interaction_time = 0
        self.interaction_cooldown = 0.5
        self.id = i
        self.activated = True

    def toggle(self):#Basically change the state of the lever from activated to not activated. Takes into account the countdown(useful for silly people trying to destroy the game)
        current_time = time.time()
        if current_time - self.last_interaction_time >= self.interaction_cooldown:
            self.state = int(not self.state)
            self.last_interaction_time = current_time

            return True
        return False

    def can_interact(self, player_rect, interaction_distance=2):#Check if the player can "touch" the lever.
        can_interact = self.rect.colliderect(player_rect.inflate(interaction_distance, interaction_distance))
        return can_interact and self.activated

    def render(self, surface, offset=(0, 0)):#Just display the marvellous lever design of our dear designer
        surface.blit(self.game.assets[self.game.get_environment(self.game.level) + '_lever'][self.state], (self.pos[0] - offset[0], self.pos[1] - offset[1]))

class Teleporter:
    def __init__(self, game, pos, size, t_id):
        self.game = game
        self.pos = list(pos)
        self.size = size
        self.id = t_id

    def rect(self):
        return pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])

    def can_interact(self, player_rect, interaction_distance=2):
        can_interact = self.rect().colliderect(player_rect.inflate(interaction_distance, interaction_distance))
        return can_interact

def load_activators_actions():
    try:
        with open("data/activators.json", "r") as file:
            actions_data = json.load(file)
            return actions_data

    except Exception as e:
        print(f"Error loading activators actions: {e}")
        return {"levers": {}, "buttons": {}}

def update_teleporter(game, t_id):
    if t_id is not None:
        action = game.activators_actions[str(game.level)]["teleporters"][str(t_id)]
        if time.time() - game.last_teleport_time < action["time"] - 0.2:
            pos = (game.player.rect().x + random.random() * game.player.rect().width,
                   game.player.rect().y + 5 + random.random() * game.player.rect().height)
            game.particles.append(
                Particle(game, 'crystal_fragment', pos, velocity=[-0.1, -4], frame=0))
            pass
        else:
            game.last_teleport_time = time.time()
            game.player.pos = action["dest"].copy()
            game.teleporting = False
            game.tp_id = None

def update_activators_actions(game, level):
    for lever in game.levers:
        if lever.can_interact(game.player.rect()):
            lever_id = str(lever.id)
            if lever_id in game.activators_actions[str(level)]["levers"]:
                action = game.activators_actions[str(level)]["levers"][lever_id]

                if action["type"] == "visual_and_door":
                    for door in game.doors:
                        if door.id == action["door_id"]:
                            lever.toggle()
                            move_visual(game, action["visual_duration"], door.pos)
                            lever.activated = False
                            door.open()

                    screen_shake(game, 10)
    for tp in game.teleporters:
        if tp.can_interact(game.player.rect()):
            if str(tp.id) in game.activators_actions[str(level)]["teleporters"]:
                game.last_teleport_time = time.time()
                game.teleporting = True
                game.tp_id = tp.id