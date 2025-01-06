import geocoder
import pyowm
from loguru import logger
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

        location = tracker.get_slot("location")
        logger.debug(f"Erkannter Slot 'location': {location}")

        if not location:
            location = ""
            logger.info("Keine Location erkannt. Fallback auf aktuelle Position.")

        if not location or location.lower() in ["hier", "meine position", "aktuell", ""]:
            logger.info("Keine spezifische Location angegeben. Fallback auf aktuelle Position.")
            g = geocoder.ip('me')
            w = weather_mgr.weather_at_coords(g.latlng[0], g.latlng[1]).weather
            dispatcher.utter_message(f"Das Wetter in {g.city} ist {w.detailed_status.lower()} bei einer Temperatur von {str(w.temperature('celsius')['temp'])} Grad Celsius.")
            return[]

        print(f"Location: {location}")

        try:
            obs_list = weather_mgr.weather_at_places(str(location), 'like', limit=5)
            if obs_list:
                w = obs_list[0].weather
                dispatcher.utter_message(f"Das Wetter in {str(location)} ist {w.detailed_status.lower()} bei einer Temperatur von {str(w.temperature('celsius')['temp'])} Grad Celsius.")
                return []
            else:
                dispatcher.utter_message(f"Ich konnte keine Wetterdaten für {location} finden.")
        except Exception as e:
            logger.error(f"Fehler bei der Wetterabfrage: {e}")
            dispatcher.utter_message("Es gab einen Fehler bei der Wetterabfrage.")
        return []