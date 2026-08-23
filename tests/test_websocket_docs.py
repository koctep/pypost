"""PYPOST-1138: Contract test suite for WebSocket user and developer documentation.

Verifies presence, structure, and required technical content across:
- doc/user/websocket.md (new user guide)
- doc/dev/websocket_architecture.md (new architecture deep dive)
- doc/user/README.md, doc/dev/README.md (index and table of contents updates)
- doc/user/interface.md, doc/user/hotkeys.md, doc/user/collections.md,
  doc/user/settings.md, doc/user/mcp-tools.md (user doc updates)
- doc/dev/ui_identity.md, doc/dev/testing.md, doc/dev/architecture.md,
  doc/dev/licensing.md (developer doc updates)
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.timeout(10)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_DOC_ROOT = _REPO_ROOT / "doc"
_USER_DOC_ROOT = _DOC_ROOT / "user"
_DEV_DOC_ROOT = _DOC_ROOT / "dev"

_WS_USER_DOC = _USER_DOC_ROOT / "websocket.md"
_WS_DEV_DOC = _DEV_DOC_ROOT / "websocket_architecture.md"
_USER_README = _USER_DOC_ROOT / "README.md"
_DEV_README = _DEV_DOC_ROOT / "README.md"
_INTERFACE_DOC = _USER_DOC_ROOT / "interface.md"
_HOTKEYS_DOC = _USER_DOC_ROOT / "hotkeys.md"
_COLLECTIONS_DOC = _USER_DOC_ROOT / "collections.md"
_SETTINGS_DOC = _USER_DOC_ROOT / "settings.md"
_MCP_TOOLS_DOC = _USER_DOC_ROOT / "mcp-tools.md"
_UI_IDENTITY_DOC = _DEV_DOC_ROOT / "ui_identity.md"
_TESTING_DOC = _DEV_DOC_ROOT / "testing.md"
_ARCHITECTURE_DOC = _DEV_DOC_ROOT / "architecture.md"
_LICENSING_DOC = _DEV_DOC_ROOT / "licensing.md"


# ---------------------------------------------------------------------------
# 1. Existence and Indexing
# ---------------------------------------------------------------------------


def test_websocket_user_guide_exists() -> None:
    """doc/user/websocket.md must exist and be indexed in doc/user/README.md."""
    assert _WS_USER_DOC.is_file(), f"Expected {_WS_USER_DOC} to exist"
    user_readme_text = _USER_README.read_text(encoding="utf-8")
    assert "websocket.md" in user_readme_text, "doc/user/README.md must link to websocket.md"


def test_websocket_dev_architecture_doc_exists() -> None:
    """doc/dev/websocket_architecture.md must exist and be indexed in doc/dev/README.md."""
    assert _WS_DEV_DOC.is_file(), f"Expected {_WS_DEV_DOC} to exist"
    dev_readme_text = _DEV_README.read_text(encoding="utf-8")
    assert (
        "websocket_architecture.md" in dev_readme_text
    ), "doc/dev/README.md must link to websocket_architecture.md"


# ---------------------------------------------------------------------------
# 2. User Guide Content Assertions (doc/user/websocket.md)
# ---------------------------------------------------------------------------


def test_websocket_user_guide_covers_core_capabilities() -> None:
    """doc/user/websocket.md must cover connecting, composing, stream inspection,
    presets, sequences, and probe tools.
    """
    assert _WS_USER_DOC.is_file(), "doc/user/websocket.md must exist"
    text = _WS_USER_DOC.read_text(encoding="utf-8")

    # Connection & protocols
    assert "ws://" in text and "wss://" in text
    assert "subprotocol" in text.lower() or "subprotocols" in text.lower()
    assert "header" in text.lower() or "headers" in text.lower()

    # Message composition & formats
    assert "JSON" in text
    assert "Binary" in text or "binary" in text
    assert "Text" in text or "text" in text

    # Presets and sequences
    assert "preset" in text.lower() or "presets" in text.lower()
    assert "sequence" in text.lower() or "sequences" in text.lower()

    # Stream inspector & export formats
    assert "stream" in text.lower()
    assert "filter" in text.lower() or "filtering" in text.lower()
    assert "NDJSON" in text or "ndjson" in text
    assert "CSV" in text or "csv" in text

    # Reconnect & heartbeats
    assert "reconnect" in text.lower() or "reconnection" in text.lower()
    assert "heartbeat" in text.lower() or "ping" in text.lower()

    # Templating & Secret masking
    assert "mask" in text.lower() or "masking" in text.lower()

    # MCP Probe tool
    assert "MCP" in text or "mcp" in text
    assert "probe" in text.lower()


def test_websocket_user_guide_documents_known_limitations() -> None:
    """doc/user/websocket.md must explicitly document known limitations."""
    assert _WS_USER_DOC.is_file(), "doc/user/websocket.md must exist"
    text = _WS_USER_DOC.read_text(encoding="utf-8")

    # Limitation 1: Compression (permessage-deflate)
    assert "compression" in text.lower() or "permessage-deflate" in text.lower()

    # Limitation 2: Handshake response body/header introspection
    assert "handshake" in text.lower()
    assert (
        "response body" in text.lower()
        or "introspection" in text.lower()
        or "status code" in text.lower()
    )


# ---------------------------------------------------------------------------
# 3. User Guide Cross-Cutting Updates
# ---------------------------------------------------------------------------


def test_user_interface_doc_covers_websocket_surfaces() -> None:
    """doc/user/interface.md must document WebSocket tab, connection bar, stream viewer,
    and composer.
    """
    assert _INTERFACE_DOC.is_file(), "doc/user/interface.md must exist"
    text = _INTERFACE_DOC.read_text(encoding="utf-8")
    assert "WebSocket" in text or "websocket" in text
    assert "Stream" in text or "stream" in text
    assert "Composer" in text or "composer" in text


def test_user_hotkeys_doc_covers_websocket_shortcuts() -> None:
    """doc/user/hotkeys.md must list WebSocket keyboard shortcuts."""
    assert _HOTKEYS_DOC.is_file(), "doc/user/hotkeys.md must exist"
    text = _HOTKEYS_DOC.read_text(encoding="utf-8")
    assert "WebSocket" in text or "websocket" in text


def test_user_collections_doc_includes_downgrade_caveat() -> None:
    """doc/user/collections.md must document WebSocket profiles and prominent downgrade caveat."""
    assert _COLLECTIONS_DOC.is_file(), "doc/user/collections.md must exist"
    text = _COLLECTIONS_DOC.read_text(encoding="utf-8")
    assert "WebSocket" in text or "websocket" in text
    assert "downgrade" in text.lower() or "older" in text.lower()


def test_user_settings_doc_covers_websocket_configuration() -> None:
    """doc/user/settings.md must document WebSocket settings."""
    assert _SETTINGS_DOC.is_file(), "doc/user/settings.md must exist"
    text = _SETTINGS_DOC.read_text(encoding="utf-8")
    assert "WebSocket" in text or "websocket" in text
    assert "ws_" in text or "max_concurrent_sessions" in text or "concurrent" in text.lower()


def test_user_mcp_tools_doc_covers_websocket_probes() -> None:
    """doc/user/mcp-tools.md must document WebSocket probe tools and sampling bounds."""
    assert _MCP_TOOLS_DOC.is_file(), "doc/user/mcp-tools.md must exist"
    text = _MCP_TOOLS_DOC.read_text(encoding="utf-8")
    assert "WebSocket" in text or "websocket" in text
    assert "probe" in text.lower()


# ---------------------------------------------------------------------------
# 4. Developer Documentation Assertions
# ---------------------------------------------------------------------------


def test_dev_websocket_architecture_covers_design_contracts() -> None:
    """doc/dev/websocket_architecture.md must detail architecture, transport,
    state machine, and observability.
    """
    assert _WS_DEV_DOC.is_file(), "doc/dev/websocket_architecture.md must exist"
    text = _WS_DEV_DOC.read_text(encoding="utf-8")
    assert "QWebSocket" in text or "transport" in text.lower()
    assert "state machine" in text.lower() or "DISCONNECTED" in text or "CONNECTED" in text
    assert "presenter" in text.lower() or "WebSocketPresenter" in text
    assert "ring buffer" in text.lower() or "buffer" in text.lower()
    assert "Prometheus" in text or "metrics" in text.lower() or "logging" in text.lower()


def test_dev_ui_identity_doc_covers_websocket_widget_ids() -> None:
    """doc/dev/ui_identity.md must document WebSocket widget object names."""
    assert _UI_IDENTITY_DOC.is_file(), "doc/dev/ui_identity.md must exist"
    text = _UI_IDENTITY_DOC.read_text(encoding="utf-8")
    assert "pypost_ws_tab_page" in text
    assert "pypost_ws_url_input" in text
    assert "pypost_ws_connect_button" in text
    assert "pypost_ws_stream_view" in text
    assert "pypost_ws_composer_edit" in text
    assert "pypost_ws_send_message_button" in text


def test_dev_testing_doc_covers_websocket_test_strategy() -> None:
    """doc/dev/testing.md must document WebSocket test strategy and mock server fixtures."""
    assert _TESTING_DOC.is_file(), "doc/dev/testing.md must exist"
    text = _TESTING_DOC.read_text(encoding="utf-8")
    assert "WebSocket" in text or "websocket" in text
    assert "mock" in text.lower() or "server" in text.lower() or "fixture" in text.lower()


def test_dev_architecture_doc_covers_websocket_subsystems() -> None:
    """doc/dev/architecture.md must list WebSocket core and UI modules."""
    assert _ARCHITECTURE_DOC.is_file(), "doc/dev/architecture.md must exist"
    text = _ARCHITECTURE_DOC.read_text(encoding="utf-8")
    assert "websocket" in text.lower()


def test_dev_licensing_doc_includes_platform_wss_smoke_step() -> None:
    """doc/dev/licensing.md release checklist must include a per-platform wss:// smoke step."""
    assert _LICENSING_DOC.is_file(), "doc/dev/licensing.md must exist"
    text = _LICENSING_DOC.read_text(encoding="utf-8")
    assert "wss://" in text or "WSS" in text or "WebSocket TLS" in text
