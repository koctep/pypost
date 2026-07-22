import pytest

pytestmark = pytest.mark.timeout(60)

import unittest
from unittest.mock import MagicMock, patch

from pypost.models.models import Collection, RequestData

def _mock_save_dialog(
    *,
    accepted: bool = True,
    collection_id: str = "c1",
    new_collection_name: str = "",
    request_name: str = "Copy",
):
    mock_dialog = MagicMock()
    mock_dialog.exec.return_value = accepted
    mock_dialog.selected_collection_id = collection_id
    mock_dialog.new_collection_name = new_collection_name
    mock_dialog.request_name = request_name
    return mock_dialog
from pypost.models.settings import AppSettings
from pypost.ui.request_save_orchestrator import (
    RequestSaveOrchestrator,
    SaveAction,
    StaleCheckContext,
)
from tests.test_tabs_presenter import FakeRequestManager, FakeStateManager, _make_request

@pytest.mark.usefixtures("qapp")

class TestRequestSaveOrchestrator(unittest.TestCase):
    def _make_orchestrator(self, requests=None):
        rm = FakeRequestManager(requests or [])
        sm = FakeStateManager()
        return RequestSaveOrchestrator(rm, sm, AppSettings(), metrics=MagicMock()), rm

    def test_save_as_assigns_new_request_id(self):
        source = _make_request("r1", "Source")
        col = Collection(id="c1", name="API", requests=[source])
        orchestrator, rm = self._make_orchestrator([source])
        rm.collections = [col]

        mock_dialog = _mock_save_dialog()
        parent = MagicMock()
        with patch(
            "pypost.ui.request_save_orchestrator.SaveRequestDialog",
            return_value=mock_dialog,
        ):
            result = orchestrator.save_as_request(source, parent)

        self.assertEqual(result.action, SaveAction.SAVE_AS)
        self.assertIsNotNone(result.request)
        self.assertNotEqual(result.request.id, "r1")
        self.assertEqual(result.request.name, "Copy")
        self.assertEqual(result.collection_id, "c1")
        self.assertEqual(len(rm.saved), 1)
        self.assertNotEqual(rm.saved[0][0].id, "r1")

    def test_save_as_cancelled_when_dialog_dismissed(self):
        source = _make_request("r1", "Source")
        orchestrator, rm = self._make_orchestrator([source])
        mock_dialog = _mock_save_dialog(accepted=False)

        parent = MagicMock()
        with patch(
            "pypost.ui.request_save_orchestrator.SaveRequestDialog",
            return_value=mock_dialog,
        ):
            result = orchestrator.save_as_request(source, parent)

        self.assertEqual(result.action, SaveAction.CANCELLED)
        self.assertIsNone(result.request)
        self.assertEqual(len(rm.saved), 0)

    def test_save_as_cancelled_when_missing_target_collection(self):
        source = _make_request("r1", "Source")
        orchestrator, rm = self._make_orchestrator([source])
        mock_dialog = _mock_save_dialog(collection_id="", new_collection_name="")

        parent = MagicMock()
        with patch(
            "pypost.ui.request_save_orchestrator.SaveRequestDialog",
            return_value=mock_dialog,
        ):
            result = orchestrator.save_as_request(source, parent)

        self.assertEqual(result.action, SaveAction.CANCELLED)
        self.assertEqual(len(rm.saved), 0)

    def test_save_as_creates_new_collection_via_dialog(self):
        source = _make_request("r1", "Source")
        orchestrator, rm = self._make_orchestrator([source])
        mock_dialog = _mock_save_dialog(
            collection_id="",
            new_collection_name="Archive",
            request_name="Archived Copy",
        )

        parent = MagicMock()
        with patch(
            "pypost.ui.request_save_orchestrator.SaveRequestDialog",
            return_value=mock_dialog,
        ):
            result = orchestrator.save_as_request(source, parent)

        self.assertEqual(result.action, SaveAction.SAVE_AS)
        self.assertEqual(len(rm.collections), 1)
        self.assertEqual(rm.collections[0].name, "Archive")
        self.assertEqual(result.collection_id, rm.collections[0].id)
        self.assertEqual(len(rm.saved), 1)
        self.assertEqual(rm.saved[0][1], rm.collections[0].id)

    def test_save_as_expands_target_collection(self):
        source = _make_request("r1", "Source")
        col = Collection(id="c1", name="API", requests=[source])
        rm = FakeRequestManager([source])
        rm.collections = [col]
        sm = FakeStateManager()
        orchestrator = RequestSaveOrchestrator(rm, sm, AppSettings())
        mock_dialog = _mock_save_dialog()
        parent = MagicMock()

        with patch(
            "pypost.ui.request_save_orchestrator.SaveRequestDialog",
            return_value=mock_dialog,
        ):
            orchestrator.save_as_request(source, parent)

        self.assertEqual(sm.get_expanded_collections(), ["c1"])

    def test_save_as_preserves_source_request_in_manager(self):
        source = _make_request("r1", "Original")
        source.url = "https://original.example.com"
        col = Collection(id="c1", name="API", requests=[source])
        orchestrator, rm = self._make_orchestrator([source])
        rm.collections = [col]
        rm._requests["r1"] = (source, col)

        save_input = source.model_copy(deep=True)
        save_input.url = "https://copy.example.com"
        mock_dialog = _mock_save_dialog(request_name="Copy")
        parent = MagicMock()

        with patch(
            "pypost.ui.request_save_orchestrator.SaveRequestDialog",
            return_value=mock_dialog,
        ):
            result = orchestrator.save_as_request(save_input, parent)

        self.assertEqual(result.action, SaveAction.SAVE_AS)
        self.assertEqual(save_input.id, "r1")
        self.assertEqual(save_input.url, "https://copy.example.com")

        original_lookup = rm.find_request("r1")
        self.assertIsNotNone(original_lookup)
        stored_original, _ = original_lookup
        self.assertEqual(stored_original.url, "https://original.example.com")

        self.assertEqual(len(rm.saved), 1)
        saved_request, saved_collection_id = rm.saved[0]
        self.assertNotEqual(saved_request.id, "r1")
        self.assertEqual(saved_request.url, "https://copy.example.com")
        self.assertEqual(saved_collection_id, "c1")

    def test_save_overwrite_cancelled_by_user(self):
        req = _make_request("r1", "Existing")
        col = Collection(id="c1", name="API", requests=[req])
        orchestrator, rm = self._make_orchestrator([req])
        rm.collections = [col]
        rm._requests["r1"] = (req, col)

        settings = AppSettings(confirm_overwrite_request=True)
        orchestrator = RequestSaveOrchestrator(rm, FakeStateManager(), settings)

        parent = MagicMock()
        with patch(
            "pypost.ui.request_save_orchestrator.confirm_overwrite_request",
            return_value=False,
        ):
            result = orchestrator.save_request(req, parent)

        self.assertEqual(result.action, SaveAction.CANCELLED)
        self.assertEqual(len(rm.saved), 0)

    def test_save_new_persists_via_dialog(self):
        req = _make_request("new-id", "Draft")
        orchestrator, rm = self._make_orchestrator()

        mock_dialog = MagicMock()
        mock_dialog.exec.return_value = True
        mock_dialog.selected_collection_id = "c1"
        mock_dialog.new_collection_name = ""
        mock_dialog.request_name = "Saved Draft"

        parent = MagicMock()
        with patch(
            "pypost.ui.request_save_orchestrator.SaveRequestDialog",
            return_value=mock_dialog,
        ):
            result = orchestrator.save_request(req, parent)

        self.assertEqual(result.action, SaveAction.CREATED_NEW)
        self.assertEqual(len(rm.saved), 1)
        self.assertEqual(rm.saved[0][0].name, "Saved Draft")

    def test_stale_context_blocks_overwrite_when_user_declines(self):
        req = _make_request("r1", "Existing")
        disk = _make_request("r1", "On Disk")
        col = Collection(id="c1", name="API", requests=[disk])
        orchestrator, rm = self._make_orchestrator([disk])
        rm.collections = [col]
        rm._requests["r1"] = (disk, col)

        settings = AppSettings(confirm_overwrite_request=False)
        orchestrator = RequestSaveOrchestrator(rm, FakeStateManager(), settings)

        stale = StaleCheckContext(
            persisted_baseline=_make_request("r1", "Baseline"),
            stale_persisted=True,
        )
        parent = MagicMock()
        with patch(
            "pypost.ui.request_save_orchestrator.confirm_overwrite_newer_saved_version",
            return_value=False,
        ):
            result = orchestrator.save_request(req, parent, stale_context=stale)

        self.assertEqual(result.action, SaveAction.CANCELLED)
