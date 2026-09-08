"""Tests for RequestStore: where a saved request goes, and what that records."""
import unittest
from unittest.mock import MagicMock

from tests.helpers import FakeStorageManager
from pypost.core.request_manager import RequestManager
from pypost.models.models import Collection, RequestData
from pypost.ui.presenters.request_store import RequestStore


class FakeStateManager:
    def __init__(self):
        self._expanded = []

    def get_expanded_collections(self):
        return list(self._expanded)

    def set_expanded_collections(self, ids):
        self._expanded = list(ids)


class RequestStoreTests(unittest.TestCase):
    def setUp(self):
        self.existing = RequestData(id="r1", name="Get users", url="http://real")
        self.collection = Collection(
            id="c1", name="Team API", requests=[self.existing],
        )
        self.storage = FakeStorageManager([self.collection])
        self.manager = RequestManager(self.storage)
        self.state = FakeStateManager()
        self.metrics = MagicMock()
        self.store = RequestStore(self.manager, self.state, self.metrics)

    def test_find_existing_reports_the_holding_collection(self):
        found, collection = self.store.find_existing("r1")

        self.assertEqual("r1", found.id)
        self.assertEqual("c1", collection.id)

    def test_find_existing_returns_none_for_an_unsaved_request(self):
        self.assertIsNone(self.store.find_existing("nope"))

    def test_resolve_target_prefers_the_chosen_collection(self):
        self.assertEqual("c1", self.store.resolve_target("c1", "Ignored"))

    def test_resolve_target_creates_a_collection_from_a_name(self):
        target = self.store.resolve_target(None, "Fresh API")

        self.assertIsNotNone(target)
        names = [c.name for c in self.store.collections()]
        self.assertIn("Fresh API", names)

    def test_resolve_target_reports_no_target(self):
        self.assertIsNone(self.store.resolve_target(None, None))
        self.assertIsNone(self.store.resolve_target("", ""))

    def test_store_persists_expands_and_records_a_new_save(self):
        request = RequestData(id="r2", name="Create user", url="http://new")

        self.store.store(request, "c1")

        self.assertEqual("http://new", self.manager.find_request("r2")[0].url)
        self.assertEqual(["c1"], self.state.get_expanded_collections())
        self.metrics.track_gui_save_action.assert_called_once_with("new")

    def test_overwrite_persists_and_records_an_overwrite(self):
        edited = RequestData(id="r1", name="Get users", url="http://edited")

        self.store.overwrite(edited, "c1")

        self.assertEqual("http://edited", self.manager.find_request("r1")[0].url)
        self.metrics.track_gui_save_action.assert_called_once_with("overwrite")

    def test_overwrite_leaves_the_expanded_set_alone(self):
        """The collection is already on screen; a save should not move the tree."""
        self.store.overwrite(self.existing, "c1")

        self.assertEqual([], self.state.get_expanded_collections())

    def test_store_copy_is_independent_of_the_source(self):
        copy = self.store.store_copy(self.existing, "c1", "Get users (copy)")

        self.assertNotEqual(self.existing.id, copy.id)
        self.assertEqual("Get users (copy)", copy.name)
        self.assertEqual(self.existing.url, copy.url)
        self.assertIsNotNone(self.manager.find_request(copy.id))
        self.assertEqual("Get users", self.manager.find_request("r1")[0].name)

    def test_store_copy_expands_the_receiving_collection(self):
        self.store.store_copy(self.existing, "c1", "Copy")

        self.assertEqual(["c1"], self.state.get_expanded_collections())

    def test_expanding_twice_does_not_duplicate_the_entry(self):
        self.store.store(RequestData(id="r2", name="A"), "c1")
        self.store.store(RequestData(id="r3", name="B"), "c1")

        self.assertEqual(["c1"], self.state.get_expanded_collections())


if __name__ == "__main__":
    unittest.main()
