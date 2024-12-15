import datetime
import requests
from loguru import logger
from rasa_sdk import Action
from rasa_sdk.events import SlotSet

TIMEZONEDB_API_KEY = "WSBAFOWS1DLC"

class ActionTellTime(Action):
    def name(self) -> str:
        return "action_tell_time"

    def run(self, dispatcher, tracker, domain):
        entities = tracker.latest_message["entities"]
        print(f"DEBUG: Zusammengeführte Location: {entities}")
        # Suche nach zusammenhängenden location-Entitäten
        location_parts = [ent["value"] for ent in entities if ent["entity"] == "LOC"]
        if location_parts:
            # Kombiniere die Ortsnamen-Teile direkt (wenn notwendig)
            location = " ".join(location_parts)
        else:
            # Keine Entität gefunden -> Gib aktuelle Uhrzeit zurück
            current_time = datetime.datetime.now().strftime("%H:%M")
            dispatcher.utter_message(text=f"Es ist jetzt {current_time}.")
            return []
        print(f"DEBUG: Zusammengeführte Location: {location}")
        if location:
            try:
                # Schritt 1: Geokodierung mit OpenStreetMap (Nominatim API)
                geocode_url = f"https://nominatim.openstreetmap.org/search?q={location}&format=json&addressdetails=1"
                geocode_response = requests.get(geocode_url, headers={"User-Agent": "TimeFinder/1.0"})
                geocode_response.raise_for_status()
                geocode_data = geocode_response.json()

                if not geocode_data:
                    return f"Ich konnte den Ort '{location}' nicht finden."

                # Extrahiere Breiten- und Längengrad
                latitude = geocode_data[0]["lat"]
                longitude = geocode_data[0]["lon"]

                #if matching_timezone:
                time_response = requests.get(f"http://api.timezonedb.com/v2.1/get-time-zone?key={TIMEZONEDB_API_KEY}&format=json&by=position&lat={latitude}&lng={longitude}", timeout=10)
                time_response.raise_for_status()
                time_data = time_response.json()
                print(f"Debug: API Response = {time_data}")
                if time_data["status"] == "OK":
                    current_time = time_data["formatted"].split(" ")[1][:5]  # Zeit im Format HH:MM
                    dispatcher.utter_message(text=f"In {location} ist es jetzt {current_time}.")
                    logger.info(f"Dispatcher sendet Antwort: In {location} ist es jetzt {current_time}.")
                else:
                    dispatcher.utter_message(text="Es gab ein Problem mit der Zeit-API.")
            except Exception as e:
                dispatcher.utter_message(text="Es gab ein Problem beim Aufruf der Zeit.")
                print(f"Fehler: {e}")
        else:
            current_time = datetime.datetime.now().strftime("%H:%M")
            dispatcher.utter_message(text=f"Es ist jetzt {current_time}.")
        return [SlotSet("location", None)]