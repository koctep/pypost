"""Background collection load bridge for CollectionsPresenter."""

import logging

from typing import Callable

from PySide6.QtCore import QObject, Signal

from pypost.core.collection_storage_gateway import CollectionStorageGateway
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

    def load_async(self) -> None:
        logger.info("collection_storage_async_load_dispatched")
        self._gateway.load_async()

    def _on_load_completed(self, collections: list) -> None:
        self._finish_load(collections)

    def _on_load_failed(self, error: object) -> None:
        logger.error("collection_storage_async_load_failed error=%s", error)
        self._finish_load([])

    def _finish_load(self, collections: list) -> None:
        self._request_manager.apply_loaded_collections(collections)
        self._refresh_tree()
        self.collections_loaded.emit()
