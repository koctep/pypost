from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from pypost.models.mcp_client import McpClientConnection
from pypost.models.models import Collection

if TYPE_CHECKING:
    from pypost.core.request_manager import RequestManager
    from pypost.core.storage_interface import StorageInterface

logger = logging.getLogger(__name__)


class McpClientRegistry:
    """In-memory index service managing MCP Client profiles across collections."""

    def __init__(
        self, request_manager: RequestManager, storage: Optional[StorageInterface] = None
    ) -> None:
        self.request_manager = request_manager
        self.storage = storage
        self._index: Dict[str, Tuple[McpClientConnection, Collection]] = {}
        self.rebuild_index()

    def rebuild_index(self) -> None:
        """Rebuilds the internal index of MCP Client profiles for O(1) access."""
        self._index.clear()
        for col in self.request_manager.get_collections():
            for profile in getattr(col, "mcp_clients", []):
                self._index[profile.id] = (profile, col)
        logger.debug(
            "mcp_client_registry_index_rebuilt indexed_count=%d",
            len(self._index),
        )

    def drop_collection_mcp_clients_from_index(self, col: Collection) -> None:
        """Removes all indexed MCP Client profiles belonging to *col*."""
        removed = 0
        for profile in getattr(col, "mcp_clients", []):
            if self._index.pop(profile.id, None) is not None:
                removed += 1
        logger.debug(
            "drop_collection_mcp_clients_from_index col_id=%s count=%d",
            col.id,
            removed,
        )

    def get_mcp_clients(self) -> List[McpClientConnection]:
        """Returns all indexed MCP Client profiles."""
        return [profile for profile, _ in self._index.values()]

    def find_mcp_client(
        self, profile_id: str
    ) -> Optional[Tuple[McpClientConnection, Collection]]:
        """Find a profile by ID. Returns (McpClientConnection, Collection) or None."""
        return self._index.get(profile_id)

    def save_mcp_client(self, profile: McpClientConnection, collection_id: str) -> None:
        """Saves an MCP Client profile to the specified collection."""
        logger.info(
            "save_mcp_client_started profile_id=%s col_id=%s",
            profile.id,
            collection_id,
        )
        cols = self.request_manager.get_collections()
        target = next((c for c in cols if c.id == collection_id), None)
        if not target:
            logger.warning(
                "save_mcp_client_not_found profile_id=%s col_id=%s",
                profile.id,
                collection_id,
            )
            raise ValueError(f"Collection with ID {collection_id} not found")

        if not hasattr(target, "mcp_clients"):
            target.mcp_clients = []

        for i, existing in enumerate(target.mcp_clients):
            if existing.id == profile.id:
                target.mcp_clients[i] = profile
                break
        else:
            target.mcp_clients.append(profile)

        if self.storage is not None:
            self.storage.save_collection(target)
        self._index[profile.id] = (profile, target)
        logger.info(
            "save_mcp_client_succeeded profile_id=%s col_id=%s",
            profile.id,
            collection_id,
        )

    def delete_mcp_client(self, profile_id: str) -> bool:
        """Deletes an MCP Client profile by ID from its owning collection."""
        logger.info("delete_mcp_client_started profile_id=%s", profile_id)
        indexed = self._index.get(profile_id)
        if not indexed:
            logger.warning("delete_mcp_client_not_found profile_id=%s", profile_id)
            return False

        _, col = indexed
        for i, profile in enumerate(col.mcp_clients):
            if profile.id == profile_id:
                del col.mcp_clients[i]
                break
        if self.storage is not None:
            self.storage.save_collection(col)
        self._index.pop(profile_id, None)
        logger.info(
            "delete_mcp_client_succeeded profile_id=%s collection_id=%s",
            profile_id,
            col.id,
        )
        return True

    def rename_mcp_client(self, profile_id: str, new_name: str) -> bool:
        """Renames a profile by ID and persists the parent collection."""
        logger.info("rename_mcp_client_started profile_id=%s", profile_id)
        normalized_name = new_name.strip()
        if not normalized_name:
            logger.warning(
                "rename_mcp_client_rejected_empty_name profile_id=%s",
                profile_id,
            )
            return False

        indexed = self._index.get(profile_id)
        if not indexed:
            logger.warning("rename_mcp_client_not_found profile_id=%s", profile_id)
            return False

        profile, col = indexed
        profile.name = normalized_name
        if self.storage is not None:
            self.storage.save_collection(col)
        logger.info(
            "rename_mcp_client_succeeded profile_id=%s collection_id=%s",
            profile_id,
            col.id,
        )
        return True

    def find_item(self, item_id: str) -> Optional[Tuple[str, object, Collection]]:
        """Resolve an ID in O(1) to ('mcp_client', McpClientConnection, collection)."""
        match = self._index.get(item_id)
        if match is not None:
            profile, col = match
            logger.debug(
                "find_item_resolved item_id=%s kind=mcp_client col_id=%s",
                item_id,
                col.id,
            )
            return ("mcp_client", profile, col)

        logger.debug("find_item_not_found item_id=%s", item_id)
        return None
