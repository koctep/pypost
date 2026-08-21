from __future__ import annotations

import json
import logging
from pathlib import Path

from platformdirs import user_config_dir

from pypost.core.settings_secrets import parse_settings_from_disk, serialize_settings_for_disk
from pypost.models.settings import AppSettings

logger = logging.getLogger(__name__)


class StrictConfigError(Exception):
    def __init__(self, path: Path, category: str) -> None:
        self.path = path
        self.category = category
        super().__init__(f"settings failure path={path} category={category}")


class ConfigManager:
    def __init__(
        self,
        app_name="pypost",
        app_author=None,
        *,
        config_dir: Path | str | None = None,
    ):
        if config_dir is not None:
            self.config_dir = Path(config_dir)
        else:
            self.config_dir = Path(user_config_dir(app_name, app_author))
        self.config_path = self.config_dir / "settings.json"
        self._ensure_config_dir()

    def _ensure_config_dir(self):
        if not self.config_dir.exists():
            try:
                self.config_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                logger.error("config_directory_create_failed path=%s error=%s", self.config_dir, e)

    def load_config(self) -> AppSettings:
        if not self.config_path.exists():
            return AppSettings()
        try:
            with open(self.config_path, "r") as f:
                data = json.load(f)
                return parse_settings_from_disk(data)
        except Exception as e:
            logger.error("config_load_failed path=%s error=%s", self.config_path, e)
            return AppSettings()

    def load_config_strict(self) -> AppSettings:
        if not self.config_path.exists():
            return AppSettings()
        try:
            with open(self.config_path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            if not isinstance(data, dict):
                raise StrictConfigError(self.config_path, "invalid_root")
            return parse_settings_from_disk(data)
        except StrictConfigError:
            raise
        except json.JSONDecodeError as exc:
            raise StrictConfigError(self.config_path, "malformed_json") from exc
        except OSError as exc:
            raise StrictConfigError(self.config_path, "unreadable") from exc
        except Exception as exc:
            raise StrictConfigError(self.config_path, "invalid_settings") from exc

    def save_config(self, settings: AppSettings):
        try:
            # Increment revision before saving
            settings.revision += 1

            with open(self.config_path, "w") as f:
                json.dump(serialize_settings_for_disk(settings), f, indent=4)
        except Exception as e:
            logger.error("config_save_failed path=%s error=%s", self.config_path, e)
