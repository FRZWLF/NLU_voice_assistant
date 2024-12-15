from rasa_sdk import Action
from rasa_sdk.events import SlotSet
from wikipedia import wikipedia


class ActionTellWiki(Action):
    def name(self) -> str:
        return "action_tell_wiki"

    def run(self, dispatcher, tracker, domain):
        entities = tracker.latest_message["entities"]
        print(f"Wiki query: {entities}")
        query = next((ent["value"] for ent in entities), None)
        print(f"Wiki query: {query}")

        if not query:
            dispatcher.utter_message(text="Ich konnte kein Thema erkennen. Bitte gib ein Thema an.")
            return []

        wikipedia.set_lang("de")

        try:
            # Versuche eine Zusammenfassung zu holen
            summary = wikipedia.summary(query, sentences=2, auto_suggest=True)
            dispatcher.utter_message(text=f"{summary}")
            dispatcher.utter_message(text=f"Möchtest du mehr über {query} erfahren?")
            return [SlotSet("wiki_query", query)]
        except wikipedia.exceptions.PageError:
            # Kein Artikel gefunden
            dispatcher.utter_message(text=f"Ich konnte keinen Artikel zu '{query}' finden.")
        except Exception as e:
            # Allgemeiner Fehler
            dispatcher.utter_message(text="Es gab ein Problem beim Abrufen der Informationen.")
            print(f"Fehler: {e}")

        return []


class ActionTellMoreWiki(Action):
    def name(self):
        return "action_tell_more_wiki"

    def run(self, dispatcher, tracker, domain):
        query = tracker.get_slot("wiki_query")
        intent = tracker.get_intent_of_latest_message()

        if intent == "affirm":
            if query:
                summary = wikipedia.summary(query, sentences=10)
                dispatcher.utter_message(text=f"{summary}")
            else:
                dispatcher.utter_message(text="Ich konnte das Thema nicht abrufen. Bitte starte die Anfrage erneut.")
        elif intent == "deny":
            dispatcher.utter_message(response = "utter_end_by_deny")

        return [SlotSet("wiki_query", None)]