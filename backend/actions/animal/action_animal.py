import os
from loguru import logger
from rasa_sdk import Action
from socketio import Client

sio = Client()
sio.connect("http://127.0.0.1:5000")

class ActionPlayAnimalSound(Action):
    def __init__(self):
        self.cached_files = {}
        ogg_path = os.path.join('actions', 'animal', 'animals')
        for filename in os.listdir(ogg_path):
            if filename.endswith(".ogg"):
                animal_key = filename.split(".")[0]
                self.cached_files[animal_key] = os.path.join(ogg_path, filename)

    def name(self) -> str:
        return "action_play_animalsound"

    def run(self, dispatcher, tracker, domain):
        animal = tracker.get_slot("animal")
        logger.debug(f"DEBUG: Volume slot: {animal}")
        ogg_path = os.path.join('actions','animal','animals')

        animals = {
            "cat": [ "cat", "katze", "chat", "gato", "gatto", "猫", "кот" ],
            "chicken": [ "chicken", "huhn", "poulet", "pollo", "pollo", "鶏", "курица" ],
            "cock": [ "cock", "hahn", "coq", "gallo", "gallo", "雄鶏", "петух" ],
            "cow": [ "cow", "kuh", "vache", "vaca", "mucca", "牛", "корова" ],
            "dog": [ "dog", "hund", "chien", "perro", "cane", "犬", "собака" ],
            "donkey": [ "donkey", "esel", "âne", "burro", "asino", "ロバ", "осел" ],
            "duck": [ "duck", "ente", "canard", "pato", "anatra", "アヒル", "утка" ],
            "goat": [ "goat", "ziege", "chèvre", "cabra", "capra", "ヤギ", "коза" ],
            "goose": [ "goose", "gans", "ganz", "oie", "ganso", "oca", "ガチョウ", "гусь" ],
            "horse": [ "horse", "pferd", "cheval", "caballo", "cavallo", "馬", "лошадь" ],
            "ox": [ "ox", "ochse", "bœuf", "buey", "bue", "雄牛", "бык" ],
            "pig": [ "pig", "schwein", "cochon", "cerdo", "maiale", "豚", "свинья" ],
            "sheep": [ "sheep", "schaf", "mouton", "oveja", "pecora", "羊", "овца" ],
            "turkey": [ "turkey", "truthahn", "dinde", "pavo", "tacchino", "七面鳥", "индюк" ],
        }

        animal = animal.strip().lower()
        for key,value in animals.items():
            if animal in value:
                ogg_file = os.path.join(ogg_path, f"{key}.ogg")
                sio.emit('play_animalsound', ogg_file)
                return ""

        return dispatcher.utter_message(text="Das Tier kenne ich nicht.")