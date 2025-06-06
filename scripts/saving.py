import json
import os
import time

from scripts.boss import SecondBoss
from scripts.entities import DistanceEnemy
from scripts.sound import set_game_volume


class Save:
    def __init__(self, game):  # Initialize the class and ensure that save.py exist
        self.game = game
        self.save_folder = "saves"
        self.ensure_save_folder_exists()

    def ensure_save_folder_exists(self):  # just create a litle save if it does not already exist(pretty common)
        if not os.path.exists(self.save_folder):
            os.makedirs(self.save_folder)

    def save_game(self, slot=1):
        save_data = {
            "player": {
                "position": self.game.player.pos,
                "hp": self.game.player_hp,
                "spawn_point": self.game.spawn_point,
            },
            "spawners": self.game.spawners,
            "spawner_pos": self.game.spawner_pos,
            "level": self.game.level,
            "charged_levels": self.game.charged_levels.copy(),
            "activators": {lvl:[] for lvl in self.game.levels},  # Store activators states
            "enemies": {lvl:[] for lvl in self.game.levels},
            "throwable": [],  # Store throwable objects
            "doors": {lvl:[] for lvl in self.game.levels},  # Store door states
            "light_emitting_tiles": self.game.light_emitting_tiles,
            "settings": {
                "volume": self.game.volume,
                "keyboard_layout": self.game.keyboard_layout,
                "language": self.game.selected_language
            },
            "timestamp": time.time(),
        }

        for lvl in self.game.charged_levels:
            for activator in self.game.levels[lvl]["activators"].copy():
                activator_data = {
                    "position": activator.pos,
                    "state": activator.state,
                    "type": activator.type,
                    "id": activator.id if hasattr(activator, "id") else 0,
                    "activated": activator.activated
                }
                save_data["activators"][lvl].append(activator_data)

            # Save door states
            for door in self.game.levels[lvl]["doors"].copy():
                door_data = {
                    "position": door.pos,
                    "size": door.size,
                    "type": door.type,
                    "id": door.id if hasattr(door, "id") else None,
                    "opened": door.opened,
                    "opening_speed": door.opening_speed if hasattr(door, "opening_speed") else 1
                }
                save_data["doors"][lvl].append(door_data)

            for enemy in self.game.levels[lvl]["enemies"].copy():
                attributes = {}

                if hasattr(enemy, "attack_distance"):
                    attributes["attack_distance"] = enemy.attack_distance
                if hasattr(enemy, "attack_dmg"):
                    attributes["attack_dmg"] = enemy.attack_dmg
                if hasattr(enemy, "attack_time"):
                    attributes["attack_time"] = enemy.attack_time

                if hasattr(enemy, "attributes"):
                    attributes = enemy.attributes

                enemy_data = {
                    "position": enemy.pos,
                    "hp": enemy.hp,
                    "type": enemy.enemy_type if hasattr(enemy, "type") else "picko",
                    "size": enemy.size if hasattr(enemy, "size") else (16, 16),
                    "attributes": attributes
                }
                save_data["enemies"][lvl].append(enemy_data)

        # Save throwable objects
        for obj in self.game.throwable:
            throwable_data = {
                "position": obj.pos,
                "velocity": obj.velocity,
                "action": obj.action,
                "grabbed": obj.grabbed if hasattr(obj, "grabbed") else False,
                "type": obj.type if hasattr(obj, "type") else "blue_rock"
            }
            save_data["throwable"].append(throwable_data)

        # Ajoutez ce code pour écrire les données dans un fichier
        save_path = os.path.join(self.save_folder, f"save_{slot}.json")
        try:
            with open(save_path, 'w') as save_file:
                json.dump(save_data, save_file, indent=4)
            print(f"Game saved successfully to {save_path}")
            return True
        except Exception as e:
            print(f"Error saving game: {e}")
            return False

    def load_game(self, slot=1):

        save_path = os.path.join(self.save_folder, f"save_{slot}.json")

        if not os.path.exists(save_path):
            print(f"No save found in {save_path}")
            return False

        try:
            with open(save_path, 'r') as save_file:
                save_data = json.load(save_file)

            level = save_data.get("level", 0)
            self.game.level = level
            self.game.charged_levels = save_data["charged_levels"]
            for l in self.game.levels:
                if l not in save_data["charged_levels"]:
                    self.game.levels[l]["charged"] = False
                else:
                    self.game.levels[l]["charged"] = True

            if "spawner_pos" in save_data:
                self.game.spawner_pos = save_data["spawner_pos"]
            if "spawners" in save_data:
                self.game.spawners = save_data["spawners"]
            if "light_emitting_tiles" in save_data:
                self.game.light_emitting_tiles = save_data["light_emitting_tiles"]

            # Load throwable objects if present in save data
            if "throwable" in save_data and isinstance(save_data["throwable"], list):
                # Clear existing throwable objects
                if save_data["throwable"]:
                    backup_throwable = self.game.throwable.copy() if hasattr(self.game, "throwable") else []
                    self.game.throwable = []

                    try:
                        # Import the Throwable class
                        from scripts.entities import Throwable

                        # Recreate throwable objects
                        for obj_data in save_data["throwable"]:
                            throwable_type = obj_data.get("type", "blue_rock")
                            new_obj = Throwable(self.game, throwable_type, obj_data["position"], (16, 16))

                            # Set additional properties
                            new_obj.velocity = obj_data.get("velocity", [0, 0])
                            new_obj.action = obj_data.get("action", "intact")
                            if hasattr(new_obj, "grabbed"):
                                new_obj.grabbed = obj_data.get("grabbed", False)

                            self.game.throwable.append(new_obj)
                    except Exception as e:
                        print(f"Error restoring throwable objects: {e}")
                        self.game.throwable = backup_throwable
                        import traceback
                        traceback.print_exc()

            if "settings" in save_data:
                volume = save_data["settings"].get("volume", 0.5)
                set_game_volume(self.game, volume)

                self.game.keyboard_layout = save_data["settings"].get("keyboard_layout", "qwerty")

                self.game.selected_language = save_data["settings"].get("language", "English")

                if hasattr(self.game, "menu") and hasattr(self.game.menu, "update_settings_from_game"):
                    self.game.menu.update_settings_from_game()

            for lvl in self.game.charged_levels:
                # Load door states if present in save data
                if "doors" in save_data and isinstance(save_data["doors"], dict):
                    if save_data["doors"][str(lvl)]:
                        backup_doors = self.game.levels[lvl]["doors"].copy() if "doors" in self.game.levels[lvl] else []
                        self.game.levels[lvl]['doors'] = []

                        try:
                            from scripts.doors import Door

                            for door_data in save_data["doors"][str(lvl)]:
                                # Find if the door already exists in the level (by position and type)
                                matching_door = None
                                for existing_door in backup_doors:
                                    if (existing_door.pos == door_data["position"] and
                                            existing_door.type == door_data["type"]):
                                        matching_door = existing_door
                                        break

                                if matching_door:
                                    # Update existing door state
                                    matching_door.opened = door_data["opened"]
                                    self.game.levels[lvl]['doors'].append(matching_door)
                                else:
                                    # Create a new door if needed
                                    door_id = door_data.get("id")
                                    new_door = Door(
                                        door_data["size"],
                                        door_data["position"],
                                        door_data["type"],
                                        door_id,
                                        False,
                                        door_data.get("opening_speed", 1),
                                        self.game
                                    )
                                    new_door.opened = door_data["opened"]
                                    self.game.levels[lvl]['doors'].append(new_door)
                        except Exception as e:
                            print(f"Error restoring doors: {e}")
                            self.game.levels[lvl]['doors'] = backup_doors
                            import traceback
                            traceback.print_exc()
                    else:
                        self.game.levels[lvl]['doors'] = []

                if "activators" in save_data and isinstance(save_data["activators"], dict):
                    # Clear existing activators if needed
                    if save_data["activators"][str(lvl)]:
                        backup_activators = self.game.levels[lvl]['activators'].copy() if "activators" in self.game.levels[lvl] else []
                        self.game.levels[lvl]['activators'] = []

                        try:
                            # Update activator states
                            for activator_data in save_data["activators"][str(lvl)]:
                                # Find if the activator already exists in the level (by position and ID)
                                matching_activator = None
                                for existing_activator in backup_activators:
                                    if (existing_activator.pos == activator_data["position"] and
                                            (not hasattr(existing_activator, "id") or existing_activator.id == activator_data["id"])):
                                        matching_activator = existing_activator
                                        break

                                if matching_activator:
                                    # Update existing activator state
                                    matching_activator.state = activator_data["state"]
                                    matching_activator.activated = activator_data["activated"]
                                    self.game.levels[lvl]['activators'].append(matching_activator)
                                else:
                                    # Create a new activator if needed
                                    from scripts.activators import Activator
                                    new_activator = Activator(self.game, activator_data["position"],activator_data['type'], i=activator_data.get("id", 0))
                                    new_activator.activated = activator_data["activated"]
                                    new_activator.state = activator_data["state"]
                                    self.game.levels[lvl]['activators'].append(new_activator)

                        except Exception as e:
                            print(f"Error restoring activators: {e}")
                            self.game.levels[lvl]['activators'] = backup_activators
                            import traceback
                            traceback.print_exc()
                    else:
                        self.game.levels[lvl]['activators'] = []

                if "enemies" in save_data and isinstance(save_data["enemies"], dict):
                    if save_data["enemies"][str(lvl)]:
                        backup_enemies = save_data["enemies"][str(lvl)].copy() if "enemies" in self.game.levels[lvl] else []
                        self.game.levels[lvl]['enemies'] = []

                        try:
                            from scripts.entities import Enemy

                            for enemy_data in save_data["enemies"][str(lvl)]:
                                try:
                                    enemy_type = enemy_data.get("type", "picko")

                                    if f"{enemy_type}/idle" not in self.game.assets:
                                        print(
                                            f"Warning: Enemy type '{enemy_type}' not found in assets, using 'picko' instead")
                                        enemy_type = "picko"

                                    default_attributes = {
                                        "attack_distance": 20,
                                        "attack_dmg": 5,
                                        "attack_time": 1
                                    }

                                    attributes = default_attributes.copy()
                                    if "attributes" in enemy_data and isinstance(enemy_data["attributes"], dict):
                                        attributes.update(enemy_data["attributes"])

                                    if enemy_type != "glorbo":
                                        enemy = Enemy(
                                            self.game,
                                            enemy_type,
                                            enemy_data["position"],
                                            enemy_data.get("size", (16, 16)),
                                            enemy_data.get("hp", 100),
                                            attributes
                                        )
                                    else:
                                        enemy = DistanceEnemy(
                                            self.game,
                                            enemy_type,
                                            enemy_data["position"],
                                            enemy_data.get("size", (16, 16)),
                                            enemy_data.get("hp", 100),
                                            attributes
                                        )

                                    self.game.levels[lvl]['enemies'].append(enemy)

                                except Exception as e:
                                    print(f"Error creating enemy: {e}")

                        except Exception as e:
                            print(f"Error recreating enemies: {e}")
                            self.game.levels[lvl]['enemies'] = backup_enemies
                            import traceback
                            traceback.print_exc()
                    else:
                        self.game.levels[lvl]['enemies'] = []

            self.game.scroll = list(save_data["player"]["position"])
            self.game.load_level(level)
            if "player" in save_data:
                if "position" in save_data["player"]:
                    self.game.player.pos = save_data["player"]["position"]
                if "hp" in save_data["player"]:
                    self.game.player_hp = save_data["player"]["hp"]
                if "spawn_point" in save_data["player"]:
                    self.game.spawn_point = save_data["player"]["spawn_point"]
            # Update interactable objects list to include any newly loaded throwable objects
            self.game.interactable = self.game.throwable.copy() + self.game.activators.copy()

            print(f"Game loaded successfully from {save_path}")
            return True

        except Exception as e:
            print(f"Error while loading the save: {e}")
            import traceback
            traceback.print_exc()
            return False

    def list_saves(self):  # keep a list of the saves and what they have into them(what is stored)
        saves = []

        for file in os.listdir(self.save_folder):
            if file.startswith("save_") and file.endswith(".json"):
                save_path = os.path.join(self.save_folder, file)
                try:
                    with open(save_path, 'r') as save_file:
                        save_data = json.load(save_file)

                    slot = int(file.split('_')[1].split('.')[0])

                    from datetime import datetime
                    save_date = datetime.fromtimestamp(save_data["timestamp"]).strftime("%Y-%m-%d")
                    level = save_data.get("level", "Unknown")
                    save_info = {
                        "slot": slot,
                        "date": save_date,
                        "level": level,
                        "player_hp": save_data["player"].get("hp", 0),
                        "enemy_count": len(save_data.get("enemies", {})[str(level)]),
                        "throwable_count": len(save_data.get("throwable", [])),  # Count of throwable objects
                        "doors_count": len(save_data.get("doors", {})[str(level)]),  # Count of doors
                        "open_doors": 0,
                        # Count of open doors
                        "keyboard_layout": save_data.get("settings", {}).get("keyboard_layout", "unknown")
                    }
                    for lvl in self.game.levels:
                        for door in save_data.get("doors", {})[str(lvl)]:
                            if door.get("opened", False):
                                save_info["open_doors"] += 1

                    saves.append(save_info)
                except Exception as e:
                    print(f"Error reading save file {file}: {e}")

        return saves

    def delete_save(self, slot=1):  # Pretty self-explanatory
        save_path = os.path.join(self.save_folder, f"save_{slot}.json")

        if os.path.exists(save_path):
            os.remove(save_path)
            print(f"Save {slot} deleted")
            return True
        else:
            print(f"No save found in the slot {slot}")
            return False

    def get_latest_save(self):  # check, among the list of saves which one is the latest. It will be used in the main in order to load the game where the user let it when he closed it
        saves = self.list_saves()
        if not saves:
            return None

        saves.sort(key=lambda x: x["date"], reverse=True)
        return saves[0]["slot"]

def save_game(game, slot=1):
    if hasattr(game, 'save_system'):
        success = game.save_system.save_game(slot)
        return success
    return False

def load_game(game, slot=1):
    if hasattr(game, 'save_system'):
        success = game.save_system.load_game(slot)
        return success
    return False