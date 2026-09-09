"""UI session state persistence for PyPost.

Design contract (see doc/dev/state_manager.md):

- ``StateManager`` owns persistence for high-churn UI fields only
  (``expanded_collections``, ``open_tabs``, ``last_environment_id``).
- It holds a reference to the same ``AppSettings`` instance loaded by
  ``ConfigManager``; ``MainWindow.settings`` points at that object. Shared
  mutability is intentional so preference fields edited in the Settings dialog
  remain visible everywhere without a reload.
- Granular updates: each ``set_*`` method compares values and skips scheduling
  when unchanged; disk writes still serialize the full settings file via
  ``ConfigManager.save_config`` (acceptable for current file size).
- User preference changes bypass debounce and save immediately through
  ``ConfigManager`` in ``MainWindow.open_settings()``.
"""
from __future__ import annotations

import logging
from typing import Final, List, Optional, Tuple

from PySide6.QtCore import QObject, QTimer, Signal

from pypost.core.config_manager import ConfigManager, ConfigPersistenceError
from pypost.models.settings import AppSettings

logger = logging.getLogger(__name__)

_UI_STATE_SAVE_DEBOUNCE_MS = 300
_UI_STATE_FIELDS: Final[Tuple[str, ...]] = (
    "expanded_collections",
    "open_tabs",
    "last_environment_id",
)


class StateManager(QObject):
    """
    Persists UI session state with debounced disk writes.

    Call ``flush_pending_save()`` before application shutdown so pending UI
    changes are not lost inside the debounce window.
    """

    persistence_failed = Signal(str)

    def __init__(
        self,
        config_manager: ConfigManager,
        settings: AppSettings,
        parent: QObject | None = None,
    ):
        super().__init__(parent)
        self.config_manager = config_manager
        self.settings = settings
        self._save_pending = False
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(_UI_STATE_SAVE_DEBOUNCE_MS)
        self._save_timer.timeout.connect(self._on_debounced_save_timeout)

    def save(self) -> None:
        """Persists the current state to disk immediately."""
        self._save_timer.stop()
        try:
            self.config_manager.save_config(self.settings)
        except ConfigPersistenceError as exc:
            self._save_pending = True
            self.persistence_failed.emit(str(exc))
            raise
        self._save_pending = False
        logger.debug("state_manager_save_immediate")

    def flush_pending_save(self) -> None:
        """Write pending UI state to disk without waiting for the debounce timer."""
        if not self._save_pending:
            return
        self.save()

    def get_expanded_collections(self) -> List[str]:
        return list(self.settings.expanded_collections)

    def set_expanded_collections(self, ids: List[str]) -> None:
        if self.settings.expanded_collections != ids:
            self.settings.expanded_collections = list(ids)
            self._schedule_save()

    def get_open_tabs(self) -> List[str]:
        return list(self.settings.open_tabs)

    def set_open_tabs(self, ids: List[str]) -> None:
        if self.settings.open_tabs != ids:
            self.settings.open_tabs = list(ids)
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
        try:
            self.save()
        except ConfigPersistenceError as exc:
            logger.error("state_manager_save_debounced_failed error=%s", exc)
            return
        logger.debug("state_manager_save_debounced")
