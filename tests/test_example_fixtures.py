"""Contract tests for shipped examples/ fixtures (PYPOST-1017 / 1026 / 1047 / 1028)."""

from __future__ import annotations

import re
from collections.abc import Sequence
from pathlib import Path

import pytest

from pypost.core.collection_import import load_collection_import_candidates
from pypost.core.environment_import import load_import_candidates
from pypost.core.mcp_secrets_policy import McpSecretsPolicy
from pypost.core.mcp_tool_contract import normalize_mcp_tool_name
from pypost.core.storage import StorageManager
from pypost.core.template_service import TemplateService
from pypost.models.models import Collection, Environment, RequestData

pytestmark = pytest.mark.timeout(30)

REPO_ROOT = Path(__file__).resolve().parents[1]
JIRA_COLLECTION_PATH = REPO_ROOT / "examples" / "collections" / "jira_mcp.json"
JIRA_ENV_PATH = REPO_ROOT / "examples" / "environments" / "jira_cloud.json"
MCP_PROBE_PATH = REPO_ROOT / "examples" / "collections" / "mcp.json"

PLACEHOLDER_BASE_URL = "https://your-team.atlassian.net"
PLACEHOLDER_CREDENTIALS = "you@example.com:your-api-token"

# PYPOST-1039: the read-only current-user smoke tool raises the published floor.
JIRA_MCP_MIN_EXPOSED_REQUESTS = 23

# PYPOST-1027: preserve the three accepted stretch operations as one contract.
PROTECTED_STRETCH_JIRA_MCP_OPERATIONS = (
    ("jira-get-worklog", "GET", ("/rest/api/3/issue/", "/worklog")),
    ("jira-move-issues-to-backlog", "POST", ("/rest/agile/1.0/backlog/issue",)),
    ("jira-search-assignable-users", "GET", ("/rest/api/3/user/assignable/search",)),
)

# Locked required capabilities (no stretch-swap escape hatch).
REQUIRED_JIRA_MCP_REQUEST_IDS = frozenset(
    {
        "jira-get-current-user",
        "jira-create-sprint",
        "jira-add-issues-to-sprint",
        "jira-get-sprint-issues",
        "jira-link-issue-parent",
        "jira-add-comment",
        "jira-assign-issue",
        # PYPOST-1047: delete sprint.
        "jira-delete-sprint",
    }
) | frozenset(request_id for request_id, _, _ in PROTECTED_STRETCH_JIRA_MCP_OPERATIONS)

JIRA_NUMERIC_IDENTIFIER_MAPPINGS = {
    "jira-list-board-sprints": "board_id",
    "jira-get-sprint": "sprint_id",
    "jira-update-sprint": "sprint_id",
    "jira-delete-sprint": "sprint_id",
    "jira-add-issues-to-sprint": "sprint_id",
    "jira-get-sprint-issues": "sprint_id",
}


def _make_storage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> StorageManager:
    monkeypatch.delenv("PYPOST_ENV_ENCRYPTION_ENABLED", raising=False)
    monkeypatch.delenv("PYPOST_ENV_ENCRYPTION_KEY", raising=False)
    return StorageManager(data_dir=tmp_path / "pypost-data")


def _load_jira_mcp_collection() -> Collection:
    collections, parse_errors = load_collection_import_candidates(JIRA_COLLECTION_PATH)
    assert parse_errors == []
    assert len(collections) == 1
    collection = collections[0]
    assert collection.id == "jira-cloud-mcp"
    return collection


def _load_jira_cloud_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Environment:
    storage = _make_storage(tmp_path, monkeypatch)
    environments, parse_errors = load_import_candidates(JIRA_ENV_PATH, storage)
    assert parse_errors == []
    assert len(environments) == 1
    return environments[0]


def _request_by_id(collection: Collection, request_id: str) -> RequestData:
    return next(request for request in collection.requests if request.id == request_id)


def _has_request(
    requests: list[RequestData],
    *,
    request_id: str | None = None,
    method: str | None = None,
    url_contains: tuple[str, ...] = (),
) -> bool:
    for request in requests:
        if request_id is not None and request.id != request_id:
            continue
        if method is not None and request.method.upper() != method.upper():
            continue
        if any(fragment not in request.url for fragment in url_contains):
            continue
        return True
    return False


