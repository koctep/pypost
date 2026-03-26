import unittest
import sys
import types

try:
    import platformdirs  # noqa: F401
except ModuleNotFoundError:
    platformdirs_stub = types.ModuleType("platformdirs")
    platformdirs_stub.user_data_dir = lambda app_name, app_author=None: "/tmp"
    sys.modules["platformdirs"] = platformdirs_stub

from tests.helpers import FakeStorageManager
from pypost.core.request_manager import RequestManager
from pypost.models.models import Collection, RequestData


class RequestManagerDeleteTests(unittest.TestCase):
    def test_delete_request_removes_request_and_persists_collection(self):
        req = RequestData(id="r1", name="Get users")
        collection = Collection(id="c1", name="Team API", requests=[req])
        storage = FakeStorageManager([collection])
        manager = RequestManager(storage)

        deleted = manager.delete_request("r1")

        self.assertTrue(deleted)
        self.assertEqual([], collection.requests)
        self.assertEqual(["Team API"], [c.name for c in storage.saved_collections])
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

    def test_rename_request_updates_name_and_persists_collection(self):
        req = RequestData(id="r1", name="Get users")
        collection = Collection(id="c1", name="Team API", requests=[req])
        storage = FakeStorageManager([collection])
        manager = RequestManager(storage)

        renamed = manager.rename_request("r1", "Get active users")

        self.assertTrue(renamed)
        self.assertEqual("Get active users", collection.requests[0].name)
        self.assertEqual(["Team API"], [c.name for c in storage.saved_collections])

    def test_rename_collection_updates_name_and_rewrites_collection_file(self):
        collection = Collection(id="c1", name="Team API", requests=[])
        storage = FakeStorageManager([collection])
        manager = RequestManager(storage)

        renamed = manager.rename_collection("c1", "Team API v2")

        self.assertTrue(renamed)
        self.assertEqual("Team API v2", manager.get_collections()[0].name)
        self.assertEqual(["Team API"], storage.deleted_collection_names)
        self.assertEqual(["Team API v2"], [c.name for c in storage.saved_collections])

    def test_rename_collection_item_rejects_empty_name(self):
        req = RequestData(id="r1", name="Get users")
        collection = Collection(id="c1", name="Team API", requests=[req])
        storage = FakeStorageManager([collection])
        manager = RequestManager(storage)

        renamed = manager.rename_collection_item("r1", "request", "   ")

        self.assertFalse(renamed)
        self.assertEqual("Get users", collection.requests[0].name)


if __name__ == "__main__":
    unittest.main()
