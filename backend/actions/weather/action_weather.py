import geocoder
import pyowm
from pyowm.utils.config import get_default_config
from rasa_sdk import Action

OWM_API_KEY = "bc5744c123c52a756cfe5b9fa9671c31"


class ActionTellWeather(Action):
    def name(self):
        return "action_tell_weather"

    def run(self, dispatcher, tracker, domain):
        config_dict = get_default_config()
        config_dict['language'] = "de"

        owm = pyowm.OWM(OWM_API_KEY, config_dict)
        weather_mgr = owm.weather_manager()

        entities = tracker.latest_message["entities"]
        print(f"DEBUG: Location entity: {entities}")
        if not entities:
            location = ""
        else:
            location = next((ent["value"] for ent in entities if ent["entity"] == "LOC"), None)
            location = location.rstrip("?.,!")
            print(location)
            if not location and any(ent["value"].lower() in ['wetter', 'aktuelles wetter'] for ent in entities):
                location = ""
            elif not location and not any(ent["value"].lower() in ['wetter', 'aktuelles wetter'] for ent in entities):
                location = None

        print(f"Location: {location}")

        if location is None:
            dispatcher.utter_message("Ich habe den Ort nicht erkannt.")
            return []
        elif (location == "hier") or (location == ""):
            g = geocoder.ip('me')
            w = weather_mgr.weather_at_coords(g.latlng[0], g.latlng[1]).weather
            dispatcher.utter_message(f"Das Wetter in {g.city} ist {w.detailed_status} bei einer Temperatur von {str(w.temperature('celsius')['temp'])} Grad Celsius.")
            return[]
        else:
            obs_list = weather_mgr.weather_at_places(str(location), 'like', limit=5)
            if len(obs_list) > 0:
                w = obs_list[0].weather
                dispatcher.utter_message(f"Das Wetter in {str(location)} ist {w.detailed_status.lower()} bei einer Temperatur von {str(w.temperature('celsius')['temp'])} Grad Celsius.")
                return []

        return dispatcher.utter_message(f"Ich konnte den Ort {location} nicht finden.")