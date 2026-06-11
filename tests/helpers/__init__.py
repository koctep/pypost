"""Shared test helpers for PyPost unit tests."""


class FakeStorageManager:
    def __init__(self, collections=None):
        self._collections = collections or []
        self.saved_collections: list = []  # Collection instances (see save_collection)
        self.deleted_collection_ids: list = []

    def seed_collections(self, collections):
        """Simulate persisted data changing between load_collections() calls (tests only)."""
        self._collections = list(collections) if collections else []

    def load_collections(self):
        return list(self._collections)

    def save_collection(self, collection):
        self.saved_collections.append(collection)

    def delete_collection(self, collection_id: str, *, collection_name: str | None = None):
        self.deleted_collection_ids.append(collection_id)
