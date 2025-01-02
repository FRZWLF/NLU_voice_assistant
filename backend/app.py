from flask import Flask, request, jsonify
from flask_socketio import SocketIO
from flask_cors import CORS
from loguru import logger

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

@socketio.on("music_state")
def handle_music_state(data):
    """
    Verarbeitet die Musikzustände (play/stop).
    """
    logger.debug(f"Empfangene Daten im music_state-Handler: {data} ({type(data)})")
    if not voice_assistant:
        logger.error("VoiceAssistant ist None. Initialisierung fehlgeschlagen.")
        return {"status": "error", "message": "VoiceAssistant nicht initialisiert"}

    try:
        state = data.get("state")
        url = data.get("url")  # Optional: für den Play-Status
        logger.debug(f"Verarbeiteter State: {state}, URL: {url}")

        if state == "play":
            if not url:
                return {"status": "error", "message": "No stream URL provided"}
            # Stream starten
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



# Socket.IO Events
@socketio.on('connect')
def handle_connect():
    print("Client verbunden.")
    if voice_assistant:
        socketio.emit("assistant_ready", {"status": "ready"}, namespace="/")

@socketio.on('disconnect')
def handle_disconnect():
    print("Client getrennt.")