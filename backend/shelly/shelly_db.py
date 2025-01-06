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
        devices_table = db.table('devices')
        Device = Query()
        logger.info(f"Name: {name}")

        # Prüfe, ob das Gerät schon in der Datenbank existiert
        existing_device = devices_table.search(Device.id == device_id)

        if existing_device:
            # Aktualisiere das bestehende Gerät
            devices_table.update({
                **shelly_data,
                "name": name.lower() if name else existing_device[0].get("name"),
                "type": device_type if device_type else existing_device[0].get("type"),
                "ip": ip if ip else existing_device[0].get("ip"),
            }, Device.id == device_id)
            logger.info(f"Gerät aktualisiert: {device_id}")
        else:
            # Füge das Gerät als neues Element hinzu
            devices_table.insert({
                **shelly_data,
                "id": device_id,
                "name": name.lower(),
                "type": device_type,
                "ip": ip,
            })
            logger.info(f"Neues Gerät hinzugefügt: {device_id}")
    except Exception as e:
        logger.error(f"Fehler beim Speichern des Geräts: {e}")