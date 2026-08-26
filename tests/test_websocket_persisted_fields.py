"""Unit tests for Qt-free WebSocket draft field comparison."""

import unittest

import pytest

from pypost.core.websocket_persisted_fields import (
    factory_websocket_draft,
    websocket_draft_fields_equal,
)
from pypost.models.websocket import WebSocketConnection, WebSocketMessagePreset

pytestmark = pytest.mark.timeout(10)


class TestWebsocketPersistedFields(unittest.TestCase):
    def test_factory_matches_new_connection_ignoring_id(self):
        factory = factory_websocket_draft()
        draft = WebSocketConnection()
        self.assertNotEqual(factory.id, draft.id)
        self.assertTrue(websocket_draft_fields_equal(factory, draft))

    def test_url_change_is_not_equal(self):
        factory = factory_websocket_draft()
        edited = WebSocketConnection(url="ws://example.com/stream")
        self.assertFalse(websocket_draft_fields_equal(factory, edited))

    def test_name_change_is_not_equal(self):
        factory = factory_websocket_draft()
        edited = WebSocketConnection(name="Renamed")
        self.assertFalse(websocket_draft_fields_equal(factory, edited))

    def test_mcp_flag_change_is_not_equal(self):
        factory = factory_websocket_draft()
        edited = WebSocketConnection(expose_as_mcp=True)
        self.assertFalse(websocket_draft_fields_equal(factory, edited))

    def test_preset_change_is_not_equal(self):
        factory = factory_websocket_draft()
        edited = WebSocketConnection(
            presets=[WebSocketMessagePreset(name="Ping", payload="{}")]
        )
        self.assertFalse(websocket_draft_fields_equal(factory, edited))
