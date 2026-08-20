"""Integration tests for RequestWidget → TabsPresenter save flows (PYPOST-320)."""

import pytest

import unittest
from unittest.mock import MagicMock, patch

from pypost.models.models import Collection
from pypost.models.settings import AppSettings
from pypost.ui.presenters.tabs_presenter import RequestTab, TabsPresenter

from tests.test_request_save_orchestrator import _mock_save_dialog
from tests.test_tabs_presenter import FakeRequestManager, FakeStateManager, _make_request

pytestmark = pytest.mark.timeout(120)


@pytest.mark.usefixtures("qapp")

class TestSaveFlowIntegration(unittest.TestCase):
    """GUI entry points on RequestWidget wired through TabsPresenter."""

    def _make_presenter(self, requests=None):
        rm = FakeRequestManager(requests)
        sm = FakeStateManager()
        return TabsPresenter(rm, sm, AppSettings(), metrics=MagicMock()), rm

    def _active_tab(self, presenter: TabsPresenter) -> RequestTab:
        tab = presenter.widget.currentWidget()
        self.assertIsInstance(tab, RequestTab)
        return tab

    def test_save_menu_action_overwrites_existing_request(self):
        req = _make_request("r1", "Existing")
        col = Collection(id="c1", name="API", requests=[req])
        presenter, rm = self._make_presenter([req])
        rm.collections = [col]
        rm._requests["r1"] = (req, col)
        presenter.add_new_tab(req, save_state=False)

        tab = self._active_tab(presenter)
        tab.request_editor.url_input.setText("https://updated.example.com")

        saved_signals = []
        presenter.request_saved.connect(lambda: saved_signals.append(True))

        tab.request_editor.handle_save_menu_action()

        self.assertEqual(len(rm.saved), 1)
        self.assertEqual(rm.saved[0][0].id, "r1")
        self.assertEqual(rm.saved[0][0].url, "https://updated.example.com")
        self.assertEqual(saved_signals, [True])
        self.assertEqual(tab.request_data.url, "https://updated.example.com")

    def test_save_menu_action_cancelled_when_dialog_dismissed(self):
        presenter, rm = self._make_presenter()
        presenter.add_new_tab(save_state=False)

        tab = self._active_tab(presenter)
        tab.request_editor.url_input.setText("https://draft.example.com")
        original_id = tab.request_editor.request_data.id

        saved_signals = []
        presenter.request_saved.connect(lambda: saved_signals.append(True))
        mock_dialog = _mock_save_dialog(accepted=False)

        with patch(
            "pypost.ui.request_save_orchestrator.SaveRequestDialog",
            return_value=mock_dialog,
        ):
            tab.request_editor.handle_save_menu_action()

        self.assertEqual(len(rm.saved), 0)
        self.assertEqual(saved_signals, [])
        self.assertEqual(tab.request_editor.request_data.id, original_id)

    def test_save_shortcut_cancelled_on_overwrite_decline(self):
        req = _make_request("r1", "Existing")
        col = Collection(id="c1", name="API", requests=[req])
        rm = FakeRequestManager([req])
        rm.collections = [col]
        rm._requests["r1"] = (req, col)
        settings = AppSettings(confirm_overwrite_request=True)
        presenter = TabsPresenter(rm, FakeStateManager(), settings, metrics=MagicMock())
        presenter.add_new_tab(req, save_state=False)

        tab = self._active_tab(presenter)
        tab.request_editor.url_input.setText("https://blocked.example.com")

        with patch(
            "pypost.ui.request_save_orchestrator.confirm_overwrite_request",
            return_value=False,
        ):
            tab.request_editor.handle_save_request_shortcut()

        self.assertEqual(len(rm.saved), 0)
        self.assertEqual(
            tab.request_editor.url_input.text(),
            "https://blocked.example.com",
        )

    def test_save_as_shortcut_persists_copy_with_new_id(self):
        source = _make_request("r1", "Source")
        col = Collection(id="c1", name="API", requests=[source])
        presenter, rm = self._make_presenter([source])
        rm.collections = [col]
        rm._requests["r1"] = (source, col)
        presenter.add_new_tab(source, save_state=False)

        tab = self._active_tab(presenter)
        tab.request_editor.url_input.setText("https://copy.example.com")

        save_as_events = []
        presenter.request_save_as_completed.connect(
            lambda request, collection_id: save_as_events.append(
                (request.id, collection_id),
            ),
        )
        mock_dialog = _mock_save_dialog(request_name="Copy")

        with patch(
            "pypost.ui.request_save_orchestrator.SaveRequestDialog",
            return_value=mock_dialog,
        ):
            tab.request_editor.handle_save_as_shortcut()

        self.assertEqual(len(rm.saved), 1)
        saved_request, saved_collection_id = rm.saved[0]
        self.assertNotEqual(saved_request.id, "r1")
        self.assertEqual(saved_request.url, "https://copy.example.com")
        self.assertEqual(saved_collection_id, "c1")
        self.assertEqual(len(save_as_events), 1)
        self.assertEqual(save_as_events[0][0], saved_request.id)
        self.assertEqual(tab.request_data.id, saved_request.id)
        self.assertEqual(tab.request_editor.request_data.id, saved_request.id)

        original_lookup = rm.find_request("r1")
        self.assertIsNotNone(original_lookup)
        stored_original, _ = original_lookup
        self.assertEqual(stored_original.url, source.url)

    def test_save_as_menu_action_cancelled_when_dialog_dismissed(self):
        source = _make_request("r1", "Source")
        col = Collection(id="c1", name="API", requests=[source])
        presenter, rm = self._make_presenter([source])
        rm.collections = [col]
        rm._requests["r1"] = (source, col)
        presenter.add_new_tab(source, save_state=False)

        tab = self._active_tab(presenter)
        tab.request_editor.url_input.setText("https://copy.example.com")
        original_id = tab.request_data.id

        save_as_events = []
        presenter.request_save_as_completed.connect(
            lambda request, collection_id: save_as_events.append(
                (request.id, collection_id),
            ),
        )
        mock_dialog = _mock_save_dialog(accepted=False)

        with patch(
            "pypost.ui.request_save_orchestrator.SaveRequestDialog",
            return_value=mock_dialog,
        ):
            tab.request_editor.handle_save_as_menu_action()

        self.assertEqual(len(rm.saved), 0)
        self.assertEqual(save_as_events, [])
        self.assertEqual(tab.request_data.id, original_id)
        self.assertEqual(tab.request_editor.request_data.id, original_id)

if __name__ == "__main__":
    unittest.main()
