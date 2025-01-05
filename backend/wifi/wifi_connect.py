import base64
import json
import subprocess
import os
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from flask_socketio import emit
from loguru import logger
from .wifi_crypto import decrypt_aes_key

def create_new_connection(ssid, password):
    """
    Erstellt eine WLAN-Konfigurationsdatei und fügt sie dem System hinzu.
    """
    profile_content = f"""<?xml version="1.0"?>
<WLANProfile xmlns="http://www.microsoft.com/networking/WLAN/profile/v1">
    <name>{ssid}</name>
    <SSIDConfig>
        <SSID>
            <name>{ssid}</name>
        </SSID>
    </SSIDConfig>
    <connectionType>ESS</connectionType>
    <connectionMode>auto</connectionMode>
    <MSM>
        <security>
            <authEncryption>
                <authentication>WPA2PSK</authentication>
                <encryption>AES</encryption>
                <useOneX>false</useOneX>
            </authEncryption>
            <sharedKey>
                <keyType>passPhrase</keyType>
                <protected>false</protected>
                <keyMaterial>{password}</keyMaterial>
            </sharedKey>
        </security>
    </MSM>
</WLANProfile>
"""
    config_file = f"{ssid}.xml"
    try:
        # XML-Datei schreiben
        with open(config_file, "w") as file:
            file.write(profile_content)
        logger.info(f"WLAN-Konfigurationsdatei '{config_file}' erstellt.")

        # Profil hinzufügen
        result = subprocess.run(
            ["netsh", "wlan", "add", "profile", f"filename={config_file}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )

        if result.returncode == 0:
            logger.info(f"WLAN-Profil '{ssid}' erfolgreich hinzugefügt.")
        else:
            logger.error(f"Fehler beim Hinzufügen des Profils: {result.stderr.strip()}")
            raise Exception(f"Fehler beim Hinzufügen des WLAN-Profils: {result.stderr.strip()}")

    finally:
        # Temporäre Datei entfernen
        if os.path.exists(config_file):
            os.remove(config_file)
            logger.info(f"Temporäre Datei '{config_file}' entfernt.")

def connect_to_wifi(ssid):
    """
    Verbindet mit dem angegebenen WLAN-Profil.
    """
    try:
        result = subprocess.run(
            ["netsh", "wlan", "connect", f"name={ssid}"],
            check=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )

        if result.returncode == 0:
            logger.info(f"Verbindung mit WLAN '{ssid}' erfolgreich initiiert.")
            return True
        else:
            logger.error(f"Fehler bei der Verbindung: {result.stderr.strip()}")
            return False
    except Exception as e:
        logger.error(f"Fehler beim Verbindungsversuch: {e}")
        return False


def save_wifi(data):
    """
    Speichert die WLAN-Daten verschlüsselt.
    """
    logger.debug(f"Empfangene WLAN-Daten zum Speichern: {data}")
    try:
        encrypted_aes_key = base64.b64decode(data['encrypted_key'])

        # AES-Schlüssel entschlüsseln
        aes_key = decrypt_aes_key(encrypted_aes_key)

        # WLAN-Daten entschlüsseln
        iv = base64.b64decode(data["iv"])
        ciphertext = base64.b64decode(data["ciphertext"])
        tag = base64.b64decode(data["tag"])

        cipher = Cipher(algorithms.AES(aes_key), modes.GCM(iv, tag), backend=default_backend())
        decryptor = cipher.decryptor()
        plaintext = decryptor.update(ciphertext) + decryptor.finalize()

        wifi_data = json.loads(plaintext.decode())
        ssid = wifi_data['ssid']
        password = wifi_data['password']

        logger.info(f"Entschlüsselte WLAN-Daten: SSID={ssid}, Passwort={password}")

        # Teste die Verbindung
        create_new_connection(ssid, password)
        if connect_to_wifi(ssid):
            # Verbindung erfolgreich, speichere die Daten
            save_credentials(ssid, password)
            logger.info(f"WLAN-Daten für '{ssid}' erfolgreich gespeichert.")
            emit('wifi_save_success', {"status": "success", "message": "WLAN-Daten erfolgreich gespeichert."})
        else:
            # Verbindung fehlgeschlagen
            logger.warning(f"WLAN-Verbindung mit '{ssid}' fehlgeschlagen.")
            emit('wifi_save_error', {"status": "error", "message": "WLAN-Verbindung fehlgeschlagen."})
    except Exception as e:
        logger.error(f"Fehler bei der Verarbeitung der WLAN-Daten: {e}")
        emit('wifi_save_error', {"status": "error", "message": "Fehler bei der Verarbeitung der WLAN-Daten."})


def save_credentials(ssid, password):
    try:
        with open("actions/smarthome/data/wifi_credentials.json", "w") as file:
            json.dump({"ssid": ssid, "password": password}, file)
        logger.info(f"WLAN-Daten für '{ssid}' erfolgreich gespeichert.")
    except Exception as e:
        logger.error(f"Fehler beim Speichern der WLAN-Daten: {e}")

def get_credentials():
    try:
        with open("actions/smarthome/data/wifi_credentials.json", "r") as file:
            data = json.load(file)
            return data
    except Exception as e:
        logger.error(f"Fehler beim Speichern der WLAN-Daten: {e}")