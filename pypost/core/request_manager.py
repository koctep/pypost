from typing import List, Optional, Tuple, Dict
from pypost.core.storage import StorageManager
from pypost.models.models import Collection, RequestData

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
        # Note: In a real app we might want to check for name duplicates or generate a UUID here if not handled by model
        import uuid
        new_col = Collection(id=str(uuid.uuid4()), name=name, requests=[])
        self.collections.append(new_col)
        self.storage.save_collection(new_col)
        return new_col

