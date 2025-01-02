from fuzzywuzzy import fuzz
from loguru import logger
from rasa_sdk import Action
from socketio import Client

sio = Client()
sio.connect("http://127.0.0.1:5000")


class ActionPlayRadiostream(Action):
    def name(self) -> str:
        return "action_play_radiostream"

    def run(self, dispatcher, tracker, domain):
        station_stream = None
        entities = tracker.latest_message["entities"]
        print(f"DEBUG: Location entity: {entities}")
        station = next((ent["value"] for ent in entities if ent["entity"]), None)
        station = clean_station_name(station)

        stations = {
            "deutschland funk": "https://st01.sslstream.dlf.de/dlf/01/128/mp3/stream.mp3",
            "top 40": "https://frontend.streamonkey.net/antthue-radiotop40/stream/mp3",
            "energy": "https://frontend.streamonkey.net/energy-berlin/stream/mp3",
            "absolut relax": "https://absolut-relax.live-sm.absolutradio.de/absolut-relax/stream/mp3",
            "mdr jump": "https://mdr-284320-0.sslcast.mdr.de/mdr/284320/0/mp3/high/stream.mp3",
            "sunshine live": "https://sunsl.streamabc.net/sunsl-sunslhardstyle-mp3-192-5865645"
        }

        for key, value in stations.items():
            ratio = fuzz.ratio(station.lower(), key.lower())
            logger.info("Übereinstimmung von {} und {} ist {}%", station, key, ratio)
            if ratio > 60:
                station_stream = value
                logger.info("Station '{}' erkannt mit URL '{}'.".format(key, station_stream))
                break

        # Wurde kein Sender gefunden?
        if station_stream is None:
            logger.debug("Kein Sender mit dem Namen '{}' gefunden.".format(station))
            return dispatcher.utter_message(text=f"Ich konnte den Sender {station} leider nicht finden.")
        else:
            logger.debug("Starte Streaming von '{}' mit URL '{}'.".format(station, station_stream))

        sio.emit("music_state", {"state": "play", "url": station_stream})

        # Der Assistent muss nicht sprechen, wenn ein Radiostream gespielt wird
        return []

def clean_station_name(extracted_text: str):
    keywords = ["spiele", "radio", "radiosender", "sender", "den", "ein", "an", "schalte", "wähle", "ab"]
    # Entferne Schlüsselwörter aus dem Text
    cleaned_text = " ".join(word for word in extracted_text.split() if word.lower() not in keywords)
    return cleaned_text