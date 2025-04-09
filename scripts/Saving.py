import json
import os
import time


class Save:
    def __init__(self, game):
        self.game = game
        self.save_folder = "saves"
        self.ensure_save_folder_exists()

    def ensure_save_folder_exists(self):
        """Vérifie que le dossier de sauvegarde existe, sinon le crée"""
        if not os.path.exists(self.save_folder):
            os.makedirs(self.save_folder)

    def save_game(self, slot=1):
        """Sauvegarde l'état actuel du jeu dans un fichier"""
        # Création de la structure de données à sauvegarder
        save_data = {
            "player": {
                "position": self.game.player.pos,
                "hp": self.game.player_hp
            },
            "enemies": [],
            "settings": {
                "volume": self.game.volume,
                "keyboard_layout": self.game.keyboard_layout
            },
            "timestamp": time.time()
        }

        # Enregistrement des données des ennemis
        for enemy in self.game.enemies:
            enemy_data = {
                "position": enemy.pos,
                "hp": enemy.hp
            }
            save_data["enemies"].append(enemy_data)

        # Écriture dans le fichier
        save_path = os.path.join(self.save_folder, f"save_{slot}.json")
        with open(save_path, 'w') as save_file:
            json.dump(save_data, save_file, indent=4)

        print(f"Jeu sauvegardé dans {save_path}")
        return True

    def load_game(self, slot=1):
        """Charge l'état du jeu depuis un fichier"""
        save_path = os.path.join(self.save_folder, f"save_{slot}.json")

        if not os.path.exists(save_path):
            print(f"Aucune sauvegarde trouvée dans {save_path}")
            return False

        try:
            with open(save_path, 'r') as save_file:
                save_data = json.load(save_file)

            # Chargement des données du joueur
            self.game.player.pos = save_data["player"]["position"]
            self.game.player_hp = save_data["player"]["hp"]

            # Chargement des paramètres
            self.game.set_volume(save_data["settings"]["volume"])
            self.game.keyboard_layout = save_data["settings"]["keyboard_layout"]

            # Suppression des ennemis actuels et chargement des ennemis sauvegardés
            self.game.enemies.clear()
            for enemy_data in save_data["enemies"]:
                from scripts.entities import Enemy
                enemy = Enemy(self.game, enemy_data["position"], (16, 16), enemy_data["hp"], 20)
                self.game.enemies.append(enemy)

            print(f"Jeu chargé depuis {save_path}")
            return True

        except Exception as e:
            print(f"Erreur lors du chargement de la sauvegarde: {e}")
            return False

    def list_saves(self):
        """Liste toutes les sauvegardes disponibles"""
        saves = []

        for file in os.listdir(self.save_folder):
            if file.startswith("save_") and file.endswith(".json"):
                save_path = os.path.join(self.save_folder, file)
                try:
                    with open(save_path, 'r') as save_file:
                        save_data = json.load(save_file)

                    # Extraire le numéro du slot de sauvegarde
                    slot = int(file.split('_')[1].split('.')[0])

                    # Format de la date
                    from datetime import datetime
                    save_date = datetime.fromtimestamp(save_data["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")

                    saves.append({
                        "slot": slot,
                        "date": save_date,
                        "player_hp": save_data["player"]["hp"],
                        "enemy_count": len(save_data["enemies"]),
                        "keyboard_layout": save_data["settings"]["keyboard_layout"]
                    })
                except:
                    # Si le fichier est corrompu, on l'ignore
                    pass

        return saves

    def delete_save(self, slot=1):
        """Supprime une sauvegarde"""
        save_path = os.path.join(self.save_folder, f"save_{slot}.json")

        if os.path.exists(save_path):
            os.remove(save_path)
            print(f"Sauvegarde {slot} supprimée")
            return True
        else:
            print(f"Aucune sauvegarde trouvée dans le slot {slot}")
            return False