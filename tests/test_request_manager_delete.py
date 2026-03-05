import unittest
import sys
import types

try:
    import platformdirs  # noqa: F401
except ModuleNotFoundError:
    platformdirs_stub = types.ModuleType("platformdirs")
    platformdirs_stub.user_data_dir = lambda app_name, app_author=None: "/tmp"
    sys.modules["platformdirs"] = platformdirs_stub

from pypost.core.request_manager import RequestManager
from pypost.models.models import Collection, RequestData


class FakeStorageManager:
    def __init__(self, collections):
        self._collections = collections
        self.saved_collections = []
        self.deleted_collection_names = []

    def load_collections(self):
        return self._collections

    def save_collection(self, collection):
        self.saved_collections.append(collection.name)

    def delete_collection(self, collection_name: str):
        self.deleted_collection_names.append(collection_name)


class RequestManagerDeleteTests(unittest.TestCase):
    def test_delete_request_removes_request_and_persists_collection(self):
        req = RequestData(id="r1", name="Get users")
        collection = Collection(id="c1", name="Team API", requests=[req])
        storage = FakeStorageManager([collection])
        manager = RequestManager(storage)

        deleted = manager.delete_request("r1")

        self.assertTrue(deleted)
        self.assertEqual([], collection.requests)
        self.assertEqual(["Team API"], storage.saved_collections)
        self.assertIsNone(manager.find_request("r1"))

    def test_delete_collection_removes_collection_and_deletes_file(self):
        req = RequestData(id="r1", name="Get users")
        collection = Collection(id="c1", name="Team API", requests=[req])
        storage = FakeStorageManager([collection])
        manager = RequestManager(storage)

        deleted = manager.delete_collection("c1")

        self.assertTrue(deleted)
        self.assertEqual([], manager.get_collections())
        self.assertEqual(["Team API"], storage.deleted_collection_names)
        self.assertIsNone(manager.find_request("r1"))

    def test_delete_collection_item_routes_by_type(self):
        req = RequestData(id="r1", name="Get users")
        collection = Collection(id="c1", name="Team API", requests=[req])
        storage = FakeStorageManager([collection])
        manager = RequestManager(storage)

        self.assertTrue(manager.delete_collection_item("r1", "request"))
        self.assertFalse(manager.delete_collection_item("missing", "request"))
        self.assertFalse(manager.delete_collection_item("c1", "unsupported"))


if __name__ == "__main__":
    unittest.main()
