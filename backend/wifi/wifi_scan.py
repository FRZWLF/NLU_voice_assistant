import time
from flask_socketio import emit
from loguru import logger
from pywifi import PyWiFi


def scan_wifi_networks():
    wifi = PyWiFi()  # Zugriff auf WLAN-Adapter
    iface = wifi.interfaces()[0]  # Erster WLAN-Adapter

    iface.scan()
    time.sleep(2)

    results = iface.scan_results()
    networks = {}
    for network in results:
        # Verwende die SSID als Schlüssel, um doppelte Einträge zu vermeiden
        if network.ssid not in networks:
            networks[network.ssid] = {
                "ssid": network.ssid,
                "signal": network.signal,
                "frequency": network.freq
            }
        else:
            # Aktualisiere das Netzwerk basierend auf Priorität: Bevorzugt 5 GHz
            existing_network = networks[network.ssid]
            if network.freq > existing_network["frequency"] or (
                    network.freq == existing_network["frequency"] and network.signal > existing_network["signal"]
            ):
                networks[network.ssid] = {
                    "ssid": network.ssid,
                    "signal": network.signal,
                    "frequency": network.freq
                }

    # Konvertiere zurück in eine Liste
    filtered_networks = list(networks.values())
    logger.info(f"Gefilterte Netzwerke: {filtered_networks}")
    return filtered_networks


def scan_wifi():
    """
    Scannt verfügbare WLAN-Netzwerke und sendet die Liste an das Frontend.
    """
    try:
        logger.info("Starte WLAN-Scan...")
        networks = scan_wifi_networks()

        available_networks = []
        for network in networks:
            ssid = network.get("ssid")
            if ssid:
                available_networks.append(ssid)

        logger.info(f"Gefundene Netzwerke: {available_networks}")
        emit("wifi_networks", {"networks": available_networks}, namespace="/")
    except Exception as e:
        logger.error(f"Fehler beim WLAN-Scan: {e}")
        emit("wifi_networks", {"error": str(e)}, namespace="/")