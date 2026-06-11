"""Integration tests for open-tab closure after collection item delete (PYPOST-332)."""

import pytest

pytestmark = pytest.mark.timeout(120)

import unittest
from unittest.mock import MagicMock

from PySide6.QtWidgets import QApplication

from pypost.models.models import Collection, RequestData
from pypost.models.settings import AppSettings
from pypost.ui.presenters.collections_presenter import CollectionsPresenter
from pypost.ui.presenters.tabs_presenter import RequestTab, TabsPresenter


def _request_tab_count(tabs_presenter: TabsPresenter) -> int:
    widget = tabs_presenter.widget
    return sum(
        1 for i in range(widget.count()) if isinstance(widget.widget(i), RequestTab)
    )


def _make_collection(col_id: str, name: str, requests=None) -> Collection:
    return Collection(id=col_id, name=name, requests=requests or [])


def _make_request(req_id: str, name: str, method: str = "GET") -> RequestData:
    return RequestData(id=req_id, name=name, method=method)


class CollectionsFakeRequestManager:
    def __init__(self, collections=None):
        self.collections = collections or []
        self.storage = MagicMock()
        self.storage.load_collections.return_value = self.collections

    def reload_collections(self):
        self.collections = self.storage.load_collections()

    def get_collections(self):
        return self.collections

    def delete_collection_item(self, item_id, item_type):
        if item_type == "request":
            for col in self.collections:
                col.requests = [req for req in col.requests if req.id != item_id]
        elif item_type == "collection":
            self.collections = [col for col in self.collections if col.id != item_id]
        return True


class TabsFakeRequestManager:
    def __init__(self, requests=None):
        self._requests = {r.id: (r, MagicMock(id="c1")) for r in (requests or [])}
        self.collections = []

    def find_request(self, req_id):
        return self._requests.get(req_id)

    def get_collections(self):
        return self.collections

    def save_request(self, req, col_id):
        pass

    def create_collection(self, name):
        col = Collection(name=name)
        self.collections.append(col)
        return col


class FakeStateManager:
    def __init__(self, open_tabs=None):
        self._open_tabs = open_tabs or []
        self._expanded = []
        self.settings = AppSettings()

    def get_open_tabs(self):
        return list(self._open_tabs)

    def set_open_tabs(self, ids):
        self._open_tabs = ids

    def get_expanded_collections(self):
        return list(self._expanded)

    def set_expanded_collections(self, ids):
        self._expanded = ids


class FakeMetrics:
    def track_gui_collection_delete_action(self, *args):
        pass

    def track_gui_collection_rename_action(self, *args):
        pass


class TestDeleteOpenTabsIntegration(unittest.TestCase):
    """End-to-end wiring: CollectionsPresenter.requests_deleted → TabsPresenter."""

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def _make_connected_presenters(self, collections, tab_requests=None):
        col_rm = CollectionsFakeRequestManager(collections)
        col_sm = FakeStateManager()
        col_metrics = FakeMetrics()
        collections_presenter = CollectionsPresenter(col_rm, col_sm, col_metrics, icons={})
        collections_presenter.load_collections()

        tab_requests = tab_requests or []
        tabs_rm = TabsFakeRequestManager(tab_requests)
        tabs_sm = FakeStateManager()
        tabs_presenter = TabsPresenter(tabs_rm, tabs_sm, AppSettings(), metrics=MagicMock())
        collections_presenter.requests_deleted.connect(
            tabs_presenter.close_tabs_for_request_ids,
        )
        return collections_presenter, tabs_presenter

    def test_request_delete_closes_matching_open_tab(self):
        req = _make_request("r1", "Get users")
        col = _make_collection("c1", "My API", [req])
        collections_presenter, tabs_presenter = self._make_connected_presenters(
            [col],
            tab_requests=[req],
        )
        tabs_presenter.add_new_tab(req, save_state=False)
        tabs_presenter.add_new_tab(_make_request("r2", "Other"), save_state=False)

        collections_presenter._tree_actions.handle_delete("r1", "request", "Get users")

        self.assertEqual(_request_tab_count(tabs_presenter), 1)
        self.assertEqual(tabs_presenter.widget.widget(0).request_data.id, "r2")

    def test_collection_delete_closes_all_affected_open_tabs(self):
        req1 = _make_request("r1", "A")
        req2 = _make_request("r2", "B")
        col = _make_collection("c1", "My API", [req1, req2])
        collections_presenter, tabs_presenter = self._make_connected_presenters(
            [col],
            tab_requests=[req1, req2],
        )
        tabs_presenter.add_new_tab(req1, save_state=False)
        tabs_presenter.add_new_tab(req2, save_state=False)

        collections_presenter._tree_actions.handle_delete("c1", "collection", "My API")

        self.assertEqual(_request_tab_count(tabs_presenter), 1)
        self.assertEqual(tabs_presenter.widget.tabText(0), "New Request")

    def test_request_delete_leaves_unrelated_tabs_open(self):
        req1 = _make_request("r1", "Keep")
        req2 = _make_request("r2", "Delete me")
        col = _make_collection("c1", "My API", [req1, req2])
        collections_presenter, tabs_presenter = self._make_connected_presenters(
            [col],
            tab_requests=[req1, req2],
        )
        tabs_presenter.add_new_tab(req1, save_state=False)
        tabs_presenter.add_new_tab(req2, save_state=False)

        collections_presenter._tree_actions.handle_delete("r2", "request", "Delete me")

        self.assertEqual(_request_tab_count(tabs_presenter), 1)
        self.assertEqual(tabs_presenter.widget.widget(0).request_data.id, "r1")

    def test_delete_updates_persisted_open_tab_state(self):
        req = _make_request("r1", "Persisted")
        col = _make_collection("c1", "My API", [req])
        collections_presenter, tabs_presenter = self._make_connected_presenters(
            [col],
            tab_requests=[req],
        )
        tabs_presenter.add_new_tab(req, save_state=True)
        self.assertEqual(tabs_presenter._state_manager.get_open_tabs(), ["r1"])

        collections_presenter._tree_actions.handle_delete("r1", "request", "Persisted")

        self.assertEqual(tabs_presenter._state_manager.get_open_tabs(), [])


if __name__ == "__main__":
    unittest.main()
