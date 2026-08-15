"""CI-safe Jira MCP collection e2e workflow (PYPOST-1053)."""

from __future__ import annotations

import json
from pathlib import Path

import anyio
import pytest

from pypost.core.collection_import import load_collection_import_candidates
from pypost.core.mcp_tool_contract import normalize_mcp_tool_name
from tests.helpers.mcp_collection_http import stub_jira_mcp_collection_http
from tests.helpers.mcp_live_server import live_mcp_server
from tests.test_mcp_server_integration import _mcp_call_tool_result


pytestmark = pytest.mark.timeout(30)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_JIRA_COLLECTION_PATH = _REPO_ROOT / "examples" / "collections" / "jira_mcp.json"
_TOOL_IDS = (
    "jira-get-current-user",
    "jira-search-issues-jql",
    "jira-get-issue",
    "jira-list-boards",
)
_TOOL_NAMES = (
    "jira_get_current_user",
    "jira_search_issues_jql",
    "jira_get_issue",
    "jira_list_boards",
)


def _load_collection_tools():
    """Return only the four committed read-only workflow requests."""
    collections, parse_errors = load_collection_import_candidates(_JIRA_COLLECTION_PATH)
    assert parse_errors == []
    assert len(collections) == 1

    requests_by_id = {request.id: request for request in collections[0].requests}
    tools = [requests_by_id[request_id] for request_id in _TOOL_IDS]
    assert [normalize_mcp_tool_name(tool.name) for tool in tools] == list(_TOOL_NAMES)
    return tools


def _successful_jira_body(result, operation: str) -> dict[str, object]:
    """Decode one successful MCP envelope without exposing response content on failure."""
    try:
        envelope = json.loads(result.content[0].text)
        body = json.loads(envelope["body"])
    except (AttributeError, IndexError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise AssertionError(f"{operation} did not return a Jira JSON response") from exc

    assert result.isError is False, f"{operation} returned an MCP error"
    assert envelope.get("error") is False, f"{operation} returned a request error"
    assert 200 <= envelope.get("status", 0) < 300, f"{operation} did not succeed"
    assert isinstance(body, dict), f"{operation} did not return a Jira JSON object"
    return body


async def _run_collection_workflow(mcp_url: str) -> str:
    """Call the four collection tools in user-flow order through Streamable HTTP."""
    current_user = await _mcp_call_tool_result(mcp_url, _TOOL_NAMES[0])
    current_user_body = _successful_jira_body(current_user, "current user")
    assert isinstance(current_user_body.get("accountId"), str)
    assert current_user_body["accountId"]

    search_payload = {"jql": "project = OFFLINE", "maxResults": 1, "fields": ["key"]}
    search = await _mcp_call_tool_result(
        mcp_url,
        _TOOL_NAMES[1],
        {"search_payload": json.dumps(search_payload)},
    )
    search_body = _successful_jira_body(search, "issue search")
    try:
        issue_key = search_body["issues"][0]["key"]
    except (IndexError, KeyError, TypeError) as exc:
        raise AssertionError("issue search did not return a usable issue key") from exc
    assert isinstance(issue_key, str)
    assert issue_key

    issue = await _mcp_call_tool_result(
        mcp_url,
        _TOOL_NAMES[2],
        {"issue_key": issue_key},
    )
    issue_body = _successful_jira_body(issue, "issue retrieval")
    assert issue_body.get("key") == issue_key

    boards = await _mcp_call_tool_result(
        mcp_url,
        _TOOL_NAMES[3],
        {"maxResults": 1, "startAt": 0},
    )
    boards_body = _successful_jira_body(boards, "board listing")
    assert isinstance(boards_body.get("values"), list)
    assert boards_body["values"]
    return issue_key


def test_jira_collection_runs_four_read_tools_against_loopback_http() -> None:
    """The real MCP request stack must render and dispatch the offline workflow."""
    tools = _load_collection_tools()
    with stub_jira_mcp_collection_http() as stub:
        variables = {
            "jira_base_url": stub.base_url,
            "jira_credentials": "offline-only-credential",
            "jira_project_key": "OFFLINE",
        }
        with live_mcp_server(tools) as server:
            server.impl.set_variable_supplier(lambda: variables)
            server.impl.set_hidden_keys_supplier(
                lambda: {"jira_base_url", "jira_credentials"}
            )
            issue_key = anyio.run(_run_collection_workflow, server.mcp_url)

    assert [(request.method, request.path) for request in stub.requests] == [
        ("GET", "/rest/api/3/myself"),
        ("POST", "/rest/api/3/search/jql"),
        ("GET", "/rest/api/3/issue/OFFLINE-1"),
        ("GET", "/rest/agile/1.0/board"),
    ]
    assert stub.requests[1].body == {
        "jql": "project = OFFLINE",
        "maxResults": 1,
        "fields": ["key"],
    }
    assert stub.requests[-1].query == {
        "maxResults": ["1"],
        "startAt": ["0"],
        "projectKeyOrId": ["OFFLINE"],
    }
    assert stub.requests[2].path == f"/rest/api/3/issue/{issue_key}"
