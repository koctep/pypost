"""Offline contracts for PYPOST-1039's optional, read-only Jira MCP smoke."""

from __future__ import annotations

from collections.abc import Mapping
import json
import logging
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

import anyio
import pytest

from pypost.core.collection_import import load_collection_import_candidates
from pypost.core.mcp_tool_contract import normalize_mcp_tool_name
from tests.helpers.ci_workflow_yaml import workflow_job_block
from tests.helpers.mcp_live_server import free_port, live_mcp_server
from tests.makefile_contract_helpers import makefile_target_recipe_body
from tests.test_mcp_server_integration import _mcp_call_tool_result


pytestmark = pytest.mark.timeout(30)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_JIRA_COLLECTION_PATH = _REPO_ROOT / "examples" / "collections" / "jira_mcp.json"
_WORKFLOW_PATH = _REPO_ROOT / ".github" / "workflows" / "test.yml"
_MAKEFILE_PATH = _REPO_ROOT / "Makefile"

_OPT_IN_NAME = "PYPOST_LIVE_JIRA_SMOKE"
_REQUIRED_CONFIGURATION_NAMES = (
    "JIRA_BASE_URL",
    "JIRA_CREDENTIALS",
    "JIRA_PROJECT_KEY",
)
_SKIP_REASON = "live Jira MCP smoke intentionally skipped: opt-in is not enabled"
_INVALID_CONFIGURATION_REASON = "live Jira MCP smoke configuration is incomplete or invalid"
_COMMITTED_PLACEHOLDERS = {
    "https://your-team.atlassian.net",
    "you@example.com:your-api-token",
    "YOUR_PROJECT_KEY",
}
_SMOKE_REQUEST_IDS = (
    "jira-get-current-user",
    "jira-search-issues-jql",
    "jira-get-issue",
    "jira-list-boards",
)
_SMOKE_TOOL_NAMES = (
    "jira_get_current_user",
    "jira_search_issues_jql",
    "jira_get_issue",
    "jira_list_boards",
)
_SMOKE_READ_ONLY_CONTRACTS = (
    (
        "jira-get-current-user",
        "jira_get_current_user",
        "GET",
        "{{ jira_base_url }}/rest/api/3/myself",
        frozenset(),
        "",
    ),
    (
        "jira-search-issues-jql",
        "jira_search_issues_jql",
        "POST",
        "{{ jira_base_url }}/rest/api/3/search/jql",
        frozenset({"search_payload"}),
        "{{ mcp.request.search_payload }}",
    ),
    (
        "jira-get-issue",
        "jira_get_issue",
        "GET",
        "{{ jira_base_url }}/rest/api/3/issue/{{ mcp.request.issue_key }}",
        frozenset({"issue_key"}),
        "",
    ),
    (
        "jira-list-boards",
        "jira_list_boards",
        "GET",
        "{{ jira_base_url }}/rest/agile/1.0/board",
        frozenset({"maxResults", "startAt"}),
        "",
    ),
)


class _LiveSmokeOperationFailure(Exception):
    """Internal failure that deliberately carries only a fixed operation label."""

    def __init__(self, operation: str) -> None:
        self.operation = operation


def _live_smoke_configuration(environment: Mapping[str, str]) -> dict[str, str]:
    """Apply the planned process-only opt-in gate without exposing values."""
    if environment.get(_OPT_IN_NAME) != "1":
        pytest.skip(_SKIP_REASON)

    values = {name: environment.get(name, "") for name in _REQUIRED_CONFIGURATION_NAMES}
    base_url = values["JIRA_BASE_URL"]
    try:
        parsed_base_url = urlsplit(base_url)
        base_url_is_valid = (
            parsed_base_url.scheme == "https"
            and parsed_base_url.hostname is not None
            and parsed_base_url.username is None
            and parsed_base_url.password is None
            and not any(character.isspace() for character in base_url)
        )
        _ = parsed_base_url.port
    except ValueError:
        base_url_is_valid = False
    if (
        any(not value or value in _COMMITTED_PLACEHOLDERS for value in values.values())
        or not base_url_is_valid
    ):
        pytest.fail(_INVALID_CONFIGURATION_REASON)
    return values


