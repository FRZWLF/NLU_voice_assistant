from multiprocessing.pool import ThreadPool
import netifaces
from loguru import logger
import requests
import time


def configure_shelly_network(shelly_ip,ssid,password):
    try:
        response = requests.get(f"http://{shelly_ip}/rpc/Shelly.GetDeviceInfo", timeout=15)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Gerät nicht erreichbar: {e}")

    try:
        url = f"http://{shelly_ip}/rpc/WiFi.SetConfig"
        headers = {
            "Content-Type": "application/json"
        }
        payload = {
            "config": {
                "sta": {
                    "ssid": ssid,
                    "pass": password,
                    "enable": True
                }
            }
        }
        logger.info(f"Sende Netzwerk-Konfigurationsdaten an {url}...")
        logger.info(f"Payload: {payload}")
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        logger.info(f"HTTP-Status: {response.status_code}")
        logger.info(f"Response-Body: {response.text}")
        if response.status_code != 200:
            logger.error(f"Fehler bei der Netzwerkverbindung: {response.text}")
            return False

        logger.info("WiFi-Konfiguration erfolgreich gesendet. Überprüfe Verbindung...")

        logger.info("Shelly-Gerät erfolgreich mit dem Heim-WLAN verbunden.")
        return True

    except Exception as e:
        logger.error(f"Fehler beim Verbinden des Geräts: {e}")
        return False


def get_active_ip():
    """
    Ermittelt die aktive IPv4-Adresse basierend auf der Standard-Gateway-Schnittstelle.
    """
    try:
        # Standard-Gateway ermitteln
        gateways = netifaces.gateways()
        default_gateway = gateways.get('default', {}).get(netifaces.AF_INET)
        if not default_gateway:
            logger.error("Kein Standard-Gateway gefunden.")
            return None

        gateway_interface = default_gateway[1]
        logger.info(f"Aktive Netzwerkschnittstelle: {gateway_interface}")

        # IP-Adresse der aktiven Schnittstelle abrufen
        interface_addresses = netifaces.ifaddresses(gateway_interface)
        ipv4_info = interface_addresses.get(netifaces.AF_INET)
        if not ipv4_info:
            logger.error("Keine IPv4-Adresse auf der aktiven Schnittstelle gefunden.")
            return None

        active_ip = ipv4_info[0]['addr']
        logger.info(f"Aktive IPv4-Adresse: {active_ip}")
        return active_ip
    except Exception as e:
        logger.error(f"Fehler beim Ermitteln der aktiven IP-Adresse: {e}")
        return None

def find_shelly_ip_in_lan():
    """
    Sucht nach der neuen IP-Adresse des Shelly-Geräts im Heimnetzwerk.
    """
    logger.info("Starte schnellen LAN-Scan, um Shelly-IP zu finden...")
    try:
        # Aktive IP-Adresse ermitteln
        local_ip = get_active_ip()
        if not local_ip:
            logger.error("Kann keine aktive IP-Adresse ermitteln.")
            return None

        subnet = ".".join(local_ip.split(".")[:3])  # Subnetz bestimmen
        ip_range = [f"{subnet}.{i}" for i in range(1, 255)]  # IP-Bereich generieren
        logger.info(f"Zu überprüfende IPs: {len(ip_range)} Adressen im Subnetz {subnet}")

        def is_shelly_device(ip):
            try:
                response = requests.get(f"http://{ip}/rpc/Shelly.GetDeviceInfo", timeout=0.5)
                if response.status_code == 200:
                    data = response.json()
                    if "shelly" in data.get("id", "").lower():
                        logger.info(f"Shelly-Gerät gefunden unter {ip}")
                        return {"ip": ip, "info": data}
            except requests.RequestException:
                pass  # Ignoriere Verbindungsfehler
            return None

        # Parallele HTTP-Checks
        with ThreadPool(50) as pool:
            devices = pool.map(is_shelly_device, ip_range)

        # Gefundene Geräte filtern
        devices = list(filter(None, devices))
        if devices:
            logger.info(f"Gefundene Shelly-Geräte: {devices}")
            return devices[0]
        else:
            logger.warning("Keine Shelly-Geräte im LAN gefunden.")
            return None

    except Exception as e:
        logger.error(f"Fehler beim LAN-Scan: {e}")
        return None


def is_shelly_reachable(shelly_ip, retries=3, delay=2):
    """
    Prüft, ob das Shelly-Gerät unter der angegebenen IP-Adresse erreichbar ist.
    """
    for attempt in range(retries):
        try:
            logger.info(f"Prüfe Erreichbarkeit von {shelly_ip} (Versuch {attempt + 1}/{retries})...")
            response = requests.get(f"http://{shelly_ip}/rpc/Shelly.GetDeviceInfo", timeout=5)
            if response.status_code == 200:
                logger.info("Shelly-Gerät ist erreichbar.")
                return True
        except Exception as e:
            logger.warning(f"Shelly ist nicht erreichbar: {e}")
        time.sleep(delay)
    logger.error("Shelly-Gerät ist nach mehreren Versuchen nicht erreichbar.")
    return False