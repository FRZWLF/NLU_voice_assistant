import requests
from loguru import logger
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from shelly.shelly_db import load_connected_devices


class ActionControlShelly(Action):
    def name(self):
        return "action_control_shelly"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        device_name = tracker.get_slot("device_name")
        state = tracker.get_slot("device_state")
        devices = load_connected_devices()

        if not devices:
            logger.error("Keine Geräte in der Datenbank gefunden.")
            return dispatcher.utter_message(text=f"Keine Geräte in der Datenbank gefunden.")

        # Gerät suchen
        device = next((d for d in devices if d.get("name") == device_name), None)

        if not device:
            logger.error(f"Das Gerät '{device_name}' wurde nicht gefunden.")
            return dispatcher.utter_message(text=f"Das Gerät '{device_name}' wurde nicht gefunden.")

        logger.info("Device gefunden.")
        s = None
        if state in ["ein", "an", "einschalten", "anschalten"]:
            s = "on"
        elif state in ["aus", "ausschalten"]:
            s = "off"
        else:
            logger.warning("Unbekannter Status: {}", state)
            return dispatcher.utter_message(text=f"Der Zustand {state} ist für den Schalter ungültig.")

        # Setze einen Get-Request ab, der das Gerät ein- oder ausschaltet
        PARAMS = {'turn': s}
        url = f"http://{device['ip']}/relay/0"

        try:
            logger.info("Device gefunden.")
            r = requests.get(url = url, params = PARAMS)
            r.raise_for_status()
            data = r.json()
            logger.debug("API-Antwort: {}", data)
            return ""
        except Exception as e:
            logger.error("Fehler beim Senden der Anfrage: {}", e)
            return dispatcher.utter_message(text=f"Anfrage an {device_name} fehlgeschlagen.")