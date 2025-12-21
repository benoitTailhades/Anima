import json
import os
import time

# Removed Boss import to match the new main script
from scripts.entities import DistanceEnemy, Enemy, Throwable
from scripts.sound import set_game_volume
from scripts.activators import Activator
from scripts.doors import Door


class Save:
    def __init__(self, game):
        self.game = game
        self.save_folder = "saves"
        self.ensure_save_folder_exists()

    def ensure_save_folder_exists(self):
        """Creates the save directory if it doesn't exist."""
        if not os.path.exists(self.save_folder):
            os.makedirs(self.save_folder)

    def save_game(self, slot=1):
        """
        Serializes current game state to a JSON file.
        Iterates through charged levels to save persistent changes (dead enemies, opened doors).
        """
        # Base structure
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
            "activators": {str(lvl): [] for lvl in self.game.levels},
            "enemies": {str(lvl): [] for lvl in self.game.levels},
            "throwable": [],
            "doors": {str(lvl): [] for lvl in self.game.levels},
            "light_emitting_tiles": self.game.light_emitting_tiles,
            "settings": {
                "volume": self.game.volume,
                "keyboard_layout": self.game.keyboard_layout,
                "language": self.game.selected_language
            },
            "timestamp": time.time(),
        }

        # --- Save Persistent Level Data ---
        # We only save data for levels that the player has visited ("charged")
        for lvl in self.game.charged_levels:
            lvl_key = str(lvl)  # JSON keys must be strings

            # 1. Save Activators (Levers, Buttons)
            if "activators" in self.game.levels[lvl]:
                for activator in self.game.levels[lvl]["activators"]:
                    activator_data = {
                        "position": activator.pos,
                        "state": activator.state,
                        "type": activator.type,
                        "id": activator.id if hasattr(activator, "id") else 0,
                        "activated": activator.activated
                    }
                    save_data["activators"][lvl_key].append(activator_data)

            # 2. Save Doors
            if "doors" in self.game.levels[lvl]:
                for door in self.game.levels[lvl]["doors"]:
                    door_data = {
                        "position": door.pos,
                        "size": door.size,
                        "type": door.type,
                        "id": door.id if hasattr(door, "id") else None,
                        "opened": door.opened,
                        "opening_speed": door.opening_speed if hasattr(door, "opening_speed") else 1
                    }
                    save_data["doors"][lvl_key].append(door_data)

            # 3. Save Enemies
            if "enemies" in self.game.levels[lvl]:
                for enemy in self.game.levels[lvl]["enemies"]:
                    attributes = {}
                    # Capture custom attributes if they exist
                    if hasattr(enemy, "attributes"):
                        attributes = enemy.attributes
                    else:
                        # Fallback for standard attributes
                        if hasattr(enemy, "attack_distance"): attributes["attack_distance"] = enemy.attack_distance
                        if hasattr(enemy, "attack_dmg"): attributes["attack_dmg"] = enemy.attack_dmg
                        if hasattr(enemy, "attack_time"): attributes["attack_time"] = enemy.attack_time

                    enemy_data = {
                        "position": enemy.pos,
                        "hp": enemy.hp,
                        "type": enemy.enemy_type if hasattr(enemy, "enemy_type") else "picko",
                        "size": enemy.size if hasattr(enemy, "size") else (16, 16),
                        "attributes": attributes
                    }
                    save_data["enemies"][lvl_key].append(enemy_data)

        # 4. Save Throwable Objects (Rocks) - These are global or current-level specific
        for obj in self.game.throwable:
            throwable_data = {
                "position": obj.pos,
                "velocity": obj.velocity,
                "action": obj.action,
                "grabbed": obj.grabbed if hasattr(obj, "grabbed") else False,
                "type": obj.type if hasattr(obj, "type") else "blue_rock"
            }
            save_data["throwable"].append(throwable_data)

        # Write to file
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
        """
        Loads the game state from JSON.
        Restores player position, settings, and reconstructs objects for visited levels.
        """
        save_path = os.path.join(self.save_folder, f"save_{slot}.json")

        if not os.path.exists(save_path):
            print(f"No save found in {save_path}")
            return False

        try:
            with open(save_path, 'r') as save_file:
                save_data = json.load(save_file)

            # --- Restore Core Game State ---
            level = save_data.get("level", 0)
            self.game.level = level
            self.game.charged_levels = save_data.get("charged_levels", [])

            # Sync charged status
            for l in self.game.levels:
                self.game.levels[l]["charged"] = l in self.game.charged_levels

            if "spawner_pos" in save_data: self.game.spawner_pos = save_data["spawner_pos"]
            if "spawners" in save_data: self.game.spawners = save_data["spawners"]
            if "light_emitting_tiles" in save_data: self.game.light_emitting_tiles = save_data["light_emitting_tiles"]

            # --- Restore Throwable Objects ---
            if "throwable" in save_data and isinstance(save_data["throwable"], list):
                self.game.throwable = []
                try:
                    for obj_data in save_data["throwable"]:
                        throwable_type = obj_data.get("type", "blue_rock")
                        new_obj = Throwable(self.game, throwable_type, obj_data["position"], (16, 16))
                        new_obj.velocity = obj_data.get("velocity", [0, 0])
                        new_obj.action = obj_data.get("action", "intact")
                        if hasattr(new_obj, "grabbed"):
                            new_obj.grabbed = obj_data.get("grabbed", False)
                        self.game.throwable.append(new_obj)
                except Exception as e:
                    print(f"Error restoring throwable objects: {e}")

            # --- Restore Settings ---
            if "settings" in save_data:
                volume = save_data["settings"].get("volume", 0.5)
                set_game_volume(self.game, volume)
                self.game.keyboard_layout = save_data["settings"].get("keyboard_layout", "qwerty")
                self.game.selected_language = save_data["settings"].get("language", "English")
                if hasattr(self.game, "menu"):
                    self.game.menu.update_settings_from_game()

            # --- Restore Level-Specific Data (Enemies, Doors, Activators) ---
            for lvl in self.game.charged_levels:
                lvl_key = str(lvl)

                # 1. Restore Doors
                if "doors" in save_data and lvl_key in save_data["doors"]:
                    self.game.levels[lvl]['doors'] = []
                    try:
                        for door_data in save_data["doors"][lvl_key]:
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
                        print(f"Error restoring doors for level {lvl}: {e}")

                # 2. Restore Activators
                if "activators" in save_data and lvl_key in save_data["activators"]:
                    self.game.levels[lvl]['activators'] = []
                    try:
                        for activator_data in save_data["activators"][lvl_key]:
                            new_activator = Activator(
                                self.game,
                                activator_data["position"],
                                activator_data['type'],
                                i=activator_data.get("id", 0)
                            )
                            new_activator.activated = activator_data["activated"]
                            new_activator.state = activator_data["state"]
                            self.game.levels[lvl]['activators'].append(new_activator)
                    except Exception as e:
                        print(f"Error restoring activators for level {lvl}: {e}")

                # 3. Restore Enemies
                if "enemies" in save_data and lvl_key in save_data["enemies"]:
                    self.game.levels[lvl]['enemies'] = []
                    try:
                        for enemy_data in save_data["enemies"][lvl_key]:
                            enemy_type = enemy_data.get("type", "picko")

                            # Validation to ensure asset exists
                            if f"{enemy_type}/idle" not in self.game.assets:
                                enemy_type = "picko"  # Fallback

                            attributes = {
                                "attack_distance": 20,
                                "attack_dmg": 5,
                                "attack_time": 1
                            }
                            if "attributes" in enemy_data:
                                attributes.update(enemy_data["attributes"])

                            # Distinct instantiation for DistanceEnemy vs Standard Enemy
                            if enemy_type == "glorbo":
                                enemy = DistanceEnemy(
                                    self.game, enemy_type, enemy_data["position"],
                                    enemy_data.get("size", (16, 16)),
                                    enemy_data.get("hp", 100), attributes
                                )
                            else:
                                enemy = Enemy(
                                    self.game, enemy_type, enemy_data["position"],
                                    enemy_data.get("size", (16, 16)),
                                    enemy_data.get("hp", 100), attributes
                                )
                            self.game.levels[lvl]['enemies'].append(enemy)
                    except Exception as e:
                        print(f"Error restoring enemies for level {lvl}: {e}")

            # --- Finalize Load ---
            # Set scroll to player position
            if "player" in save_data and "position" in save_data["player"]:
                self.game.scroll = list(save_data["player"]["position"])

            # Load the actual map tiles and background
            self.game.load_level(level)

            # Override player stats with saved stats
            if "player" in save_data:
                if "position" in save_data["player"]:
                    self.game.player.pos = save_data["player"]["position"]
                if "hp" in save_data["player"]:
                    self.game.player_hp = save_data["player"]["hp"]
                if "spawn_point" in save_data["player"]:
                    self.game.spawn_point = save_data["player"]["spawn_point"]

            # Update interactables
            self.game.interactable = self.game.throwable.copy() + self.game.activators.copy()

            print(f"Game loaded successfully from {save_path}")
            return True

        except Exception as e:
            print(f"Error while loading the save: {e}")
            import traceback
            traceback.print_exc()
            return False

    def list_saves(self):
        """Returns a summary of all save files in the save folder."""
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
                    level = save_data.get("level", 0)

                    # Safe retrieval of list lengths
                    enemies_in_level = save_data.get("enemies", {}).get(str(level), [])
                    doors_in_level = save_data.get("doors", {}).get(str(level), [])

                    save_info = {
                        "slot": slot,
                        "date": save_date,
                        "level": level,
                        "player_hp": save_data["player"].get("hp", 0),
                        "enemy_count": len(enemies_in_level),
                        "throwable_count": len(save_data.get("throwable", [])),
                        "doors_count": len(doors_in_level),
                        "open_doors": 0,
                        "keyboard_layout": save_data.get("settings", {}).get("keyboard_layout", "unknown")
                    }

                    # Calculate total open doors across all levels
                    for lvl_key in save_data.get("doors", {}):
                        for door in save_data["doors"][lvl_key]:
                            if door.get("opened", False):
                                save_info["open_doors"] += 1

                    saves.append(save_info)
                except Exception as e:
                    print(f"Error reading save file {file}: {e}")
        return saves

    def delete_save(self, slot=1):
        save_path = os.path.join(self.save_folder, f"save_{slot}.json")
        if os.path.exists(save_path):
            os.remove(save_path)
            print(f"Save {slot} deleted")
            return True
        else:
            print(f"No save found in the slot {slot}")
            return False

    def get_latest_save(self):
        saves = self.list_saves()
        if not saves:
            return None
        saves.sort(key=lambda x: x["date"], reverse=True)
        return saves[0]["slot"]


# --- Global Helpers ---
def save_game(game, slot=1):
    if hasattr(game, 'save_system'):
        return game.save_system.save_game(slot)
    return False


def load_game(game, slot=1):
    if hasattr(game, 'save_system'):
        return game.save_system.load_game(slot)
    return False