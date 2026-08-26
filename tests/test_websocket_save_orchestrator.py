"""Red tests for WebSocketSaveOrchestrator (PYPOST-1161 / WS-TM-5).

Asserts desired save / save-as / overwrite / stale behavior before Step 4
implements ``pypost.ui.websocket_save_orchestrator.WebSocketSaveOrchestrator``.
"""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

import pytest

from pypost.core.websocket_registry import WebSocketRegistry
from pypost.models.models import Collection
from pypost.models.settings import AppSettings
from pypost.models.websocket import WebSocketConnection
from pypost.ui.request_save_orchestrator import SaveAction, StaleCheckContext
from tests.test_request_save_orchestrator import _mock_save_dialog
from tests.test_tabs_presenter import FakeRequestManager, FakeStateManager

pytestmark = pytest.mark.timeout(60)


def _make_ws(
    ws_id: str = "ws1",
    name: str = "Feed",
    url: str = "wss://example.com/stream",
) -> WebSocketConnection:
    return WebSocketConnection(id=ws_id, name=name, url=url)


def _result_profile(result):
    """Saved profile from reused SaveResult (``.connection`` or ``.request``)."""
    conn = getattr(result, "connection", None)
    if conn is not None:
        return conn
    return result.request


def _load_websocket_save_orchestrator():
    """Load WebSocketSaveOrchestrator; AssertionError = feature not implemented yet."""
    import importlib.util

    spec = importlib.util.find_spec("pypost.ui.websocket_save_orchestrator")
    assert spec is not None, (
        "missing module pypost.ui.websocket_save_orchestrator "
        "(WebSocketSaveOrchestrator not implemented — PYPOST-1161)"
    )
    module = importlib.import_module("pypost.ui.websocket_save_orchestrator")
    assert hasattr(module, "WebSocketSaveOrchestrator"), (
        "WebSocketSaveOrchestrator class missing from websocket_save_orchestrator"
    )
    return module.WebSocketSaveOrchestrator


@pytest.mark.usefixtures("qapp")
class TestWebSocketSaveOrchestrator(unittest.TestCase):
    def _make_orchestrator(self, collections=None, settings=None):
        WebSocketSaveOrchestrator = _load_websocket_save_orchestrator()

        rm = FakeRequestManager()
        rm.collections = list(collections or [])
        registry = WebSocketRegistry(rm, storage=MagicMock())
        sm = FakeStateManager()
        orch = WebSocketSaveOrchestrator(
            registry,
            sm,
            settings or AppSettings(),
            metrics=MagicMock(),
        )
        return orch, registry, rm, sm

    def test_save_draft_to_collection(self):
        col = Collection(id="c1", name="API", websockets=[])
        orch, registry, _rm, _sm = self._make_orchestrator([col])
        draft = _make_ws("ws-draft", "Draft", "ws://draft.example.com")

        mock_dialog = _mock_save_dialog(
            collection_id="c1",
            request_name="Saved Draft",
        )
        parent = MagicMock()
        with patch(
            "pypost.ui.websocket_save_orchestrator.SaveRequestDialog",
            return_value=mock_dialog,
        ):
            result = orch.save_profile(draft, parent)

        self.assertEqual(result.action, SaveAction.CREATED_NEW)
        self.assertEqual(result.collection_id, "c1")
        profile = _result_profile(result)
        self.assertIsNotNone(profile)
        self.assertEqual(profile.name, "Saved Draft")
        self.assertEqual(profile.id, "ws-draft")

        found = registry.find_websocket("ws-draft")
        self.assertIsNotNone(found)
        saved_conn, saved_col = found
        self.assertEqual(saved_conn.name, "Saved Draft")
        self.assertEqual(saved_col.id, "c1")

    def test_save_overwrite_existing_profile(self):
        existing = _make_ws("ws1", "Existing", "ws://old.example.com")
        col = Collection(id="c1", name="API", websockets=[existing])
        settings = AppSettings(confirm_overwrite_request=True)
        orch, registry, _rm, _sm = self._make_orchestrator([col], settings=settings)

        edited = existing.model_copy(deep=True)
        edited.url = "ws://new.example.com"
        parent = MagicMock()
        with patch(
            "pypost.ui.websocket_save_orchestrator.confirm_overwrite_request",
            return_value=True,
        ) as confirm:
            result = orch.save_profile(edited, parent)

        confirm.assert_called_once()
        self.assertEqual(result.action, SaveAction.OVERWRITE)
        self.assertEqual(result.collection_id, "c1")
        found = registry.find_websocket("ws1")
        self.assertIsNotNone(found)
        self.assertEqual(found[0].url, "ws://new.example.com")
        self.assertEqual(found[0].id, "ws1")

    def test_save_stale_cancelled(self):
        disk = _make_ws("ws1", "On Disk", "ws://disk.example.com")
        col = Collection(id="c1", name="API", websockets=[disk])
        settings = AppSettings(confirm_overwrite_request=False)
        orch, registry, _rm, _sm = self._make_orchestrator([col], settings=settings)

        edited = _make_ws("ws1", "Tab Edit", "ws://tab.example.com")
        stale = StaleCheckContext(
            persisted_baseline=_make_ws("ws1", "Baseline", "ws://baseline.example.com"),
            stale_persisted=True,
        )
        parent = MagicMock()
        with patch(
            "pypost.ui.websocket_save_orchestrator.confirm_overwrite_newer_saved_version",
            return_value=False,
        ):
            result = orch.save_profile(edited, parent, stale_context=stale)

        self.assertEqual(result.action, SaveAction.CANCELLED)
        found = registry.find_websocket("ws1")
        self.assertIsNotNone(found)
        self.assertEqual(found[0].url, "ws://disk.example.com")
        self.assertEqual(found[0].name, "On Disk")

    def test_save_as_assigns_new_id(self):
        source = _make_ws("ws1", "Source", "ws://original.example.com")
        col = Collection(id="c1", name="API", websockets=[source])
        orch, registry, _rm, _sm = self._make_orchestrator([col])

        save_input = source.model_copy(deep=True)
        save_input.url = "ws://copy.example.com"
        mock_dialog = _mock_save_dialog(request_name="Copy")
        parent = MagicMock()
        with patch(
            "pypost.ui.websocket_save_orchestrator.SaveRequestDialog",
            return_value=mock_dialog,
        ):
            result = orch.save_as_profile(save_input, parent)

        self.assertEqual(result.action, SaveAction.SAVE_AS)
        self.assertEqual(result.collection_id, "c1")
        profile = _result_profile(result)
        self.assertIsNotNone(profile)
        self.assertNotEqual(profile.id, "ws1")
        self.assertEqual(profile.name, "Copy")
        self.assertEqual(profile.url, "ws://copy.example.com")

        original = registry.find_websocket("ws1")
        self.assertIsNotNone(original)
        self.assertEqual(original[0].url, "ws://original.example.com")
        self.assertEqual(original[0].name, "Source")

        new_found = registry.find_websocket(profile.id)
        self.assertIsNotNone(new_found)
        self.assertEqual(new_found[0].name, "Copy")
        self.assertEqual(new_found[1].id, "c1")


if __name__ == "__main__":
    unittest.main()
