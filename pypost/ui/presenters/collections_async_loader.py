"""Background collection load bridge for CollectionsPresenter."""

from __future__ import annotations


import logging

from typing import Callable

from PySide6.QtCore import QObject, Signal

from pypost.core.qt.collection_storage_gateway import CollectionStorageGateway
from pypost.core.lifecycle import TeardownResult
from pypost.core.request_manager import RequestManager
from pypost.core.storage_interface import StorageInterface

logger = logging.getLogger(__name__)


class CollectionsAsyncLoader(QObject):
    """Dispatches collection disk reads off the UI thread at startup."""

    collections_loaded = Signal()

    def __init__(
        self,
        request_manager: RequestManager,
        storage: StorageInterface,
        refresh_tree: Callable[[], None],
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._request_manager = request_manager
        self._refresh_tree = refresh_tree
        self._gateway = CollectionStorageGateway(storage, parent=self)
        self._gateway.load_completed.connect(self._on_load_completed)
        self._gateway.load_failed.connect(self._on_load_failed)

    def is_busy(self) -> bool:
        return self._gateway.has_pending_work()

    def try_load_async(self) -> bool:
        """Dispatch load if idle. Returns False when skipped because busy."""
        if self.is_busy():
            logger.info("load_collections_skipped reason=busy")
            return False
        self.load_async()
        return True

    def load_async(self) -> None:
        logger.info("collection_storage_async_load_dispatched")
        self._gateway.load_async()

    def teardown(self, timeout_ms: int = 5000) -> TeardownResult:
        """Fence completion delivery and drain the startup loader."""
        return self._gateway.teardown(timeout_ms)

    def _on_load_completed(self, collections: list) -> None:
        self._finish_load(collections)

    def _on_load_failed(self, error: object) -> None:
        logger.error("collection_storage_async_load_failed error=%s", error)
        self._finish_load([])

    def _finish_load(self, collections: list) -> None:
        self._request_manager.apply_loaded_collections(collections)
        self._refresh_tree()
        self.collections_loaded.emit()
