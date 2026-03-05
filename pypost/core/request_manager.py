import logging
from typing import List, Optional, Tuple, Dict
from pypost.core.storage import StorageManager
from pypost.models.models import Collection, RequestData

logger = logging.getLogger(__name__)


class RequestManager:
    """
    Manages the lifecycle of requests and collections, abstracting storage operations.
    """
    def __init__(self, storage_manager: StorageManager):
        self.storage = storage_manager
        self.collections: List[Collection] = []
        self._request_index: Dict[str, Tuple[RequestData, Collection]] = {}
        self.reload_collections()

    def reload_collections(self):
        """Reloads collections from storage."""
        self.collections = self.storage.load_collections()
        self._rebuild_index()

    def _rebuild_index(self):
        """Rebuilds the internal index of requests for O(1) access."""
        self._request_index.clear()
        for col in self.collections:
            for req in col.requests:
                self._request_index[req.id] = (req, col)

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

    def create_collection(self, name: str) -> Collection:
        """Creates a new collection."""
        # Note: in a real app we may check duplicate names before persisting.
        import uuid
        new_col = Collection(id=str(uuid.uuid4()), name=name, requests=[])
        self.collections.append(new_col)
        self.storage.save_collection(new_col)
        return new_col

    def delete_request(self, request_id: str) -> bool:
        """Deletes a request by ID from its collection."""
        logger.info("delete_request_started request_id=%s", request_id)
        for col in self.collections:
            for idx, req in enumerate(col.requests):
                if req.id == request_id:
                    del col.requests[idx]
                    self.storage.save_collection(col)
                    self._rebuild_index()
                    logger.info(
                        "delete_request_succeeded request_id=%s collection_id=%s",
                        request_id,
                        col.id,
                    )
                    return True
        logger.warning("delete_request_not_found request_id=%s", request_id)
        return False

    def delete_collection(self, collection_id: str) -> bool:
        """Deletes a collection by ID."""
        logger.info("delete_collection_started collection_id=%s", collection_id)
        for idx, col in enumerate(self.collections):
            if col.id == collection_id:
                self.storage.delete_collection(col.name)
                del self.collections[idx]
                self._rebuild_index()
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
        if item_type == "collection":
            return self.delete_collection(item_id)
        if item_type == "request":
            return self.delete_request(item_id)
        logger.warning(
            "delete_collection_item_unsupported_type item_id=%s item_type=%s",
            item_id,
            item_type,
        )
        return False

    def rename_request(self, request_id: str, new_name: str) -> bool:
        """Renames a request by ID and persists the parent collection."""
        normalized_name = new_name.strip()
        if not normalized_name:
            logger.warning("rename_request_rejected_empty_name request_id=%s", request_id)
            return False

        for col in self.collections:
            for req in col.requests:
                if req.id == request_id:
                    req.name = normalized_name
                    self.storage.save_collection(col)
                    self._rebuild_index()
                    logger.info(
                        "rename_request_succeeded request_id=%s collection_id=%s",
                        request_id,
                        col.id,
                    )
                    return True

        logger.warning("rename_request_not_found request_id=%s", request_id)
        return False

    def rename_collection(self, collection_id: str, new_name: str) -> bool:
        """Renames a collection by ID and updates stored collection file name."""
        normalized_name = new_name.strip()
        if not normalized_name:
            logger.warning("rename_collection_rejected_empty_name collection_id=%s", collection_id)
            return False

        for col in self.collections:
            if col.id == collection_id:
                old_name = col.name
                col.name = normalized_name
                self.storage.delete_collection(old_name)
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
        if item_type == "collection":
            return self.rename_collection(item_id, new_name)
        if item_type == "request":
            return self.rename_request(item_id, new_name)
        logger.warning(
            "rename_collection_item_unsupported_type item_id=%s item_type=%s",
            item_id,
            item_type,
        )
        return False
