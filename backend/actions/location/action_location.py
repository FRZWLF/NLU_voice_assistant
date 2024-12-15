import geocoder
from rasa_sdk import Action


class ActionTellLocation(Action):
    def name(self) -> str:
        return "action_tell_location"

    def run(self, dispatcher, tracker, domain):
        loc = geocoder.ip('me')
        return dispatcher.utter_message(text=f"Du befindest dich in {loc.city}.")