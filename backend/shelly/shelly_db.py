import json
import os
from loguru import logger

CONNECTED_DEVICES_FILE = os.path.join("actions","smarthome","data","smartdevices_db.json")

def load_connected_devices():
    """
    Lädt die Liste der bereits verbundenen Shelly-Geräte aus der JSON-Datei.
    """
    if os.path.exists(CONNECTED_DEVICES_FILE):
        try:
            with open(CONNECTED_DEVICES_FILE, "r") as file:
                return json.load(file)
        except Exception as e:
            logger.error(f"Fehler beim Laden der verbundenen Geräte: {e}")
            return {}
    return {}

def save_connected_device(shelly_data):
    """
    Speichert ein Shelly-Gerät in der JSON-Datei.
    """
    devices = load_connected_devices()
    devices[shelly_data["id"]] = shelly_data  # Speichere nach ID
    try:
        with open(CONNECTED_DEVICES_FILE, "w") as file:
            json.dump(devices, file, indent=4)
        logger.info(f"Shelly-Gerät erfolgreich gespeichert: {shelly_data}")
    except Exception as e:
        logger.error(f"Fehler beim Speichern des Shelly-Geräts: {e}")