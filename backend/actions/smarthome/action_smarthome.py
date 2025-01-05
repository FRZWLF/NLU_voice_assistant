import os
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

DB_PATH = os.path.join('data', 'smartdevices_db.json')
db = SmartHomeDB(DB_PATH)
shelly_handler = ShellyHandler()

class ActionAddSmartDevice(Action):
    def name(self):
        return "action_add_smart_device"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        # Gerätesuche starten
        devices = shelly_handler.discover_shelly_device()
        if not devices:
            dispatcher.utter_message(text="Es wurden keine Smart-Geräte gefunden.")
            return []

        # Geräte in der Datenbank speichern
        for device in devices:
            db.add_device(device)
        dispatcher.utter_message(text=f"{len(devices)} Geräte wurden hinzugefügt.")
        return []

class ActionControlSmartDevice(Action):
    def name(self):
        return "action_control_smart_device"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        device_name = tracker.get_slot("device_name")
        state = tracker.get_slot("device_state")

        # Übersetze den Gerätezustand in "on"/"off"
        state = "on" if state in ["an", "ein"] else "off"
        device = db.get_device_by_name(device_name)

        if not device:
            dispatcher.utter_message(text=f"Das Gerät '{device_name}' wurde nicht gefunden.")
            return []

        # Shelly-Gerät steuern
        success = shelly_handler.control_device(device, state)
        if success:
            dispatcher.utter_message(text=f"Das Gerät '{device_name}' wurde {state} geschaltet.")
        else:
            dispatcher.utter_message(text=f"Das Gerät '{device_name}' konnte nicht gesteuert werden.")
        return []
