"""PYPOST-552: user-facing MCP setup docs use Streamable HTTP /mcp URLs."""
import pytest
from pathlib import Path

pytestmark = pytest.mark.timeout(10)

REPO_ROOT = Path(__file__).resolve().parents[1]
USER_DOC = REPO_ROOT / "doc" / "mcp_integration.md"
TEST_README = REPO_ROOT / "config" / "test" / "README.md"
MCP_COLLECTION = REPO_ROOT / "examples" / "collections" / "mcp.json"


def test_user_mcp_doc_primary_url_is_streamable_http():
    text = USER_DOC.read_text(encoding="utf-8")
    assert "http://127.0.0.1:1080/mcp" in text
    assert "Type: **SSE**" not in text
    assert "1080/sse" not in text.split("### Cursor")[0]


def test_user_mcp_doc_cursor_section_uses_mcp_path():
    cursor_section = USER_DOC.read_text(encoding="utf-8").split("### Cursor", 1)[1]
    assert "1080/mcp" in cursor_section
    assert "Streamable HTTP" in cursor_section


def test_config_test_readme_list_tools_uses_mcp():
    text = TEST_README.read_text(encoding="utf-8")
    assert "1080/mcp" in text
    assert "List Tools" in text


def test_mcp_collection_list_tools_url_uses_mcp():
    text = MCP_COLLECTION.read_text(encoding="utf-8")
    assert '"url": "http://127.0.0.1:1080/mcp"' in text