def test_jira_mcp_collection_imports_via_native_loader():
    collection = _load_jira_mcp_collection()
    assert collection.name == "Jira Cloud MCP"
    assert len(collection.requests) >= JIRA_MCP_MIN_EXPOSED_REQUESTS
    assert all(request.expose_as_mcp for request in collection.requests)

    text = JIRA_COLLECTION_PATH.read_text(encoding="utf-8")
    assert "{{ jira_base_url }}" in text
    assert "base64(jira_credentials)" in text
    assert PLACEHOLDER_CREDENTIALS not in text


def test_jira_mcp_collection_covers_required_skill_capabilities():
    """PYPOST-1026/1047: curated analog must cover locked skill/workflow gaps."""
    collection = _load_jira_mcp_collection()
    requests = collection.requests
    request_ids = {request.id for request in requests}

    missing_ids = sorted(REQUIRED_JIRA_MCP_REQUEST_IDS - request_ids)
    assert not missing_ids, (
        "jira_mcp.json missing required MCP request ids: " + ", ".join(missing_ids)
    )

    assert _has_request(
        requests,
        request_id="jira-get-current-user",
        method="GET",
        url_contains=("{{ jira_base_url }}", "/rest/api/3/myself"),
    ), "current-user lookup must GET /rest/api/3/myself"
    current_user = next(request for request in requests if request.id == "jira-get-current-user")
    assert current_user.expose_as_mcp is True
    assert normalize_mcp_tool_name(current_user.name) == "jira_get_current_user"
    assert current_user.params == {}
    assert current_user.body == ""
    assert "base64(jira_credentials)" in current_user.headers.get("Authorization", "")
    assert current_user.headers.get("Accept") == "application/json"

    assert _has_request(
        requests,
        request_id="jira-create-sprint",
        method="POST",
        url_contains=("/rest/agile/1.0/sprint",),
    ), "create sprint must POST /rest/agile/1.0/sprint"
    assert _has_request(
        requests,
        request_id="jira-add-issues-to-sprint",
        method="POST",
        url_contains=("/rest/agile/1.0/sprint/", "/issue"),
    ), "sprint membership must POST .../sprint/{id}/issue"
    assert _has_request(
        requests,
        request_id="jira-get-sprint-issues",
        method="GET",
        url_contains=("/rest/agile/1.0/sprint/", "/issue"),
    ), "get sprint issues must GET .../sprint/{id}/issue"
    assert _has_request(
        requests,
        request_id="jira-link-issue-parent",
        method="PUT",
        url_contains=("/rest/api/3/issue/",),
    ), "epic/parent link must be a dedicated PUT issue request"
    assert _has_request(
        requests,
        request_id="jira-add-comment",
        method="POST",
        url_contains=("/comment",),
    ), "add comment must POST .../comment"
    assert _has_request(
        requests,
        request_id="jira-assign-issue",
        method="PUT",
        url_contains=("/assignee",),
    ), "assign issue must PUT .../assignee"
    # PYPOST-1047: delete sprint.
    assert _has_request(
        requests,
        request_id="jira-delete-sprint",
        method="DELETE",
        url_contains=("/rest/agile/1.0/sprint/",),
    ), "delete sprint must DELETE .../sprint/{id}"


@pytest.mark.parametrize(
    ("request_id", "method", "url_contains"),
    PROTECTED_STRETCH_JIRA_MCP_OPERATIONS,
)
def test_jira_mcp_collection_covers_protected_stretch_operations(
    request_id: str, method: str, url_contains: tuple[str, ...]
):
    """PYPOST-1027: each protected stretch ID keeps its intended operation."""
    requests = _load_jira_mcp_collection().requests
    operation = f"{method} {' '.join(url_contains)}"
    assert _has_request(
        requests,
        request_id=request_id,
        method=method,
        url_contains=url_contains,
    ), f"Jira MCP request {request_id} must remain {operation}"


