import sys
import types
import unittest

try:
    import platformdirs  # noqa: F401
except ModuleNotFoundError:
    _stub = types.ModuleType("platformdirs")
    _stub.user_data_dir = lambda app_name, app_author=None: "/tmp"
    sys.modules["platformdirs"] = _stub

from tests.helpers import FakeStorageManager
from pypost.core.request_manager import RequestManager
from pypost.models.models import Collection, RequestData


class TestRequestManagerCreate(unittest.TestCase):
    def setUp(self):
        self.storage = FakeStorageManager()
        self.manager = RequestManager(self.storage)

    def test_create_collection_returns_collection_with_uuid_id(self):
        col = self.manager.create_collection("My API")
        self.assertIsInstance(col.id, str)
        self.assertTrue(len(col.id) > 0)
        self.assertEqual("My API", col.name)

    def test_create_collection_persists_via_storage(self):
        self.manager.create_collection("My API")
        self.assertEqual(["My API"], [c.name for c in self.storage.saved_collections])


class TestRequestManagerSaveRequest(unittest.TestCase):
    def setUp(self):
        self.req_v1 = RequestData(id="r1", name="Get users")
        self.collection = Collection(id="c1", name="Team API", requests=[])
        self.storage = FakeStorageManager([self.collection])
        self.manager = RequestManager(self.storage)

    def test_save_new_request_appended_to_collection(self):
        req = RequestData(id="r_new", name="New req")
        self.manager.save_request(req, "c1")
        self.assertEqual([req], self.collection.requests)
        self.assertIn("Team API", [c.name for c in self.storage.saved_collections])

    def test_save_existing_request_updates_in_place(self):
        self.collection.requests = [self.req_v1]
        self.manager.reload_collections()
        req_v2 = RequestData(id="r1", name="Get active users")
        self.manager.save_request(req_v2, "c1")
        self.assertEqual(1, len(self.collection.requests))
        self.assertEqual(req_v2, self.collection.requests[0])

    def test_save_request_unknown_collection_raises_value_error(self):
        req = RequestData(id="r_new", name="New req")
        with self.assertRaises(ValueError):
            self.manager.save_request(req, "unknown")


class TestRequestManagerFind(unittest.TestCase):
    def setUp(self):
        self.req = RequestData(id="r1", name="Get users")
        col = Collection(id="c1", name="Team API", requests=[self.req])
        storage = FakeStorageManager([col])
        self.manager = RequestManager(storage)
        self.col = col

    def test_find_request_returns_tuple_when_found(self):
        result = self.manager.find_request("r1")
        self.assertIsNotNone(result)
        req, col = result
        self.assertEqual(self.req, req)
        self.assertEqual(self.col, col)

    def test_find_request_returns_none_when_not_found(self):
        result = self.manager.find_request("missing")
        self.assertIsNone(result)


class TestRequestManagerReload(unittest.TestCase):
    def setUp(self):
        self.storage = FakeStorageManager()
        self.manager = RequestManager(self.storage)

    def test_reload_collections_rebuilds_index_from_storage(self):
        req = RequestData(id="r1", name="Get users")
        col = Collection(id="c1", name="Team API", requests=[req])
        self.storage.seed_collections([col])
        self.manager.reload_collections()
        result = self.manager.find_request("r1")
        self.assertIsNotNone(result)
        self.assertEqual(req, result[0])


class TestRequestManagerGetCollections(unittest.TestCase):
    def test_get_collections_returns_current_list(self):
        c1 = Collection(id="c1", name="Col 1", requests=[])
        c2 = Collection(id="c2", name="Col 2", requests=[])
        storage = FakeStorageManager([c1, c2])
        manager = RequestManager(storage)
        cols = manager.get_collections()
        self.assertEqual(2, len(cols))


class TestRequestManagerDeleteIndex(unittest.TestCase):
    def test_delete_request_index_consistent_after_deletion(self):
        r1 = RequestData(id="r1", name="Req 1")
        r2 = RequestData(id="r2", name="Req 2")
        col = Collection(id="c1", name="Team API", requests=[r1, r2])
        storage = FakeStorageManager([col])
        manager = RequestManager(storage)

        manager.delete_request("r1")

        self.assertIsNone(manager.find_request("r1"))
        result = manager.find_request("r2")
        self.assertIsNotNone(result)
        self.assertEqual(r2, result[0])


if __name__ == "__main__":
    unittest.main()
