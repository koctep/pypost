from typing import List, Optional
from pypost.core.config_manager import ConfigManager
from pypost.models.settings import AppSettings

class StateManager:
    """Single owner of the application settings.

    Everything that reads or writes settings goes through here, so there is one
    in-memory copy and one path to disk. Loading a second copy elsewhere, or
    writing straight to ConfigManager, puts the two out of step and whichever
    saves last wins.
    """
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self._settings: AppSettings = self.config_manager.load_config()

    @property
    def settings(self) -> AppSettings:
        return self._settings

    def replace_settings(self, settings: AppSettings) -> None:
        """Adopt a new settings object and persist it."""
        if settings is self._settings:
            return
        self._settings = settings
        self.save()

    def save(self):
        """Persists the current state to disk."""
        self.config_manager.save_config(self._settings)

    def get_expanded_collections(self) -> List[str]:
        # Copy, so a caller mutating the result cannot silently edit stored state and
        # then compare equal to it in the setter below.
        return list(self._settings.expanded_collections)

    def set_expanded_collections(self, ids: List[str]):
        if self._settings.expanded_collections != ids:
            self._settings.expanded_collections = list(ids)
            self.save()

    def get_open_tabs(self) -> List[str]:
        return list(self._settings.open_tabs)

    def set_open_tabs(self, ids: List[str]):
        if self._settings.open_tabs != ids:
            self._settings.open_tabs = list(ids)
            self.save()

    def get_last_environment_id(self) -> Optional[str]:
        return self._settings.last_environment_id

    def set_last_environment_id(self, env_id: Optional[str]):
        if self._settings.last_environment_id != env_id:
            self._settings.last_environment_id = env_id
            self.save()

