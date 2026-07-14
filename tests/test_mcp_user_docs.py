"""PYPOST-552/680: user-facing MCP setup docs and envelope guidance."""
import pytest
from pathlib import Path

pytestmark = pytest.mark.timeout(10)

REPO_ROOT = Path(__file__).resolve().parents[1]
USER_DOC = REPO_ROOT / "doc" / "mcp_integration.md"
DEV_DOC = REPO_ROOT / "doc" / "dev" / "mcp_integration.md"
TEST_README = REPO_ROOT / "config" / "test" / "README.md"
MCP_COLLECTION = REPO_ROOT / "examples" / "collections" / "mcp.json"
CHECKLIST = REPO_ROOT / "ai-tasks" / "PYPOST-552" / "cursor-verification-checklist.md"


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


def test_user_mcp_doc_documents_json_envelope_parsing():
    text = USER_DOC.read_text(encoding="utf-8")
    assert "## Tool call responses (JSON envelope)" in text
    assert "json.loads" in text
    for field in ("status", "error", "body", "logs"):
        assert f"`{field}`" in text


def test_dev_mcp_doc_documents_agent_json_parsing():
    text = DEV_DOC.read_text(encoding="utf-8")
    assert "#### Agent parsing (PYPOST-680)" in text
    assert "json.loads(text_content.text)" in text


def test_cursor_checklist_mentions_envelope_fields():
    text = CHECKLIST.read_text(encoding="utf-8")
    assert "JSON envelope" in text
    for field in ("status", "error", "body"):
        assert field in text


def test_config_test_readme_mentions_envelope_parsing():
    text = TEST_README.read_text(encoding="utf-8")
    assert "json.loads" in text
    assert "status" in text and "error" in text and "body" in text
