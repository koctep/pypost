import unittest
from unittest.mock import MagicMock, patch

from PySide6.QtWidgets import QApplication, QMessageBox

from pypost.models.models import Collection, RequestData
from pypost.models.settings import AppSettings
from pypost.ui.request_save_orchestrator import (
    RequestSaveOrchestrator,
    SaveAction,
    StaleCheckContext,
)
from tests.test_tabs_presenter import FakeRequestManager, FakeStateManager, _make_request


class TestRequestSaveOrchestrator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._app = QApplication.instance() or QApplication([])

    def _make_orchestrator(self, requests=None):
        rm = FakeRequestManager(requests or [])
        sm = FakeStateManager()
        return RequestSaveOrchestrator(rm, sm, AppSettings(), metrics=MagicMock()), rm

    def test_save_as_assigns_new_request_id(self):
        source = _make_request("r1", "Source")
        col = Collection(id="c1", name="API", requests=[source])
        orchestrator, rm = self._make_orchestrator([source])
        rm.collections = [col]

        mock_dialog = MagicMock()
        mock_dialog.exec.return_value = True
        mock_dialog.selected_collection_id = "c1"
        mock_dialog.new_collection_name = ""
        mock_dialog.request_name = "Copy"

        parent = MagicMock()
        with patch(
            "pypost.ui.request_save_orchestrator.SaveRequestDialog",
            return_value=mock_dialog,
        ):
            result = orchestrator.save_as_request(source, parent)

        self.assertEqual(result.action, SaveAction.SAVE_AS)
        self.assertIsNotNone(result.request)
        self.assertNotEqual(result.request.id, "r1")
        self.assertEqual(len(rm.saved), 1)
        self.assertNotEqual(rm.saved[0][0].id, "r1")

    def test_save_overwrite_cancelled_by_user(self):
        req = _make_request("r1", "Existing")
        col = Collection(id="c1", name="API", requests=[req])
        orchestrator, rm = self._make_orchestrator([req])
        rm.collections = [col]
        rm._requests["r1"] = (req, col)

        settings = AppSettings(confirm_overwrite_request=True)
        orchestrator = RequestSaveOrchestrator(rm, FakeStateManager(), settings)

        parent = MagicMock()
        with patch.object(QMessageBox, "question", return_value=QMessageBox.No):
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
        with patch.object(QMessageBox, "question", return_value=QMessageBox.No):
            result = orchestrator.save_request(req, parent, stale_context=stale)

        self.assertEqual(result.action, SaveAction.CANCELLED)
