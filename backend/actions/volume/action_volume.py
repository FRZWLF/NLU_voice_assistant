import os
import yaml
from loguru import logger
from rasa_sdk import Action
from rasa_sdk.events import FollowupAction
from socketio import Client
from transformers import MarianMTModel, MarianTokenizer
from typing import Sequence

from words2num import w2n

sio = Client()
sio.connect("http://127.0.0.1:5000")
CONFIG_FILE = "config_ai_assistant.yml"

def __read_config__():
    with open(CONFIG_FILE, "r", encoding='utf8') as ymlfile:
        cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)
    return cfg

def __write_config__(cfg):
    with open(CONFIG_FILE, 'w', encoding="utf-8") as ymlfile:
        yaml.dump(cfg, ymlfile, default_flow_style=False, allow_unicode=True)

class Translator:
    def __init__(self, source_lang: str, dest_lang: str, model_dir="./MarianMTModel") -> None:
        if source_lang == dest_lang:
            self.is_identity_translation = True
            return

        self.is_identity_translation = False
        if dest_lang == "ja":
            dest_lang = "jap"

        self.model_name = f"opus-mt-{source_lang}-{dest_lang}"
        self.model_path = os.path.join(model_dir, self.model_name)

        # Lade das Modell und den Tokenizer aus dem lokalen Verzeichnis
        self.model = MarianMTModel.from_pretrained(self.model_path, local_files_only=True)
        self.tokenizer = MarianTokenizer.from_pretrained(self.model_path, local_files_only=True)

    def translate(self, texts: Sequence[str]) -> Sequence[str]:
        if self.is_identity_translation:
            return texts

        # Falls texts ein einzelner String ist, wandle ihn in eine Liste um
        if isinstance(texts, str):
            texts = [texts]

        tokens = self.tokenizer(list(texts), return_tensors="pt", padding=True)
        translate_tokens = self.model.generate(**tokens)
        return [self.tokenizer.decode(t, skip_special_tokens=True) for t in translate_tokens]



class ActionGetVolume(Action):
    def name(self) -> str:
        return "action_get_volume"

    def run(self, dispatcher, tracker, domain):
        CONFIG_FILE = "config_ai_assistant.yml"
        with open(CONFIG_FILE,'r',encoding="utf-8") as ymlfile:
            cfg = yaml.load(ymlfile,Loader=yaml.FullLoader)

        volume = int(cfg['assistant']['volume'] * 10)
        logger.info("Lautstärke ist {} von zehn.", volume)
        return dispatcher.utter_message(text=f"Die Lautstärke ist {volume} von 10.")


def parse_volume_input(volume_input: str) -> int:
    """
    Versucht, eine Zahl oder ein Zahlenwort in eine Ganzzahl zu konvertieren.
    """
    try:
        # Versuche, den Text direkt als Zahl zu interpretieren
        return int(volume_input)
    except ValueError:
        try:
            # Konvertiere das Zahlenwort in eine Zahl
            return w2n(volume_input.lower())
        except ValueError:
            raise ValueError("Ungültige Eingabe, keine Zahl erkannt.")


class ActionMaxVolume(Action):
    def name(self) -> str:
        return "action_max_volume"

    def run(self, dispatcher, tracker, domain):
        max_volume = round(10.0 / 10.0, 1)
        sio.emit('set_volume', max_volume)
        cfg = __read_config__()
        cfg['assistant']['volume'] = max_volume
        __write_config__(cfg)
        return dispatcher.utter_message(text=f"Die Lautstärke ist {int(max_volume * 10)} von 10.")

class ActionSetVolume(Action):
    def name(self) -> str:
        return "action_set_volume"

    def run(self, dispatcher, tracker, domain):
        volume = tracker.get_slot("volume_change")
        logger.debug(f"DEBUG: Volume slot: {volume}")
        cfg = __read_config__()
        language = cfg['assistant']['language']

        if volume == "":
            logger.debug("Ich habe keine volume")
            return [FollowupAction("action_get_volume")]
        translator = Translator(language, "en")
        volume = translator.translate(volume)[0].lower()
        try:
            num_vol = parse_volume_input(volume)
        except ValueError:
            return dispatcher.utter_message(text="Bitte nenne eine Lautstärke zwischen 0 und 10")

        if num_vol < 0 or num_vol > 10:
            logger.info("Lautstärke {} ist ungültig, nur Werte von 0 - 10 sind erlaubt.", num_vol)
            return dispatcher.utter_message(text="Bitte nenne eine Lautstärke zwischen 0 und 10")
        else:
            new_volume = round(num_vol / 10.0, 1)
            sio.emit('set_volume', new_volume)
            cfg['assistant']['volume'] = new_volume
            __write_config__(cfg)
            return dispatcher.utter_message(text=f"Die Lautstärke ist {int(new_volume * 10)} von 10.")


class ActionVolumeUp(Action):
    def name(self) -> str:
        return "action_volume_up"

    def run(self, dispatcher, tracker, domain):
        cfg = __read_config__()
        vol_up = 1

        # Prüfe die Eingabe des Nutzers
        user_message = tracker.latest_message.get("text", "").lower()

        if "ein bisschen" in user_message:
            vol_up = 1
        elif "viel" in user_message or "deutlich" in user_message:
            vol_up = 2

        vol = cfg['assistant']['volume']

        new_volume = round(min(1.0, (vol + vol_up / 10.0)), 1)
        logger.info("Setze Lautstärke von {} auf {}.", vol, new_volume)
        logger.debug("Setze Lautstärke auf {}.", new_volume)
        sio.emit('set_volume', new_volume)
        cfg['assistant']['volume'] = new_volume
        __write_config__(cfg)
        return dispatcher.utter_message(text=f"Die Lautstärke ist {int(new_volume * 10)} von 10.")


class ActionVolumeDown(Action):
    def name(self) -> str:
        return "action_volume_down"

    def run(self, dispatcher, tracker, domain):
        cfg = __read_config__()
        vol_down = 1

        # Prüfe die Eingabe des Nutzers
        user_message = tracker.latest_message.get("text", "").lower()

        if "ein bisschen" in user_message:
            vol_down = 1
        elif "viel" in user_message or "deutlich" in user_message:
            vol_down = 2

        vol = cfg['assistant']['volume']

        new_volume = round(max(0.0, (vol - vol_down / 10.0)), 1)
        logger.info("Setze Lautstärke von {} auf {}.", vol, new_volume)
        logger.debug("Setze Lautstärke auf {}.", new_volume)
        sio.emit('set_volume', new_volume)
        cfg['assistant']['volume'] = new_volume
        __write_config__(cfg)
        return dispatcher.utter_message(text=f"Die Lautstärke ist {int(new_volume * 10)} von 10.")