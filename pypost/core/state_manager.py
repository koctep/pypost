import logging
from typing import List, Optional

from PySide6.QtCore import QObject, QTimer

from pypost.core.config_manager import ConfigManager
from pypost.models.settings import AppSettings

logger = logging.getLogger(__name__)

_UI_STATE_SAVE_DEBOUNCE_MS = 300


class StateManager(QObject):
    """
    Manages the persistent state of the UI, abstracting the AppSettings structure.

    UI-driven mutations are debounced to reduce redundant disk writes; call
    flush_pending_save() before application shutdown.
    """

    def __init__(self, config_manager: ConfigManager, parent: QObject | None = None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.settings: AppSettings = self.config_manager.load_config()
        self._save_pending = False
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(_UI_STATE_SAVE_DEBOUNCE_MS)
        self._save_timer.timeout.connect(self._on_debounced_save_timeout)

    def save(self) -> None:
        """Persists the current state to disk immediately."""
        self._save_timer.stop()
        self._save_pending = False
        self.config_manager.save_config(self.settings)
        logger.debug("state_manager_save_immediate")

    def flush_pending_save(self) -> None:
        """Write pending UI state to disk without waiting for the debounce timer."""
        if not self._save_pending:
            return
        self.save()

    def get_expanded_collections(self) -> List[str]:
        return self.settings.expanded_collections

    def set_expanded_collections(self, ids: List[str]) -> None:
        if self.settings.expanded_collections != ids:
            self.settings.expanded_collections = ids
            self._schedule_save()

    def get_open_tabs(self) -> List[str]:
        return self.settings.open_tabs

    def set_open_tabs(self, ids: List[str]) -> None:
        if self.settings.open_tabs != ids:
            self.settings.open_tabs = ids
            self._schedule_save()

    def get_last_environment_id(self) -> Optional[str]:
        return self.settings.last_environment_id

    def set_last_environment_id(self, env_id: Optional[str]) -> None:
        if self.settings.last_environment_id != env_id:
            self.settings.last_environment_id = env_id
            self._schedule_save()

    def _schedule_save(self) -> None:
        self._save_pending = True
        self._save_timer.start()
        logger.debug(
            "state_manager_save_scheduled debounce_ms=%d",
            _UI_STATE_SAVE_DEBOUNCE_MS,
        )

    def _on_debounced_save_timeout(self) -> None:
        if not self._save_pending:
            return
        self._save_pending = False
        self.config_manager.save_config(self.settings)
        logger.debug("state_manager_save_debounced")
