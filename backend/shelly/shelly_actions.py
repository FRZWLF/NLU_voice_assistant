import re
import subprocess
from flask_socketio import emit
from loguru import logger
from .shelly_db import load_connected_devices, save_connected_device
from .shelly_utils import is_shelly_reachable, configure_shelly_network, find_shelly_ip_in_lan
from wifi.wifi_connect import get_credentials, connect_to_wifi


def discover_shelly_ap():
    """
    Sucht nach Shelly-Access-Points in der Nähe.
    """
    try:
        logger.info("Starte WLAN-Scan nach Shelly-Access Points...")
        result = subprocess.run(
            ["netsh", "wlan", "show", "network"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        networks = result.stdout.decode("utf-8", errors="ignore")

        if result.returncode != 0:
            logger.error("Fehler beim WLAN-Scan: %s", result.stderr)
            return []

        # Suche nach SSIDs, die "Shelly" enthalten
        shelly_networks = []
        ssid_pattern = re.compile(r"SSID \d+ : (.+)")
        # Lade verbundene Geräte aus der Datenbank
        connected_devices = load_connected_devices()

        for line in networks.splitlines():
            match = ssid_pattern.search(line)
            if match:
                ssid = match.group(1).strip()
                if "shelly" in ssid.lower():
                    shelly_networks.append({"ssid": ssid, "ip": "192.168.33.1"})

        logger.info(f"Gefundene Shelly-Netzwerke: {shelly_networks}")
        return shelly_networks
    except Exception as e:
        logger.error("Fehler beim AP-Scan: %s", e)
        return []


def connect_to_shelly_ap(data):
    ssid = data.get("ssid")
    ip = "192.168.33.1"
    wifi_cred = get_credentials()
    if not ssid:
        emit('ap_connection_result', {"status": "error", "message": "SSID fehlt"})
        return
    if not wifi_cred or not wifi_cred.get('password'):
        emit('ap_connection_result', {"status": "error", "message": "WLAN-Daten fehlen"})
        return

    pw = wifi_cred['password']

    # Überprüfen, ob das Gerät bereits verbunden ist
    connected_devices = load_connected_devices()
    if any(ssid.lower() in device.get("id", "").lower() for device in connected_devices):
        logger.info(f"Gerät '{ssid}' ist bereits verbunden.")
        emit('ap_connection_result', {"status": "error", "message": "Das Gerät ist bereits verbunden."})
        return

    try:
        logger.info(f"Verbinde mit Shelly Access Point: {ssid}")
        result = subprocess.run(
            ["netsh", "wlan", "connect", f"name={ssid}"],
            check=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        if result.returncode == 0:
            logger.info(f"Erfolgreich mit {ssid} verbunden.")
            emit('ap_connection_result', {"status": "success", "message": f"Mit {ssid} verbunden"})

            if not is_shelly_reachable(ip):
                logger.error("Shelly-AP ist nicht erreichbar.")
                emit('ap_connection_result', {"status": "error", "message": "Shelly-AP ist nicht erreichbar."})
                return

            if configure_shelly_network(ip, wifi_cred['ssid'], pw):
                logger.info("Shelly erfolgreich ins Heim-WLAN integriert.")
                emit('ap_connection_result', {"status": "success", "message": "Shelly erfolgreich konfiguriert!"})

                # Neue IP im Heimnetzwerk finden
                shelly_device = find_shelly_ip_in_lan()
                if shelly_device:
                    save_connected_device(shelly_data=shelly_device["info"],ip=shelly_device['ip'])  # Gerät speichern
                    logger.info(f"Shelly erfolgreich integriert. Neue IP: {shelly_device['ip']}")

                    # Rückverbindung zum Heim-WLAN
                    if connect_to_wifi(wifi_cred["ssid"]):
                        logger.info("Erfolgreich zum Heim-WLAN verbunden.")
                        emit('ap_connection_result', {"status": "success", "message": "Zurück zum Heim-WLAN verbunden."})
                    else:
                        logger.error("Fehler beim Verbinden mit dem Heim-WLAN.")
                        emit('ap_connection_result', {"status": "error", "message": "Fehler beim Verbinden mit dem Heim-WLAN."})

                    return {"status": "success", "message": f"Shelly erfolgreich integriert! IP: {shelly_device['ip']}"}
                else:
                    return {"status": "error", "message": "Shelly konnte im Heim-WLAN nicht gefunden werden."}
            else:
                logger.error("Fehler beim Konfigurieren des Shelly-Netzwerks.")
                emit('ap_connection_result', {"status": "error", "message": "Fehler bei der Netzwerk-Konfiguration."})
        else:
            logger.error(f"Fehler beim Verbinden mit {ssid}: {result.stderr}")
            emit('ap_connection_result', {"status": "error", "message": result.stderr})
    except Exception as e:
        logger.error("Fehler beim Verbinden mit Shelly-AP: %s", e)
        emit('ap_connection_result', {"status": "error", "message": str(e)})