def _load_current_user_request():
    collections, parse_errors = load_collection_import_candidates(_JIRA_COLLECTION_PATH)
    assert parse_errors == []
    return next(
        (request for request in collections[0].requests if request.id == "jira-get-current-user"),
        None,
    )


def _load_smoke_requests():
    """Load exactly the four read-only tools permitted to the live smoke."""
    collections, parse_errors = load_collection_import_candidates(_JIRA_COLLECTION_PATH)
    if parse_errors or len(collections) != 1:
        raise _LiveSmokeOperationFailure("tool setup")
    requests_by_id = {request.id: request for request in collections[0].requests}
    try:
        tools = [requests_by_id[request_id] for request_id in _SMOKE_REQUEST_IDS]
    except KeyError as exc:
        raise _LiveSmokeOperationFailure("tool setup") from exc
    for tool, contract in zip(tools, _SMOKE_READ_ONLY_CONTRACTS, strict=True):
        request_id, tool_name, method, url, input_names, body = contract
        if (
            tool.id != request_id
            or normalize_mcp_tool_name(tool.name) != tool_name
            or tool.method.upper() != method
            or tool.url != url
            or set(tool.mcp_params) != input_names
            or tool.body != body
            or not tool.expose_as_mcp
        ):
            raise _LiveSmokeOperationFailure("tool setup")
    return tools


