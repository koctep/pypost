import json
import logging
import os
from pathlib import Path

from platformdirs import user_config_dir

from pypost.models.settings import AppSettings


logger = logging.getLogger(__name__)


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
        next_revision = settings.revision + 1
        data = settings.model_dump()
        data["revision"] = next_revision
        tmp_path = self.config_path.with_suffix(".json.tmp")

        try:
            with open(tmp_path, 'w') as f:
                json.dump(data, f, indent=4)
            os.replace(tmp_path, self.config_path)
        except Exception as e:
            tmp_path.unlink(missing_ok=True)
            logger.error(
                "config_save_failed path=%s error=%s", self.config_path, e
            )
            raise

        settings.revision = next_revision
