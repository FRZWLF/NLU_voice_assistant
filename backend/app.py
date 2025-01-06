from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS
from loguru import logger
from shelly.shelly_actions import discover_shelly_ap, connect_to_shelly_ap
from wifi.wifi_connect import save_wifi
from wifi.wifi_scan import scan_wifi
from wifi.wifi_crypto import get_public_key

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# Globale Variable für VoiceAssistant
voice_assistant = None

def init_voice_assistant(iassistant):
    global voice_assistant
    voice_assistant = iassistant
    logger.debug(f"VoiceAssistant erfolgreich initialisiert: {voice_assistant}")

saved_url = None  # Speicher für die URL
@socketio.on("music_state")
def handle_music_state(data):
    """
    Verarbeitet die Musikzustände (play/stop).
    """
    logger.debug(f"Empfangene Daten im music_state-Handler: {data} ({type(data)})")
    if not voice_assistant:
        logger.error("VoiceAssistant ist None. Initialisierung fehlgeschlagen.")
        return {"status": "error", "message": "VoiceAssistant nicht initialisiert"}

    global saved_url
    try:
        state = data.get("state")
        url = data.get("url", "")  # Optional: für den Play-Status
        logger.debug(f"Verarbeiteter State: {state}, URL: {url}")

        if state == "play":
            if not url:
                if not saved_url:  # Auch keine gespeicherte URL vorhanden
                    logger.error("Keine URL verfügbar")
                    return {"status": "error", "message": "No stream URL provided"}
                url = saved_url  # Verwende die gespeicherte URL
                logger.info(f"Verwende gespeicherte URL: {url}")

            # Stream starten
            saved_url = url
            logger.info(f"saved url: {saved_url}")
            voice_assistant.audio_player.play_stream(url)
            logger.debug("Stream gestartet, sende 'stream_status'-Event.")
            socketio.emit("stream_status", {"status": "playing", "url": url}, namespace="/")
            return {"status": "success", "message": f"Playing stream {url}"}

        elif state == "stop":
            # Stream stoppen
            logger.debug("Stream stoppen.")
            voice_assistant.audio_player.stop()
            socketio.emit("stream_status", {"status": "stopped"}, namespace="/")
            logger.debug("Stream gestoppt und 'stream_status'-Event gesendet.")
            return {"status": "success", "message": "Stream gestoppt"}

        else:
            return {"status": "error", "message": f"Unbekannter Zustand: {state}"}

    except Exception as e:
        logger.error(f"Fehlgeschlagen: {e}")
        return {"status": "error", "message": str(e)}


@socketio.on('set_volume')
def set_volume(data):
    voice_assistant.voice.set_volume(data)
    voice_assistant.audio_player.set_volume(data)
    voice_assistant.volume = data

@socketio.on('play_animalsound')
def play_animalsound(data):
    logger.debug(f"Empfangenes ogg-file: {data}")
    voice_assistant.audio_player.play_file(data)



@app.route('/get-public-key', methods=['GET'])
def handle_public_key():
    return get_public_key()

@socketio.on('scan_wifi')
def handle_scan_wifi():
    scan_wifi()

@socketio.on('save_wifi_credentials')
def save_wifi_credentials(data):
    save_wifi(data)


@socketio.on('shelly_ap_scan')
def handle_shelly_ap_scan():
    results = discover_shelly_ap()
    shelly_networks = results[0]
    connected_devices = results[1]
    if results:
        socketio.emit('ap_scan_result', {'shelly_networks': shelly_networks,'connected_devices': connected_devices})
    else:
        logger.info("Keine Shelly-Netzwerke gefunden.")
        socketio.emit('ap_scan_result', [])


@socketio.on('connect_shelly_ap')
def handle_connect_to_shelly_ap(data):
    connect_to_shelly_ap(data)




# Socket.IO Events
@socketio.on('connect')
def handle_connect():
    print("Client verbunden.")
    if voice_assistant:
        socketio.emit("assistant_ready", {"status": "ready"}, namespace="/")

@socketio.on('disconnect')
def handle_disconnect():
    print("Client getrennt.")