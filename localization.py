import json
import os
from typing import Dict, List

class Localization:
    def __init__(self):
        self.current_language = "en"
        self.translations: Dict[str, Dict] = {}
        self.load_languages()
    
    def load_languages(self):
        """Load all language files from the languages directory."""
        languages_dir = os.path.join(os.path.dirname(__file__), "languages")
        if not os.path.exists(languages_dir):
            os.makedirs(languages_dir)
        
        # Load each language file
        for filename in os.listdir(languages_dir):
            if filename.endswith(".json"):
                lang_code = filename[:-5]  # Remove .json extension
                try:
                    with open(os.path.join(languages_dir, filename), 'r', encoding='utf-8') as f:
                        self.translations[lang_code] = json.load(f)
                except Exception as e:
                    print(f"Error loading language file {filename}: {e}")
    
    def get_available_languages(self) -> List[str]:
        """Get list of available language names."""
        return list(self.translations.keys())
    
    def set_language(self, language_code: str):
        """Set the current language."""
        if language_code in self.translations:
            self.current_language = language_code
    
    def get_text(self, key: str, default: str = "") -> str:
        """Get translated text for a key."""
        try:
            # Handle nested keys (e.g., "token_table.lexeme")
            keys = key.split('.')
            value = self.translations[self.current_language]
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def get_current_language(self) -> str:
        """Get the current language code."""
        return self.current_language 