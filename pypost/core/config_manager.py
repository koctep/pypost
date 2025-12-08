import json
import os
from pypost.models.settings import AppSettings

class ConfigManager:
    def __init__(self, config_path="settings.json"):
        self.config_path = config_path

    def load_config(self) -> AppSettings:
        if not os.path.exists(self.config_path):
            return AppSettings()
        
        try:
            with open(self.config_path, 'r') as f:
                data = json.load(f)
                return AppSettings(**data)
        except Exception as e:
            print(f"Error loading config: {e}")
            return AppSettings()

    def save_config(self, settings: AppSettings):
        try:
            with open(self.config_path, 'w') as f:
                json.dump(settings.model_dump(), f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

