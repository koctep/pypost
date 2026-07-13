import logging
from typing import Dict, List, Optional, Tuple

from pypost.core.collection_item_strategies import (
    DEFAULT_COLLECTION_ITEM_STRATEGIES,
    CollectionItemStrategy,
)
from pypost.core.storage_interface import StorageInterface
from pypost.models.models import Collection, RequestData

logger = logging.getLogger(__name__)


class RequestManager:
    """
    Manages the lifecycle of requests and collections, abstracting storage operations.
    """

    def __init__(
        self,
        storage_manager: StorageInterface,
        *,
        item_strategies: dict[str, CollectionItemStrategy] | None = None,
        defer_initial_load: bool = False,
    ):
        self.storage = storage_manager
        self.collections: List[Collection] = []
        self._request_index: Dict[str, Tuple[RequestData, Collection]] = {}
        self._item_strategies = (
            item_strategies
            if item_strategies is not None
            else DEFAULT_COLLECTION_ITEM_STRATEGIES
        )
        if not defer_initial_load:
            self.reload_collections()

    def reload_collections(self):
        """Reloads collections from storage."""
        self.collections = self.storage.load_collections()
        self._rebuild_index()

    def apply_loaded_collections(self, collections: List[Collection]) -> None:
        """Applies collections loaded off the main thread and rebuilds the index."""
        self.collections = collections
        self._rebuild_index()
        logger.info(
            "apply_loaded_collections_completed collection_count=%d request_count=%d",
            len(self.collections),
            len(self._request_index),
        )

    def _rebuild_index(self):
        """Rebuilds the internal index of requests for O(1) access."""
        self._request_index.clear()
        for col in self.collections:
            for req in col.requests:
                self._request_index[req.id] = (req, col)

    def _drop_request_from_index(self, request_id: str) -> None:
        """Removes one request from the lookup index without a full rebuild."""
        self._request_index.pop(request_id, None)

    def _drop_collection_requests_from_index(self, collection: Collection) -> None:
        """Removes all requests in a collection from the lookup index."""
        for req in collection.requests:
            self._drop_request_from_index(req.id)

    def get_collections(self) -> List[Collection]:
        return self.collections

    def find_request(self, request_id: str) -> Optional[Tuple[RequestData, Collection]]:
        """
        Finds a request by ID.
        Returns a tuple (RequestData, Collection) or None if not found.
        """
        return self._request_index.get(request_id)

    def save_request(self, request: RequestData, collection_id: str):
        """
        Saves a request to the specified collection.
        Updates the request if it exists, or adds it if it's new.
        """
        target_collection = None
        for col in self.collections:
            if col.id == collection_id:
                target_collection = col
                break

        if not target_collection:
            raise ValueError(f"Collection with ID {collection_id} not found")

        # Update or Add
        found = False
        for i, req in enumerate(target_collection.requests):
            if req.id == request.id:
                target_collection.requests[i] = request
                found = True
                break

        if not found:
            target_collection.requests.append(request)

        # Persist
        self.storage.save_collection(target_collection)

        # Update index
        self._rebuild_index()

    def _find_collection_by_name(self, name: str, *, exclude_id: str | None = None):
        normalized = name.strip()
        for col in self.collections:
            if col.id != exclude_id and col.name == normalized:
                return col
        return None

    def create_collection(self, name: str) -> Collection:
        """Creates a new collection."""
        import uuid

        normalized = name.strip()
        if not normalized:
            raise ValueError("Collection name cannot be empty")
        if self._find_collection_by_name(normalized):
            raise ValueError(f"Collection '{normalized}' already exists")

        new_col = Collection(id=str(uuid.uuid4()), name=normalized, requests=[])
        self.collections.append(new_col)
        self.storage.save_collection(new_col)
        return new_col

    def delete_request(self, request_id: str) -> bool:
        """Deletes a request by ID from its collection."""
        logger.info("delete_request_started request_id=%s", request_id)
        indexed = self._request_index.get(request_id)
        if not indexed:
            logger.warning("delete_request_not_found request_id=%s", request_id)
            return False

        _, col = indexed
        for i, req in enumerate(col.requests):
            if req.id == request_id:
                del col.requests[i]
                break
        self.storage.save_collection(col)
        self._drop_request_from_index(request_id)
        logger.info(
            "delete_request_succeeded request_id=%s collection_id=%s",
            request_id,
            col.id,
        )
        return True

    def delete_collection(self, collection_id: str) -> bool:
        """Deletes a collection by ID."""
        logger.info("delete_collection_started collection_id=%s", collection_id)
        for idx, col in enumerate(self.collections):
            if col.id == collection_id:
                self.storage.delete_collection(col.id, collection_name=col.name)
                self._drop_collection_requests_from_index(col)
                del self.collections[idx]
                logger.info(
                    "delete_collection_succeeded collection_id=%s collection_name=%s",
                    collection_id,
                    col.name,
                )
                return True
        logger.warning("delete_collection_not_found collection_id=%s", collection_id)
        return False

    def delete_collection_item(self, item_id: str, item_type: str) -> bool:
        """
        Deletes a collection item by type.
        Supported types: "collection", "request".
        """
        logger.info(
            "delete_collection_item_started item_id=%s item_type=%s",
            item_id,
            item_type,
        )
        strategy = self._item_strategies.get(item_type)
        if strategy is None:
            logger.warning(
                "delete_collection_item_unsupported_type item_id=%s item_type=%s",
                item_id,
                item_type,
            )
            return False
        return strategy.delete(self, item_id)

    def rename_request(self, request_id: str, new_name: str) -> bool:
        """Renames a request by ID and persists the parent collection."""
        normalized_name = new_name.strip()
        if not normalized_name:
            logger.warning("rename_request_rejected_empty_name request_id=%s", request_id)
            return False

        indexed = self._request_index.get(request_id)
        if not indexed:
            logger.warning("rename_request_not_found request_id=%s", request_id)
            return False

        req, col = indexed
        req.name = normalized_name
        self.storage.save_collection(col)
        logger.info(
            "rename_request_succeeded request_id=%s collection_id=%s",
            request_id,
            col.id,
        )
        return True

    def rename_collection(self, collection_id: str, new_name: str) -> bool:
        """Renames a collection by ID and updates stored collection file name."""
        normalized_name = new_name.strip()
        if not normalized_name:
            logger.warning("rename_collection_rejected_empty_name collection_id=%s", collection_id)
            return False

        if self._find_collection_by_name(normalized_name, exclude_id=collection_id):
            logger.warning(
                "rename_collection_rejected_duplicate_name collection_id=%s new_name=%s",
                collection_id,
                normalized_name,
            )
            return False

        for col in self.collections:
            if col.id == collection_id:
                old_name = col.name
                col.name = normalized_name
                self.storage.save_collection(col)
                self._rebuild_index()
                logger.info(
                    "rename_collection_succeeded collection_id=%s old_name=%s new_name=%s",
                    collection_id,
                    old_name,
                    normalized_name,
                )
                return True

        logger.warning("rename_collection_not_found collection_id=%s", collection_id)
        return False

    def rename_collection_item(self, item_id: str, item_type: str, new_name: str) -> bool:
        """Renames a collection item by type. Supported types: collection and request."""
        logger.info(
            "rename_collection_item_started item_id=%s item_type=%s",
            item_id,
            item_type,
        )
        strategy = self._item_strategies.get(item_type)
        if strategy is None:
            logger.warning(
                "rename_collection_item_unsupported_type item_id=%s item_type=%s",
                item_id,
                item_type,
            )
            return False
        return strategy.rename(self, item_id, new_name)
