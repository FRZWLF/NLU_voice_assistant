import os
from loguru import logger
from tinydb import TinyDB, Query

CONNECTED_DEVICES_DB = TinyDB(os.path.join("actions","smarthome","data","smartdevices_db.json"))
db = CONNECTED_DEVICES_DB

def load_connected_devices():
    """
    Lädt die Liste der bereits verbundenen Shelly-Geräte aus der JSON-Datei.
    """
    try:
        devices_table = db.table('devices')
        devices = devices_table.all()
        logger.info(f"Geladene Geräte aus der DB: {devices}")
        return devices
    except Exception as e:
        logger.error(f"Fehler beim Laden der Geräte aus der DB: {e}")
        return []

def save_connected_device(shelly_data,name=None,device_type=None,ip=None):
    """
    Speichert ein Shelly-Gerät in der JSON-Datei.
    """
    try:
        device_id = shelly_data["id"]
        Device = Query()

        # Prüfe, ob das Gerät schon in der Datenbank existiert
        existing_device = CONNECTED_DEVICES_DB.search(Device.id == device_id)

        if existing_device:
            # Aktualisiere das bestehende Gerät
            CONNECTED_DEVICES_DB.update({
                "name": name if name else existing_device[0].get("name"),
                "type": device_type if device_type else existing_device[0].get("type"),
                "ip": ip if ip else existing_device[0].get("ip"),
                **shelly_data
            }, Device.id == device_id)
            logger.info(f"Gerät aktualisiert: {device_id}")
        else:
            # Füge das Gerät als neues Element hinzu
            CONNECTED_DEVICES_DB.insert({
                "id": device_id,
                "name": name,
                "type": device_type,
                "ip": ip,
                **shelly_data
            })
            logger.info(f"Neues Gerät hinzugefügt: {device_id}")
    except Exception as e:
        logger.error(f"Fehler beim Speichern des Geräts: {e}")