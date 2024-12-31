import multiprocessing
import subprocess
import sys

import numpy as np
import pvporcupine
import pyaudio
import requests
import sounddevice as sd
import whisper
import yaml
from loguru import logger
from rasa.core.agent import Agent
from webrtcvad import Vad

from TTS import Voice
from audioplayer import AudioPlayer

CONFIG_FILE = "config_ai_assistant.yml"


class VoiceAssistant:
    def __init__(self):
        logger.info("Initialisiere VoiceAssistant...")

        global CONFIG_FILE
        with open(CONFIG_FILE,'r',encoding="utf-8") as ymlfile:
            self.cfg = yaml.load(ymlfile,Loader=yaml.FullLoader)
        if self.cfg:
            logger.debug("Konfiguration erfolgreich gelesen.")
        else:
            logger.error("Konfiguration konnte nicht gelesen werden.")
            sys.exit(1)

        language = self.cfg['assistant']['language']
        if not language:
            language = "de"
        logger.info(f"Verwende Sprache {language}")

        # Initialisiere Whisper (Speech-to-Text)
        logger.info("Lade Whisper-Modell...")
        self.stt_model = whisper.load_model("medium")

        # Initialisiere TTS (Text-to-Speech)
        logger.info("Initialisiere Text-to-Speech...")
        self.voice = Voice()

        logger.debug("Initialisiere Wake Word Erkennung...")
        self.wake_words = ["americano", "bumblebee", "blueberry", "terminator", "grapefruit", "picovoice"]
        logger.debug(f"Wake Words sind {', '.join(self.wake_words)}")
        self.porcupine = pvporcupine.create(keywords=self.wake_words, sensitivities=[0.6] * len(self.wake_words))

        # Initialisiere VAD
        logger.info("Initialisiere Voice Activity Detection...")
        self.vad = Vad()
        self.vad.set_mode(3)
        self.audio_stream = self.setup_audio()

        self.audio_player = AudioPlayer()
        self.volume = self.cfg["assistant"]["volume"]
        self.silenced_volume = self.cfg["assistant"]["silenced_volume"]

        # Initialisiere Rasa-Agent für NLP
        logger.info("Lade Rasa-Agent...")
        self.agent = Agent.load("models")



    def setup_audio(self):
        devices = sd.query_devices()
        default_device = sd.default.device['input']
        logger.info(f"Standard-Mikrofon: {devices[default_device]['name']}")
        return pyaudio.PyAudio().open(
            rate=self.porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=self.porcupine.frame_length,
            input_device_index=default_device
        )

    def listen_for_wake_word(self):
        while True:
            pcm = self.audio_stream.read(self.porcupine.frame_length)
            pcm_data = np.frombuffer(pcm, dtype=np.int16)

            result = self.porcupine.process(pcm_data)
            if result >= 0:
                logger.info(f"Wake word erkannt: {self.wake_words[result]}")
                socketio.emit("wake_word_detected", {"status": "listening"}, namespace="/")
                socketio.start_background_task(self.handle_user_input)

    def handle_user_input(self):
        logger.info("Sprich jetzt.")

        audio_data = []
        silence_counter = 0
        silence_threshold = 60  # Anzahl stiller Frames, bevor die Aufnahme endet

        while True:
            pcm = self.audio_stream.read(320)
            pcm_data = np.frombuffer(pcm, dtype=np.int16)
            is_speech = self.vad.is_speech(pcm, sample_rate=16000)

            if is_speech:
                silence_counter = 0
                audio_data.append(pcm_data)
            else:
                silence_counter += 1

            # Beenden der Aufnahme nach ausreichend Stille
            if silence_counter > silence_threshold:
                logger.info("Aufnahme beendet.")
                break

        # Audio-Daten validieren, bevor sie verarbeitet werden
        if len(audio_data) == 0:
            logger.error("Keine validen Audio-Daten aufgezeichnet.")
            return

        # Audio-Daten zusammenführen und in Float konvertieren
        # Skalierung: Wertebereich von int16 (-32768 bis 32767) zu float (-1.0 bis 1.0)
        audio_data = np.concatenate(audio_data).astype(np.float32) / 32768.0

        logger.info("Audio verarbeitet. Starte Whisper.")
        socketio.emit("wake_word_detected", {"status": "processing"}, namespace="/")

        # Speech-to-Text mit Whisper
        transcription = self.stt_model.transcribe(audio_data, language="de")["text"]
        logger.info(f"Transkription: {transcription}")
        # Transkription an Rasa senden
        response = requests.post(
            "http://localhost:5005/webhooks/rest/webhook",
            json={"sender": "user", "message": transcription}
        )
        if response.ok and response.json():
            answer = response.json()[0]["text"]
            logger.info(f"Antwort: {answer}")
            socketio.emit("wake_word_detected", {"status": "ready"}, namespace="/")
            self.voice.say(answer)


# Subprozess-Methoden für andere Komponenten
def start_rasa_server():
    logger.info("Starte Rasa-Server...")
    rasa_path = "C:/Users/ricor/IdeaProjects/NLU_voice_assistant/backend"
    subprocess.run(["rasa", "run", "--enable-api", "--cors", "*"], shell=True, cwd=rasa_path)


def start_rasa_actions():
    logger.info("Starte Rasa-Actions-Server...")
    backend_path = "C:/Users/ricor/IdeaProjects/NLU_voice_assistant/backend"
    subprocess.run(["rasa", "run", "actions"], shell=True, cwd=backend_path)


def start_angular_frontend():
    logger.info("Starte Angular-Frontend...")
    frontend_path = "C:/Users/ricor/IdeaProjects/NLU_voice_assistant/frontend"
    subprocess.run(["ng", "serve"], shell=True, cwd=frontend_path)



if __name__ == "__main__":
    multiprocessing.set_start_method('spawn')

    # VoiceAssistant-Instanz erstellen und an app übergeben
    assistant = VoiceAssistant()

    from app import socketio, app, init_voice_assistant
    init_voice_assistant(assistant)

    # Starte Rasa-Server
    rasa_process = multiprocessing.Process(target=start_rasa_server)

    # Starte Rasa-Actions
    actions_process = multiprocessing.Process(target=start_rasa_actions)

    # Starte Angular-Frontend
    frontend_process = multiprocessing.Process(target=start_angular_frontend)

    rasa_process.start(); actions_process.start(); frontend_process.start()

    socketio.start_background_task(assistant.listen_for_wake_word)
    # Flask-SocketIO starten
    socketio.run(app, host="0.0.0.0", port=5000, debug=True, use_reloader=False)
    logger.info("VoiceAssistant gestartet.")

    rasa_process.join()
    actions_process.join()
    frontend_process.join()