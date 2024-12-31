import yaml
from loguru import logger
from rasa_sdk import Action
from socketio import Client

sio = Client()
sio.connect("http://127.0.0.1:5000")

class ActionGetVolume(Action):
    def name(self) -> str:
        return "action_get_volume"

    def run(self, dispatcher, tracker, domain):
        CONFIG_FILE = "config_ai_assistant.yml"
        with open(CONFIG_FILE,'r',encoding="utf-8") as ymlfile:
            cfg = yaml.load(ymlfile,Loader=yaml.FullLoader)

        volume = int(cfg['assistant']['volume'] * 10)
        logger.info("Lautstärke ist {} von zehn.", volume)
        return dispatcher.utter_message(text=f"Die Lautstärke ist {volume} von 10.")

class ActionMaxVolume(Action):
    def name(self) -> str:
        return "action_max_volume"

    def run(self, dispatcher, tracker, domain):
        max_volume = round(10.0 / 10.0, 1)
        sio.emit('set_max_volume', {"data": max_volume})
        return dispatcher.utter_message(text=f"Die Lautstärke ist {int(max_volume * 10)} von 10.")