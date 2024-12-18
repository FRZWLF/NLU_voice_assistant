from flask import Flask, request, jsonify
from flask_socketio import SocketIO
from flask_cors import CORS

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# Globale Variable für VoiceAssistant
voice_assistant = None

def init_voice_assistant(iassistant):
    global voice_assistant
    voice_assistant = iassistant

@app.route("/play_stream", methods=["POST"])
def play_stream():
    if not voice_assistant:
        return jsonify({"status": "error", "message": "VoiceAssistant nicht initialisiert"}), 500

    data = request.get_json()
    stream_url = data.get("url")

    if not stream_url:
        return jsonify({"status": "error", "message": "No stream URL provided"}), 400

    try:
        voice_assistant.audio_player.play_stream(stream_url)
        socketio.emit("stream_status", {"status": "playing", "url": stream_url}, namespace="/")
        return jsonify({"status": "success", "message": f"Playing stream {stream_url}"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# Socket.IO Events
@socketio.on('connect')
def handle_connect():
    print("Client verbunden.")

@socketio.on('disconnect')
def handle_disconnect():
    print("Client getrennt.")