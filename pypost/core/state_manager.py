from typing import List, Optional
from pypost.core.config_manager import ConfigManager
from pypost.models.settings import AppSettings

class StateManager:
    """
    Manages the persistent state of the UI, abstracting the AppSettings structure.
    """
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        # We assume settings are already loaded or load them on demand.
        # For simplicity, we'll keep a reference to the settings object managed by ConfigManager
        # but in a real app we might want to reload or sync more explicitly.
        self.settings: AppSettings = self.config_manager.load_config()

    def save(self):
        """Persists the current state to disk."""
        self.config_manager.save_config(self.settings)

    def get_expanded_collections(self) -> List[str]:
        return self.settings.expanded_collections

    def set_expanded_collections(self, ids: List[str]):
        if self.settings.expanded_collections != ids:
            self.settings.expanded_collections = ids
            self.save()

    def get_open_tabs(self) -> List[str]:
        return self.settings.open_tabs

    def set_open_tabs(self, ids: List[str]):
        if self.settings.open_tabs != ids:
            self.settings.open_tabs = ids
            self.save()

    def get_last_environment_id(self) -> Optional[str]:
        return self.settings.last_environment_id

    def set_last_environment_id(self, env_id: Optional[str]):
        if self.settings.last_environment_id != env_id:
            self.settings.last_environment_id = env_id
            self.save()

