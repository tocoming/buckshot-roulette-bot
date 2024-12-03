import json
import os
from typing import Dict

from logger import logger 

class I18n:
    def __init__(self, locale_path: str, default_lang: str = "eng"):
        self.translations = self.load_translations(locale_path)
        self.default_lang = default_lang

    def load_translations(self, locale_path: str) -> Dict[str, Dict[str, str]]:
        if not os.path.exists(locale_path):
            logger.error(f"Translation file not found at {locale_path}")
            return {}
        with open(locale_path, "r", encoding="utf-8") as f:
            try:
                translations = json.load(f)
                logger.info("Translations loaded successfully.")
                return translations
            except json.JSONDecodeError as e:
                logger.error(f"Error loading translations: {e}")
                return {}

    def get(self, lang: str, key: str, **kwargs) -> str:
        lang_translations = self.translations.get(lang, {})
        message = lang_translations.get(key, self.translations[self.default_lang].get(key, f"[[{key}]]"))
        try:
            return message.format(**kwargs)
        except KeyError as e:
            logger.error(f"Missing placeholder {e} in key '{key}' for language '{lang}'")
            return message
