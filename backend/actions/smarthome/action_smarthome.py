import requests
from fuzzywuzzy import process
from loguru import logger
from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher
from shelly.shelly_db import load_connected_devices


class ActionControlShelly(Action):
    def name(self):
        return "action_control_shelly"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        device_name = (tracker.get_slot("device_name")).lower()
        state = tracker.get_slot("device_state")
        devices = load_connected_devices()
        logger.info(f"Das Gerät '{device_name}'.")
        logger.info(f"Das Gerät '{state}'.")

        if not devices:
            logger.error("Keine Geräte in der Datenbank gefunden.")
            dispatcher.utter_message(text=f"Keine Geräte in der Datenbank gefunden.")
            return [SlotSet("device_name", None), SlotSet("device_state", None)]

        # Extrahiere alle Gerätenamen aus der Datenbank
        device_names = [d.get("name").lower() for d in devices if d.get("name")]

        # Fuzzy-Suche nach dem besten Match
        best_match, confidence = process.extractOne(device_name, device_names)

        if confidence < 75:  # Mindestübereinstimmungswert
            logger.error(f"Das Gerät '{device_name}' wurde nicht gefunden. Beste Übereinstimmung: {best_match} ({confidence}%)")
            dispatcher.utter_message(text=f"Das Gerät '{device_name}' wurde nicht gefunden. Meintest du '{best_match}'?")
            return [SlotSet("device_name", None), SlotSet("device_state", None)]

        # Gerät suchen
        device = next((d for d in devices if d.get("name").lower() == best_match), None)

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
            dispatcher.utter_message(text=f"Der Zustand {state} ist für den Schalter ungültig.")
            return [SlotSet("device_name", None), SlotSet("device_state", None)]

        # Setze einen Get-Request ab, der das Gerät ein- oder ausschaltet
        PARAMS = {'turn': s}
        url = f"http://{device['ip']}/relay/0"

        try:
            logger.info("Device gefunden.")
            r = requests.get(url = url, params = PARAMS)
            r.raise_for_status()
            data = r.json()
            logger.debug("API-Antwort: {}", data)
        except Exception as e:
            logger.error("Fehler beim Senden der Anfrage: {}", e)
            dispatcher.utter_message(text=f"Anfrage an {device_name} fehlgeschlagen.")

        # Slot am Ende leeren
        return [SlotSet("device_name", None), SlotSet("device_state", None)]