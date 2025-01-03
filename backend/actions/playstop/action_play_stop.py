from loguru import logger
from rasa_sdk import Action
from socketio import Client

sio = Client()
sio.connect("http://127.0.0.1:5000")

class ActionPlay(Action):
    def name(self) -> str:
        return "action_play"

    def run(self, dispatcher, tracker, domain):
        logger.debug("Play triggered")
        sio.emit("music_state", {"state": "play", "url": ""})
        return []

class ActionStop(Action):
    def name(self) -> str:
        return "action_stop"

    def run(self, dispatcher, tracker, domain):
        logger.debug("Stop triggered")
        sio.emit("music_state", {"state": "stop", "url": ""})
        return []