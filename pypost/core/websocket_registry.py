from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from pypost.models.models import Collection
from pypost.models.websocket import WebSocketConnection

if TYPE_CHECKING:
    from pypost.core.request_manager import RequestManager
    from pypost.core.storage_interface import StorageInterface

logger = logging.getLogger(__name__)


class WebSocketRegistry:
    """In-memory index service managing WebSocket profiles across loaded collections."""

    def __init__(
        self,
        request_manager: RequestManager,
        storage: StorageInterface,
    ) -> None:
        self.request_manager = request_manager
        self.storage = storage
        self._ws_index: Dict[str, Tuple[WebSocketConnection, Collection]] = {}
        self.rebuild_index()

    def rebuild_index(self) -> None:
        """Rebuilds the internal index of websockets for O(1) access."""
        self._ws_index.clear()
        for col in self.request_manager.get_collections():
            for ws in getattr(col, "websockets", []):
                self._ws_index[ws.id] = (ws, col)
        logger.debug("websocket_registry_index_rebuilt indexed_count=%d", len(self._ws_index))

    def drop_collection_websockets_from_index(self, col: Collection) -> None:
        """Removes all indexed websockets belonging to the given collection."""
        removed = 0
        for ws in getattr(col, "websockets", []):
            if self._ws_index.pop(ws.id, None) is not None:
                removed += 1
        logger.debug("drop_collection_websockets_from_index col_id=%s count=%d", col.id, removed)

    def get_websockets(self) -> List[WebSocketConnection]:
        """Returns all indexed WebSocketConnection instances."""
        return [conn for conn, _ in self._ws_index.values()]

    def find_websocket(self, ws_id: str) -> Optional[Tuple[WebSocketConnection, Collection]]:
        """Finds a websocket profile by ID. Returns (WebSocketConnection, Collection) or None."""
        return self._ws_index.get(ws_id)

    def save_websocket(self, conn: WebSocketConnection, collection_id: str) -> None:
        """Saves a websocket profile to the specified collection."""
        logger.info("save_websocket_started ws_id=%s col_id=%s", conn.id, collection_id)
        target = next(
            (c for c in self.request_manager.get_collections() if c.id == collection_id),
            None,
        )
        if not target:
            logger.warning("save_websocket_not_found ws_id=%s col_id=%s", conn.id, collection_id)
            raise ValueError(f"Collection with ID {collection_id} not found")

        if not hasattr(target, "websockets"):
            target.websockets = []

        for i, existing in enumerate(target.websockets):
            if existing.id == conn.id:
                target.websockets[i] = conn
                break
        else:
            target.websockets.append(conn)

        self.storage.save_collection(target)
        self._ws_index[conn.id] = (conn, target)
        logger.info("save_websocket_succeeded ws_id=%s col_id=%s", conn.id, collection_id)

    def delete_websocket(self, ws_id: str) -> bool:
        """Deletes a websocket profile by ID from its owning collection."""
        logger.info("delete_websocket_started ws_id=%s", ws_id)
        indexed = self._ws_index.get(ws_id)
        if not indexed:
            logger.warning("delete_websocket_not_found ws_id=%s", ws_id)
            return False

        _, col = indexed
        for i, ws in enumerate(col.websockets):
            if ws.id == ws_id:
                del col.websockets[i]
                break
        self.storage.save_collection(col)
        self._ws_index.pop(ws_id, None)
        logger.info("delete_websocket_succeeded ws_id=%s collection_id=%s", ws_id, col.id)
        return True

    def rename_websocket(self, ws_id: str, new_name: str) -> bool:
        """Renames a websocket profile by ID and persists the parent collection."""
        logger.info("rename_websocket_started ws_id=%s", ws_id)
        normalized_name = new_name.strip()
        if not normalized_name:
            logger.warning("rename_websocket_rejected_empty_name ws_id=%s", ws_id)
            return False

        indexed = self._ws_index.get(ws_id)
        if not indexed:
            logger.warning("rename_websocket_not_found ws_id=%s", ws_id)
            return False

        conn, col = indexed
        conn.name = normalized_name
        self.storage.save_collection(col)
        logger.info("rename_websocket_succeeded ws_id=%s collection_id=%s", ws_id, col.id)
        return True

    def find_item(self, item_id: str) -> Optional[Tuple[str, object, Collection]]:
        """Resolve an ID in O(1) to ('request' | 'websocket', object, owning_collection)."""
        req_match = self.request_manager.find_request(item_id)
        if req_match is not None:
            req, col = req_match
            logger.debug("find_item_resolved item_id=%s kind=request col_id=%s", item_id, col.id)
            return ("request", req, col)

        ws_match = self._ws_index.get(item_id)
        if ws_match is not None:
            conn, col = ws_match
            logger.debug("find_item_resolved item_id=%s kind=websocket col_id=%s", item_id, col.id)
            return ("websocket", conn, col)

        logger.debug("find_item_not_found item_id=%s", item_id)
        return None