def test_jira_mcp_numeric_identifier_paths_accept_decimal_strings_and_integers():
    """PYPOST-1038 R3: all and only path IDs use the dual-form contract."""
    collection = _load_jira_mcp_collection()
    request_by_id = {request.id: request for request in collection.requests}

    union_rows = {
        (request.id, name)
        for request in collection.requests
        for name, parameter in request.mcp_params.items()
        if parameter.type == "integer_or_string"
    }
    assert union_rows == set(JIRA_NUMERIC_IDENTIFIER_MAPPINGS.items())

    for request_id, parameter_name in JIRA_NUMERIC_IDENTIFIER_MAPPINGS.items():
        request = request_by_id[request_id]
        parameter = request.mcp_params[parameter_name]
        description = parameter.description.lower()
        assert parameter.type == "integer_or_string"
        assert "decimal" in description
        assert "string" in description
        assert "integer" in description
        assert f"{{{{ to_int(mcp.request.{parameter_name}) }}}}" in request.url


def test_jira_cloud_environment_imports_with_placeholders(tmp_path, monkeypatch):
    environment = _load_jira_cloud_environment(tmp_path, monkeypatch)
    assert environment.id == "jira-cloud-mcp-environment"
    assert environment.name == "Jira Cloud MCP"
    assert environment.variables["jira_base_url"] == PLACEHOLDER_BASE_URL
    assert environment.variables["jira_credentials"] == PLACEHOLDER_CREDENTIALS
    assert "jira_credentials" in environment.hidden_keys
    assert environment.enable_mcp is True


def test_jira_project_default_is_wired_as_soft_guidance(tmp_path, monkeypatch):
    """PYPOST-1032: Jira examples guide normal work without enforcing scope."""
    environment = _load_jira_cloud_environment(tmp_path, monkeypatch)
    assert environment.variables["jira_project_key"] == "YOUR_PROJECT_KEY"
    assert "jira_project_key" not in environment.hidden_keys
    assert environment.hidden_keys == {"jira_credentials"}

    collection = _load_jira_mcp_collection()
    requests_by_id = {request.id: request for request in collection.requests}

    boards = requests_by_id["jira-list-boards"]
    assert boards.params["projectKeyOrId"] == "{{ jira_project_key }}"
    assert "jira_project_key" in boards.mcp_description
    assert "project-scoped" in boards.mcp_description

    for request_id, payload_name in (
        ("jira-search-issues-jql", "search_payload"),
        ("jira-create-issue", "issue_payload"),
    ):
        request = requests_by_id[request_id]
        guidance = " ".join(
            [
                request.mcp_description,
                request.mcp_params[payload_name].description,
            ]
        ).lower()
        assert "jira_project_key" in guidance
        assert "normal" in guidance
        assert "explicit" in guidance
        assert "permitted" in guidance

    for request_id, selected_scope in (
        ("jira-list-board-sprints", "selected board"),
        ("jira-get-sprint-issues", "selected sprint"),
    ):
        guidance = requests_by_id[request_id].mcp_description.lower()
        assert selected_scope in guidance
        assert "not automatically project-scoped" in guidance

    readme = (
        REPO_ROOT / "examples" / "README.md"
    ).read_text(encoding="utf-8").lower()
    assert "jira_project_key" in readme
    assert "set" in readme
    assert "not an authorization" in readme
    assert "not a security boundary" in readme


def test_mcp_probe_collection_still_imports():
    collections, parse_errors = load_collection_import_candidates(MCP_PROBE_PATH)

    assert parse_errors == []
    assert len(collections) == 1
    assert collections[0].id == "test-collection-mcp"
    assert collections[0].name == "MCP"
    assert len(collections[0].requests) == 3


# ---------------------------------------------------------------------------
# PYPOST-1028: Jira MCP fixture contracts (env / auth / mcp_params / allowlist)
#
# Shared checkers + fixed-input allowlist (Option A: test-module only).
# ---------------------------------------------------------------------------

_JIRA_MCP_AUTH_HEADER = "Basic {{ base64(jira_credentials) }}"
_NON_ALLOWLISTED_JIRA_MCP_REQUEST_ID = "jira-get-issue"

# Sole escape hatch for empty mcp_params (PYPOST-1029 may drop jira-list-boards).
FIXED_INPUT_JIRA_MCP_REQUEST_IDS = frozenset(
    {
        "jira-get-current-user",
        "jira-list-boards",
    }
)

# Broader than McpSecretsPolicy: also matches to_int(mcp.request.*), etc.
_MCP_REQUEST_NAME_PATTERN = re.compile(r"mcp\.request\.([a-zA-Z0-9_]+)")


