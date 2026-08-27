"""Tests for McpClientSaveOrchestrator (PYPOST-1172 / MCP-TM-7)."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

import pytest

from pypost.core.mcp_client_registry import McpClientRegistry
from pypost.models.mcp_client import McpClientConnection
from pypost.models.models import Collection
from pypost.models.settings import AppSettings
from pypost.ui.mcp_client_save_orchestrator import McpClientSaveOrchestrator
from pypost.ui.request_save_orchestrator import SaveAction
from tests.test_request_save_orchestrator import _mock_save_dialog
from tests.test_tabs_presenter import FakeRequestManager, FakeStateManager

pytestmark = pytest.mark.timeout(60)


def _make_profile(
    profile_id: str = "mcp1",
    name: str = "Local MCP",
    url: str = "http://127.0.0.1:1080/mcp",
) -> McpClientConnection:
    return McpClientConnection(id=profile_id, name=name, url=url)


@pytest.mark.usefixtures("qapp")
class TestMcpClientSaveOrchestrator(unittest.TestCase):
    def _make_orchestrator(self, collections=None, settings=None):
        rm = FakeRequestManager()
        rm.collections = list(collections or [])
        registry = McpClientRegistry(rm, storage=MagicMock())
        sm = FakeStateManager()
        orch = McpClientSaveOrchestrator(
            registry,
            sm,
            settings or AppSettings(),
            metrics=MagicMock(),
        )
        return orch, registry, rm, sm

    def test_save_draft_to_collection(self):
        col = Collection(id="c1", name="API", mcp_clients=[])
        orch, registry, _rm, _sm = self._make_orchestrator([col])
        draft = _make_profile("mcp-draft", "Draft", "http://draft.example.com/mcp")

        mock_dialog = _mock_save_dialog(
            collection_id="c1",
            request_name="Saved MCP",
        )
        with patch(
            "pypost.ui.mcp_client_save_orchestrator.SaveRequestDialog",
            return_value=mock_dialog,
        ):
            result = orch.save_profile(draft, MagicMock())

        self.assertEqual(result.action, SaveAction.CREATED_NEW)
        self.assertIsNotNone(result.request)
        self.assertEqual(result.collection_id, "c1")
        saved = registry.find_mcp_client("mcp-draft")
        self.assertIsNotNone(saved)
        _profile, saved_col = saved
        self.assertEqual(saved_col.id, "c1")
        self.assertEqual(_profile.name, "Saved MCP")

    def test_save_as_creates_new_profile_with_fresh_id(self):
        existing = _make_profile("mcp1", "Primary")
        col = Collection(id="c1", name="API", mcp_clients=[existing])
        orch, registry, _rm, _sm = self._make_orchestrator([col])

        mock_dialog = _mock_save_dialog(
            collection_id="c1",
            request_name="Copy MCP",
        )
        with patch(
            "pypost.ui.mcp_client_save_orchestrator.SaveRequestDialog",
            return_value=mock_dialog,
        ):
            result = orch.save_as_profile(existing, MagicMock())

        self.assertEqual(result.action, SaveAction.SAVE_AS)
        self.assertIsNotNone(result.request)
        self.assertNotEqual(result.request.id, "mcp1")
        self.assertEqual(result.request.name, "Copy MCP")
        self.assertIsNotNone(registry.find_mcp_client(result.request.id))

    def test_save_overwrite_existing_profile(self):
        existing = _make_profile("mcp1", "Primary", "http://old.example.com/mcp")
        col = Collection(id="c1", name="API", mcp_clients=[existing])
        settings = AppSettings(confirm_overwrite_request=False)
        orch, registry, _rm, _sm = self._make_orchestrator([col], settings=settings)

        updated = _make_profile("mcp1", "Primary", "http://new.example.com/mcp")
        result = orch.save_profile(updated, MagicMock())

        self.assertEqual(result.action, SaveAction.OVERWRITE)
        saved = registry.find_mcp_client("mcp1")
        self.assertIsNotNone(saved)
        profile, _col = saved
        self.assertEqual(profile.url, "http://new.example.com/mcp")


if __name__ == "__main__":
    unittest.main()
