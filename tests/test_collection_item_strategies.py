import pytest

import unittest

from pypost.core.collection_item_strategies import (
    DEFAULT_COLLECTION_ITEM_STRATEGIES,
    CollectionItemStrategy,
)
from pypost.core.request_manager import RequestManager
from pypost.models.models import Collection, RequestData
from tests.helpers import FakeStorageManager

pytestmark = pytest.mark.timeout(60)


class CollectionItemStrategiesTests(unittest.TestCase):
    def test_default_registry_covers_collection_and_request(self):
        self.assertIn("collection", DEFAULT_COLLECTION_ITEM_STRATEGIES)
        self.assertIn("request", DEFAULT_COLLECTION_ITEM_STRATEGIES)

    def test_custom_strategy_is_used_for_delete_and_rename(self):
        calls: list[tuple[str, str, str | None]] = []

        def custom_delete(manager, item_id):
            calls.append(("delete", item_id, None))
            return True

        def custom_rename(manager, item_id, new_name):
            calls.append(("rename", item_id, new_name))
            return True

        strategies = {
            "custom": CollectionItemStrategy(
                delete=custom_delete,
                rename=custom_rename,
            ),
        }
        storage = FakeStorageManager([])
        manager = RequestManager(storage, item_strategies=strategies)

        self.assertTrue(manager.delete_collection_item("id-1", "custom"))
        self.assertTrue(manager.rename_collection_item("id-2", "custom", "New"))

        self.assertEqual(
            [("delete", "id-1", None), ("rename", "id-2", "New")],
            calls,
        )

    def test_builtin_strategies_delegate_to_request_manager_methods(self):
        req = RequestData(id="r1", name="Get users")
        collection = Collection(id="c1", name="Team API", requests=[req])
        storage = FakeStorageManager([collection])
        manager = RequestManager(storage)

        self.assertTrue(manager.delete_collection_item("r1", "request"))
        self.assertEqual([], collection.requests)

        renamed = manager.rename_collection_item("c1", "collection", "Team API v2")
        self.assertTrue(renamed)
        self.assertEqual("Team API v2", manager.get_collections()[0].name)


if __name__ == "__main__":
    unittest.main()