def _jira_mcp_template_fields(request: RequestData) -> list[str]:
    fields: list[str] = [request.url, request.body]
    fields.extend(request.headers.values())
    fields.extend(request.params.values())
    return [field for field in fields if field]


def _extract_mcp_request_names(request: RequestData) -> set[str]:
    found: set[str] = set()
    for content in _jira_mcp_template_fields(request):
        found.update(_MCP_REQUEST_NAME_PATTERN.findall(content))
    return found


def _is_agent_driven_query_or_body(request: RequestData) -> bool:
    texts: list[str] = [request.body, *request.params.values()]
    return any("mcp.request." in text for text in texts if text)


def assert_jira_mcp_companion_env_coverage(
    collection: Collection, environment: Environment
) -> None:
    """Referenced env template names must be ⊆ companion environment.variables."""
    template_service = TemplateService()
    referenced: set[str] = set()
    for request in collection.requests:
        referenced.update(
            McpSecretsPolicy.extract_environment_variable_names(
                request, template_service
            )
        )
    missing = referenced - set(environment.variables)
    assert not missing, f"Missing companion key(s): {sorted(missing)}"


def assert_jira_mcp_auth_convention(requests: Sequence[RequestData]) -> None:
    """Every request must use Basic {{ base64(jira_credentials) }}."""
    for request in requests:
        auth = request.headers.get("Authorization", "")
        assert auth == _JIRA_MCP_AUTH_HEADER, (
            f"Request {request.id} auth convention breach "
            f"(expected Basic base64(jira_credentials))"
        )


def assert_jira_mcp_params_declared(request: RequestData) -> None:
    """Every mcp.request.<name> (incl. wrappers) must be in mcp_params."""
    missing = sorted(
        name
        for name in _extract_mcp_request_names(request)
        if name not in request.mcp_params
    )
    assert not missing, (
        f"Request {request.id} missing mcp_params key(s): {missing}"
    )


def assert_jira_mcp_fixed_input_allowlist(
    requests: Sequence[RequestData],
) -> None:
    """Empty mcp_params ids must equal FIXED_INPUT_JIRA_MCP_REQUEST_IDS."""
    empty_ids = {request.id for request in requests if not request.mcp_params}
    assert empty_ids == FIXED_INPUT_JIRA_MCP_REQUEST_IDS, (
        f"empty mcp_params ids {sorted(empty_ids)} != "
        f"FIXED_INPUT_JIRA_MCP_REQUEST_IDS "
        f"{sorted(FIXED_INPUT_JIRA_MCP_REQUEST_IDS)}"
    )


def assert_jira_mcp_agent_driven_declares_inputs(request: RequestData) -> None:
    """Agent-driven params/body require mcp_params unless allowlisted."""
    if not _is_agent_driven_query_or_body(request):
        return
    if request.mcp_params:
        return
    assert request.id in FIXED_INPUT_JIRA_MCP_REQUEST_IDS, (
        f"Request {request.id} is agent-driven without mcp_params "
        f"and outside FIXED_INPUT_JIRA_MCP_REQUEST_IDS"
    )


def test_jira_mcp_companion_env_covers_referenced_template_names(
    tmp_path, monkeypatch
):
    """Shipped collection env refs must be ⊆ companion environment variables."""
    collection = _load_jira_mcp_collection()
    environment = _load_jira_cloud_environment(tmp_path, monkeypatch)
    assert_jira_mcp_companion_env_coverage(collection, environment)


def test_jira_mcp_companion_env_coverage_rejects_missing_base_url(
    tmp_path, monkeypatch
):
    """Mutation: drop jira_base_url → checker names the missing companion key."""
    collection = _load_jira_mcp_collection()
    environment = _load_jira_cloud_environment(tmp_path, monkeypatch).model_copy(
        deep=True
    )
    del environment.variables["jira_base_url"]

    with pytest.raises(AssertionError, match=r"jira_base_url"):
        assert_jira_mcp_companion_env_coverage(collection, environment)


def test_jira_mcp_requests_use_basic_auth_convention():
    """Every shipped request must use Basic {{ base64(jira_credentials) }}."""
    collection = _load_jira_mcp_collection()
    assert_jira_mcp_auth_convention(collection.requests)


