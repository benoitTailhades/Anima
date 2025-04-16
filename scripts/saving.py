import json
import os
import time


class Save:
    def __init__(self, game):  # Initialize the class and ensure that save.py exist
        self.game = game
        self.save_folder = "saves"
        self.ensure_save_folder_exists()

    def ensure_save_folder_exists(self):  # just create a litle save if it does not already exist(pretty common)
        if not os.path.exists(self.save_folder):
            os.makedirs(self.save_folder)

    def save_game(self,slot=1):  # Using a json file(like in the Fort boyard) to save the player data and a bunch od data (settings...)
        save_data = {
            "player": {
                "position": self.game.player.pos,
                "hp": self.game.player_hp
            },
            "level": self.game.level,
            "enemies": [],
            "settings": {
                "volume": self.game.volume,
                "keyboard_layout": self.game.keyboard_layout,
                "language": self.game.selected_language
            },
            "timestamp": time.time()
        }

        for enemy in self.game.enemies:
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
                "type": enemy.type if hasattr(enemy, "type") else "picko",
                "size": enemy.size if hasattr(enemy, "size") else (16, 16),
                "attributes": attributes
            }
            save_data["enemies"].append(enemy_data)

        save_path = os.path.join(self.save_folder, f"save_{slot}.json")
        with open(save_path, 'w') as save_file:
            json.dump(save_data, save_file, indent=4)

        print(f"Game saved successfully in {save_path}")
        return True

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
            self.game.levels[level]["charged"] = False
            self.game.load_level(level)

            if "player" in save_data:
                if "position" in save_data["player"]:
                    self.game.player.pos = save_data["player"]["position"]
                if "hp" in save_data["player"]:
                    self.game.player_hp = save_data["player"]["hp"]

            if "settings" in save_data:
                volume = save_data["settings"].get("volume", 0.5)
                self.game.set_volume(volume)

                self.game.keyboard_layout = save_data["settings"].get("keyboard_layout", "qwerty")

                self.game.selected_language = save_data["settings"].get("language", "English")

                if hasattr(self.game, "menu") and hasattr(self.game.menu, "update_settings_from_game"):
                    self.game.menu.update_settings_from_game()

            if "enemies" in save_data and isinstance(save_data["enemies"], list):
                if save_data["enemies"]:
                    backup_enemies = self.game.enemies.copy()
                    self.game.enemies.clear()

                    try:
                        from scripts.entities import Enemy

                        for enemy_data in save_data["enemies"]:
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

                                enemy = Enemy(
                                    self.game,
                                    enemy_type,
                                    enemy_data["position"],
                                    enemy_data.get("size", (16, 16)),
                                    enemy_data.get("hp", 100),
                                    attributes
                                )

                                self.game.enemies.append(enemy)

                            except Exception as e:
                                print(f"Error creating enemy: {e}")

                    except Exception as e:
                        print(f"Error recreating enemies: {e}")
                        self.game.enemies = backup_enemies
                        import traceback
                        traceback.print_exc()

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

                    saves.append({
                        "slot": slot,
                        "date": save_date,
                        "level": save_data.get("level", "Unknown"),
                        "player_hp": save_data["player"].get("hp", 0),
                        "enemy_count": len(save_data.get("enemies", [])),
                        "keyboard_layout": save_data.get("settings", {}).get("keyboard_layout", "unknown")
                    })
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