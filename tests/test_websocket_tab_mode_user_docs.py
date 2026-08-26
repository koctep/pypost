"""PYPOST-1163: Contract tests for WebSocket tab-mode user documentation alignment."""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.timeout(10)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_USER = _REPO_ROOT / "doc" / "user"
_WS_DOC = _USER / "websocket.md"
_INTERFACE_DOC = _USER / "interface.md"
_HOTKEYS_DOC = _USER / "hotkeys.md"
_COLLECTIONS_DOC = _USER / "collections.md"


def test_websocket_guide_step1_describes_protocol_picker() -> None:
    """Step 1 must describe blank-tab entry via protocol picker and saved profiles."""
    text = _WS_DOC.read_text(encoding="utf-8")
    assert "protocol picker" in text.lower()
    assert "ctrl+n" in text.lower() or "ctrl+n" in text
    assert "websocket" in text.lower()
    assert "new websocket" in text.lower()


def test_interface_doc_describes_protocol_picker_on_new_tab() -> None:
    """interface.md must document protocol choice on Ctrl+N and +."""
    text = _INTERFACE_DOC.read_text(encoding="utf-8")
    lower = text.lower()
    assert "protocol picker" in lower
    assert "ctrl+n" in lower
    assert "+" in text
    assert "websocket" in lower


def test_hotkeys_doc_matches_websocket_session_registration() -> None:
    """hotkeys.md WebSocket Session section must match registered shortcut keys."""
    text = _HOTKEYS_DOC.read_text(encoding="utf-8")
    assert "## WebSocket session" in text or "## WebSocket Session" in text
    assert "Connect / Disconnect" in text or "Connect" in text
    assert "F5" in text
    assert "Ctrl+Enter" in text or "Ctrl+Return" in text
    assert "Send Message" in text
    assert "Save WebSocket Profile" in text or "Save Profile" in text
    assert "Ctrl+S" in text
    assert "Save As WebSocket Profile" in text or "Save As Profile" in text
    assert "Ctrl+Shift+S" in text
    assert "Format JSON" in text
    assert "Ctrl+Shift+F" in text
    assert "Focus URL Bar" in text
    assert "Ctrl+L" in text
    assert "Alt+D" in text
    # New Tab must mention protocol picker, not HTTP-only draft
    assert "protocol picker" in text.lower()


def test_collections_doc_describes_websocket_new_tab() -> None:
    """collections.md must document WebSocket New tab isolated-copy behavior."""
    text = _COLLECTIONS_DOC.read_text(encoding="utf-8")
    lower = text.lower()
    assert "new tab" in lower
    assert "websocket" in lower
    assert "isolated" in lower or "separate editable copy" in lower
