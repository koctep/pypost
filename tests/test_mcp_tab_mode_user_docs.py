"""PYPOST-1168: Contract tests for MCP tab-mode user documentation alignment."""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.timeout(10)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_USER = _REPO_ROOT / "doc" / "user"
_REQUESTS_DOC = _USER / "requests.md"
_INTERFACE_DOC = _USER / "interface.md"
_MCP_TOOLS_DOC = _USER / "mcp-tools.md"
_MCP_CLIENT_DOC = _USER / "mcp-client.md"


def test_requests_doc_does_not_document_http_method_mcp() -> None:
    """requests.md must not list MCP as an HTTP request method."""
    text = _REQUESTS_DOC.read_text(encoding="utf-8")
    lower = text.lower()
    assert "choose a method" in lower or "method:" in lower
    assert "**mcp**" not in text.split("## MCP Tool checkbox")[0]
    assert "method: **mcp**" not in lower
    assert "or **mcp**" not in lower


def test_requests_doc_points_to_mcp_client_guide() -> None:
    """requests.md must redirect outbound MCP readers to mcp-client.md."""
    text = _REQUESTS_DOC.read_text(encoding="utf-8")
    assert "mcp-client.md" in text
    assert "mcp client" in text.lower()


def test_interface_doc_describes_mcp_client_editor() -> None:
    """interface.md must document MCP Client as a workspace editor type."""
    text = _INTERFACE_DOC.read_text(encoding="utf-8")
    lower = text.lower()
    assert "## mcp client editor" in lower
    assert "connect" in lower
    assert "tool" in lower
    assert "headers" in lower
    assert "mcp-client.md" in text


def test_mcp_tools_doc_distinguishes_inbound_outbound() -> None:
    """mcp-tools.md must clearly separate inbound vs outbound MCP surfaces."""
    text = _MCP_TOOLS_DOC.read_text(encoding="utf-8")
    lower = text.lower()
    assert "inbound" in lower
    assert "outbound" in lower
    assert "mcp servers" in lower
    assert "mcp client" in lower
    assert "mcp-client.md" in text


def test_mcp_client_guide_exists_and_covers_workflow() -> None:
    """mcp-client.md must describe connect, list tools, and invoke."""
    assert _MCP_CLIENT_DOC.is_file()
    text = _MCP_CLIENT_DOC.read_text(encoding="utf-8")
    lower = text.lower()
    assert "protocol picker" in lower
    assert "connect" in lower
    assert "list" in lower and "tool" in lower
    assert "invoke" in lower
    assert "headers" in lower
