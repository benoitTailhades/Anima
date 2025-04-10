import json
import os
import time


class Save:
    def __init__(self, game):#Initialize the class and ensure that save.py exist
        self.game = game
        self.save_folder = "saves"
        self.ensure_save_folder_exists()

    def ensure_save_folder_exists(self):#just create a litle save if it does not already exist(pretty common)
        if not os.path.exists(self.save_folder):
            os.makedirs(self.save_folder)

    def save_game(self, slot=1):#Using a json file(like in the Fort boyard) to save the player data and a bunch od data (settings...)
        save_data = {
            "player": {
                "position": self.game.player.pos,
                "hp": self.game.player_hp
            },
            "level": self.game.level,  # Added level information
            "enemies": [],
            "settings": {
                "volume": self.game.volume,
                "keyboard_layout": self.game.keyboard_layout
            },
            "timestamp": time.time()
        }

        for enemy in self.game.enemies:
            enemy_data = {
                "position": enemy.pos,
                "hp": enemy.hp
            }
            save_data["enemies"].append(enemy_data)

        save_path = os.path.join(self.save_folder, f"save_{slot}.json")
        with open(save_path, 'w') as save_file:
            json.dump(save_data, save_file, indent=4)

        print(f"Game saved successfully in {save_path}")
        return True

    def load_game(self, slot=1):#use the basics of json to open the file, read it, warn if there is no save and use the game class to restaure the data
        save_path = os.path.join(self.save_folder, f"save_{slot}.json")

        if not os.path.exists(save_path):
            print(f"No save found in {save_path}")
            return False

        try:
            with open(save_path, 'r') as save_file:
                save_data = json.load(save_file)

            # Load level first so tile maps and other level-dependent data are loaded correctly
            level = save_data.get("level", 0)  # Default to level 0 if not found in older saves
            if self.game.level != level:
                self.game.level = level
                self.game.load_level(level)

            self.game.player.pos = save_data["player"]["position"]
            self.game.player_hp = save_data["player"]["hp"]

            self.game.set_volume(save_data["settings"]["volume"])
            self.game.keyboard_layout = save_data["settings"]["keyboard_layout"]

            self.game.enemies.clear()
            for enemy_data in save_data["enemies"]:
                from scripts.entities import Enemy
                enemy = Enemy(self.game, enemy_data["position"], (16, 16), enemy_data["hp"], 20)
                self.game.enemies.append(enemy)

            print(f"Game loaded from {save_path}")
            return True

        except Exception as e:
            print(f"Error while loading the save: {e}")
            return False

    def list_saves(self):#keep a list of the saves and what they have into them(what is stored)
        saves = []

        for file in os.listdir(self.save_folder):
            if file.startswith("save_") and file.endswith(".json"):
                save_path = os.path.join(self.save_folder, file)
                try:
                    with open(save_path, 'r') as save_file:
                        save_data = json.load(save_file)

                    slot = int(file.split('_')[1].split('.')[0])

                    from datetime import datetime
                    save_date = datetime.fromtimestamp(save_data["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")

                    saves.append({
                        "slot": slot,
                        "date": save_date,
                        "level": save_data.get("level", "Unknown"),  # Display level info in save list
                        "player_hp": save_data["player"]["hp"],
                        "enemy_count": len(save_data["enemies"]),
                        "keyboard_layout": save_data["settings"]["keyboard_layout"]
                    })
                except:
                    pass

        return saves

    def delete_save(self, slot=1):#Pretty self-explanatory
        save_path = os.path.join(self.save_folder, f"save_{slot}.json")

        if os.path.exists(save_path):
            os.remove(save_path)
            print(f"Save {slot} deleted")
            return True
        else:
            print(f"No save found in the slot {slot}")
            return False

    def get_latest_save(self):#check, among the list of saves which one is the latest. It will be used in the main in order to load the game where the user let it when he closed it
        saves = self.list_saves()
        if not saves:
            return None

        # Trier les sauvegardes par date (la plus récente en premier)
        saves.sort(key=lambda x: x["date"], reverse=True)
        return saves[0]["slot"]  # Retourne le numéro du slot de la sauvegarde la plus récente