def _successful_response_payload(result, operation: str) -> dict[str, object]:
    """Accept only a successful 2xx MCP result without surfacing its contents."""
    try:
        payload = json.loads(result.content[0].text)
    except (AttributeError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise _LiveSmokeOperationFailure(operation) from exc
    if (
        result.isError
        or not isinstance(payload, dict)
        or payload.get("error") is not False
        or not isinstance(payload.get("status"), int)
        or not 200 <= payload["status"] < 300
    ):
        raise _LiveSmokeOperationFailure(operation)
    return payload


async def _run_live_smoke(mcp_url: str, project_key: str) -> None:
    """Make the four permitted calls in order and retain response data only in memory."""
    current_user = await _mcp_call_tool_result(mcp_url, _SMOKE_TOOL_NAMES[0])
    _successful_response_payload(current_user, "current user")

    search_payload = json.dumps(
        {
            "jql": f"project = {project_key}",
            "maxResults": 1,
            "fields": ["key"],
        }
    )
    search = await _mcp_call_tool_result(
        mcp_url,
        _SMOKE_TOOL_NAMES[1],
        {"search_payload": search_payload},
    )
    search_response = _successful_response_payload(search, "issue search")
    try:
        search_body = json.loads(search_response["body"])
        issue_key = search_body["issues"][0]["key"]
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise _LiveSmokeOperationFailure("issue search") from exc
    if not isinstance(issue_key, str) or not issue_key:
        raise _LiveSmokeOperationFailure("issue search")

    issue = await _mcp_call_tool_result(
        mcp_url,
        _SMOKE_TOOL_NAMES[2],
        {"issue_key": issue_key},
    )
    _successful_response_payload(issue, "issue retrieval")

    boards = await _mcp_call_tool_result(
        mcp_url,
        _SMOKE_TOOL_NAMES[3],
        {"maxResults": 50, "startAt": 0},
    )
    _successful_response_payload(boards, "board listing")


def test_live_smoke_skips_by_default_without_reading_jira_configuration() -> None:
    """Absent opt-in is an intentional, value-free skip even with ambient settings."""
    environment = {
        "JIRA_BASE_URL": "not examined",
        "JIRA_CREDENTIALS": "not examined",
        "JIRA_PROJECT_KEY": "not examined",
    }
    with pytest.raises(pytest.skip.Exception, match=_SKIP_REASON):
        _live_smoke_configuration(environment)


@pytest.mark.parametrize(
    "environment",
    (
        {_OPT_IN_NAME: "1"},
        {
            _OPT_IN_NAME: "1",
            "JIRA_BASE_URL": "https://your-team.atlassian.net",
            "JIRA_CREDENTIALS": "protected-value",
            "JIRA_PROJECT_KEY": "PROJECT",
        },
        {
            _OPT_IN_NAME: "1",
            "JIRA_BASE_URL": "not-a-url",
            "JIRA_CREDENTIALS": "protected-value",
            "JIRA_PROJECT_KEY": "PROJECT",
        },
        {
            _OPT_IN_NAME: "1",
            "JIRA_BASE_URL": "http://jira.example.invalid",
            "JIRA_CREDENTIALS": "protected-value",
            "JIRA_PROJECT_KEY": "PROJECT",
        },
        {
            _OPT_IN_NAME: "1",
            "JIRA_BASE_URL": "ftp://jira.example.invalid",
            "JIRA_CREDENTIALS": "protected-value",
            "JIRA_PROJECT_KEY": "PROJECT",
        },
        {
            _OPT_IN_NAME: "1",
            "JIRA_BASE_URL": "https://[",
            "JIRA_CREDENTIALS": "protected-value",
            "JIRA_PROJECT_KEY": "PROJECT",
        },
        {
            _OPT_IN_NAME: "1",
            "JIRA_BASE_URL": "https://jira example.invalid",
            "JIRA_CREDENTIALS": "protected-value",
            "JIRA_PROJECT_KEY": "PROJECT",
        },
    ),
)
def test_enabled_live_smoke_fails_with_one_generic_configuration_message(
    environment: dict[str, str],
) -> None:
    """Bad enabled configuration is never silently converted to a skip."""
    with pytest.raises(pytest.fail.Exception, match=_INVALID_CONFIGURATION_REASON):
        _live_smoke_configuration(environment)


def test_current_user_smoke_tool_uses_read_only_path() -> None:
    """The local stub proves the current-user path renders and dispatches safely."""
    current_user = _load_current_user_request()
    assert current_user is not None, "missing required read-only current-user MCP request"
    assert current_user.method == "GET"
    assert current_user.url.endswith("/rest/api/3/myself")
    assert normalize_mcp_tool_name(current_user.name) == "jira_get_current_user"
    assert current_user.params == {}
    assert current_user.body == ""

    stub_port = free_port()
    captured_paths: list[str] = []
    sensitive_values = {
        "jira_base_url": f"http://127.0.0.1:{stub_port}",
        "jira_credentials": "offline-only-credential",
    }

    class _StubHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            captured_paths.append(self.path)
            payload = b'{"accountId":"offline-only-response"}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, _format, *_args):
            return

    httpd = ThreadingHTTPServer(("127.0.0.1", stub_port), _StubHandler)
    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()
    previous_disable_level = logging.root.manager.disable
    logging.disable(logging.CRITICAL)
    try:
        tool = current_user.model_copy(
            update={
                "url": current_user.url.replace(
                    "{{ jira_base_url }}", sensitive_values["jira_base_url"]
                )
            },
            deep=True,
        )
        with live_mcp_server([tool]) as server:
            server.impl.set_variable_supplier(lambda: sensitive_values)
            server.impl.set_hidden_keys_supplier(lambda: set(sensitive_values))
            result = anyio.run(_mcp_call_tool_result, server.mcp_url, "jira_get_current_user")
    finally:
        logging.disable(previous_disable_level)
        httpd.shutdown()
        server_thread.join(timeout=2.0)

    assert result.isError is False
    assert captured_paths == ["/rest/api/3/myself"]


def test_live_smoke_loads_only_fixed_read_only_tool_contracts() -> None:
    """Prevent a renamed Jira fixture route from turning protected smoke into a write."""
    tools = _load_smoke_requests()
    assert [tool.id for tool in tools] == list(_SMOKE_REQUEST_IDS)
    assert [normalize_mcp_tool_name(tool.name) for tool in tools] == list(_SMOKE_TOOL_NAMES)


def test_normal_pr_jobs_do_not_invoke_live_target_or_map_jira_configuration() -> None:
    """Protected live execution belongs to a separate dispatch-only job, never PR CI."""
    workflow = _WORKFLOW_PATH.read_text(encoding="utf-8")
    assert "pull_request:" in workflow.split("jobs:", maxsplit=1)[0]
    for job_id in ("test", "make-install-smoke", "agent-e2e"):
        job = workflow_job_block(workflow, job_id, workflow_path=_WORKFLOW_PATH)
        assert "test-jira-mcp-live" not in job
        assert "JIRA_CREDENTIALS" not in job
        assert "JIRA_BASE_URL" not in job
        assert "JIRA_PROJECT_KEY" not in job

    makefile = _MAKEFILE_PATH.read_text(encoding="utf-8")
    for target in ("test", "test-slow"):
        assert "test-jira-mcp-live" not in makefile_target_recipe_body(makefile, target)


def test_live_smoke_has_a_separate_dispatch_only_ci_and_make_interface() -> None:
    """The protected opt-in path must exist without changing normal PR validation."""
    workflow = _WORKFLOW_PATH.read_text(encoding="utf-8")
    assert "workflow_dispatch:" in workflow.split("jobs:", maxsplit=1)[0]
    assert "pull_request_target:" not in workflow
    live_job = workflow_job_block(workflow, "jira-mcp-live-smoke", workflow_path=_WORKFLOW_PATH)
    assert "jira-live-smoke" in live_job
    assert "github.event_name == 'workflow_dispatch'" in live_job
    assert "github.ref == 'refs/heads/master'" in live_job
    assert "test-jira-mcp-live" in live_job
    assert "JIRA_CREDENTIALS" in live_job
    assert "${{ secrets.JIRA_CREDENTIALS }}" in live_job

    makefile = _MAKEFILE_PATH.read_text(encoding="utf-8")
    assert "test-jira-mcp-live:" in makefile


def test_live_smoke_job_summary_distinguishes_the_fixed_skip_outcome() -> None:
    """The protected summary reports only fixed pass, fail, or intentional-skip text."""
    workflow = _WORKFLOW_PATH.read_text(encoding="utf-8")
    live_job = workflow_job_block(workflow, "jira-mcp-live-smoke", workflow_path=_WORKFLOW_PATH)

    assert "id: protected-live-smoke" in live_job
    assert "PYTEST_ADDOPTS: --junitxml=jira-live-smoke-junit.xml" in live_job
    assert "ElementTree.parse(sys.argv[1])" in live_job
    assert f'expected_skip = "{_SKIP_REASON}"' in live_job
    assert 'print("intentionally skipped")' in live_job
    assert 'print("passed")' in live_job
    assert 'print("failed")' in live_job
    assert 'echo "Jira MCP live smoke: intentionally skipped"' in live_job
    assert 'echo "Jira MCP live smoke: passed"' in live_job
    assert 'echo "Jira MCP live smoke: failed"' in live_job

    summary = live_job.split("- name: Write job summary", maxsplit=1)[1]
    for sensitive_name in _REQUIRED_CONFIGURATION_NAMES:
        assert sensitive_name not in summary
    assert "jira_base_url" not in summary
    assert "jira_credentials" not in summary
    assert "jira_project_key" not in summary


@pytest.mark.slow
@pytest.mark.live_jira
@pytest.mark.timeout(90)
def test_opted_in_live_smoke_runs_only_four_read_only_jira_mcp_tools() -> None:
    """Exercise the authorized live path without recording service or response data."""
    configuration = _live_smoke_configuration(os.environ)
    variables = {
        "jira_base_url": configuration["JIRA_BASE_URL"],
        "jira_credentials": configuration["JIRA_CREDENTIALS"],
        "jira_project_key": configuration["JIRA_PROJECT_KEY"],
    }
    previous_disable_level = logging.root.manager.disable
    logging.disable(logging.CRITICAL)
    try:
        tools = _load_smoke_requests()
        if [normalize_mcp_tool_name(tool.name) for tool in tools] != list(_SMOKE_TOOL_NAMES):
            raise _LiveSmokeOperationFailure("tool setup")
        with live_mcp_server(tools) as server:
            server.impl.set_variable_supplier(lambda: variables)
            server.impl.set_hidden_keys_supplier(lambda: set(variables))
            anyio.run(_run_live_smoke, server.mcp_url, variables["jira_project_key"])
    except _LiveSmokeOperationFailure as exc:
        pytest.fail(f"live Jira MCP smoke operation failed: {exc.operation}")
    except Exception:
        pytest.fail("live Jira MCP smoke operation failed: local MCP transport")
    finally:
        logging.disable(previous_disable_level)