def test_jira_mcp_auth_convention_rejects_altered_authorization():
    """Mutation: alter Authorization → checker names the request id."""
    collection = _load_jira_mcp_collection()
    request = _request_by_id(collection, _NON_ALLOWLISTED_JIRA_MCP_REQUEST_ID)
    mutated = request.model_copy(deep=True)
    mutated.headers["Authorization"] = "Bearer not-the-jira-convention"
    assert mutated.headers["Authorization"] != _JIRA_MCP_AUTH_HEADER

    with pytest.raises(AssertionError, match=r"jira-get-issue"):
        assert_jira_mcp_auth_convention([mutated])


def test_jira_mcp_params_declare_all_mcp_request_names():
    """Every mcp.request.<name> (incl. wrappers) must appear in mcp_params."""
    collection = _load_jira_mcp_collection()
    for request in collection.requests:
        assert_jira_mcp_params_declared(request)


def test_jira_mcp_params_declared_rejects_dropped_issue_key():
    """Mutation: drop issue_key from mcp_params while URL still references it."""
    collection = _load_jira_mcp_collection()
    request = _request_by_id(collection, "jira-get-issue")
    mutated = request.model_copy(deep=True)
    assert "issue_key" in mutated.mcp_params
    assert "mcp.request.issue_key" in mutated.url
    del mutated.mcp_params["issue_key"]

    with pytest.raises(AssertionError, match=r"jira-get-issue.*issue_key|issue_key"):
        assert_jira_mcp_params_declared(mutated)


def test_jira_mcp_empty_mcp_params_match_fixed_input_allowlist():
    """Empty mcp_params request ids must equal FIXED_INPUT_JIRA_MCP_REQUEST_IDS."""
    collection = _load_jira_mcp_collection()
    assert_jira_mcp_fixed_input_allowlist(collection.requests)


def test_jira_mcp_fixed_input_allowlist_rejects_empty_outside_allowlist():
    """Mutation: clear mcp_params on a non-allowlisted id → outside allowlist."""
    collection = _load_jira_mcp_collection()
    request = _request_by_id(collection, _NON_ALLOWLISTED_JIRA_MCP_REQUEST_ID)
    mutated = request.model_copy(deep=True)
    assert mutated.mcp_params
    mutated.mcp_params = {}

    requests = [
        mutated if item.id == mutated.id else item for item in collection.requests
    ]
    with pytest.raises(AssertionError, match=r"jira-get-issue"):
        assert_jira_mcp_fixed_input_allowlist(requests)


def test_jira_mcp_fixed_input_allowlist_rejects_empty_set_drift():
    """Mutation: empty-mcp_params set drifts from FIXED_INPUT allowlist."""
    collection = _load_jira_mcp_collection()
    request = _request_by_id(collection, "jira-search-fields")
    mutated = request.model_copy(deep=True)
    assert mutated.mcp_params
    mutated.mcp_params = {}

    requests = [
        mutated if item.id == mutated.id else item for item in collection.requests
    ]
    with pytest.raises(
        AssertionError, match=r"FIXED_INPUT_JIRA_MCP_REQUEST_IDS|jira-search-fields"
    ):
        assert_jira_mcp_fixed_input_allowlist(requests)


def test_jira_mcp_agent_driven_query_body_requires_mcp_params():
    """Agent-driven params/body imply non-empty mcp_params unless allowlisted."""
    collection = _load_jira_mcp_collection()
    for request in collection.requests:
        assert_jira_mcp_agent_driven_declares_inputs(request)


def test_jira_mcp_agent_driven_rejects_body_without_mcp_params():
    """Mutation: agent-driven body + empty mcp_params on non-allowlisted id."""
    collection = _load_jira_mcp_collection()
    request = _request_by_id(collection, _NON_ALLOWLISTED_JIRA_MCP_REQUEST_ID)
    mutated = request.model_copy(deep=True)
    mutated.mcp_params = {}
    mutated.body = '{"value": "{{ mcp.request.x }}"}'
    mutated.params = {}

    with pytest.raises(AssertionError, match=r"jira-get-issue"):
        assert_jira_mcp_agent_driven_declares_inputs(mutated)
