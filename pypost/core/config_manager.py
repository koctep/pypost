import json
import os
from pathlib import Path
from platformdirs import user_config_dir
from pypost.models.settings import AppSettings

class ConfigManager:
    def __init__(self, app_name="pypost", app_author=None):
        self.config_dir = Path(user_config_dir(app_name, app_author))
        self.config_path = self.config_dir / "settings.json"
        self._ensure_config_dir()

    def _ensure_config_dir(self):
        if not self.config_dir.exists():
            try:
                self.config_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                print(f"Error creating config directory: {e}")

    def load_config(self) -> AppSettings:
        if not self.config_path.exists():
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
            # Increment revision before saving
            settings.revision += 1
            
            with open(self.config_path, 'w') as f:
                json.dump(settings.model_dump(), f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")
