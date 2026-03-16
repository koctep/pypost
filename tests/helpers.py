class FakeStorageManager:
    def __init__(self, collections=None):
        self._collections = collections or []
        self.saved_collections: list = []
        self.deleted_collection_names: list = []

    def load_collections(self):
        return list(self._collections)

    def save_collection(self, collection):
        self.saved_collections.append(collection.name)

    def delete_collection(self, collection_name: str):
        self.deleted_collection_names.append(collection_name)
