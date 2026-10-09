"""Offline contracts for the GitHub MCP example collection (PYPOST-1334).

The GitHub pair (``examples/collections/github_mcp.json`` +
``examples/environments/github.json``), its locked REST path catalog
(``examples/collections/github_mcp_rest_paths.json``), the library manifest
entries and the README sections are checked here without any network access
beyond a loopback stub.

Missing artifacts are detected inside each test with ``Path.is_file()``
assertions, never at import or collection time, so a missing file is reported
as an assertion that names it.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

import anyio
import pytest
import requests

from pypost.core.collection_import import load_collection_import_candidates
from pypost.core.environment_import import load_import_candidates
from pypost.core.http_client import HTTPClient
from pypost.core.library_manifest import find_and_read_manifest, validate_manifest_collections
from pypost.core.mcp_secrets_policy import McpSecretsPolicy
from pypost.core.mcp_server_impl import MCPServerImpl
from pypost.core.mcp_tool_contract import McpArgumentValidationError, normalize_mcp_tool_name
from pypost.core.storage import StorageManager
from pypost.core.template_expression_types import IntegerConversionError
from pypost.core.template_service import TemplateService
from pypost.models.library_manifest import LibraryManifest
from pypost.models.models import Collection, Environment, McpToolParam, RequestData
from tests.helpers.github_mcp_collection_http import stub_github_mcp_collection_http
from tests.helpers.mcp_live_server import live_mcp_server
from tests.test_mcp_server_integration import _mcp_call_tool_result

pytestmark = pytest.mark.timeout(30)

REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_DIR = REPO_ROOT / "examples"
GITHUB_COLLECTION_PATH = EXAMPLES_DIR / "collections" / "github_mcp.json"
GITHUB_ENV_PATH = EXAMPLES_DIR / "environments" / "github.json"
GITHUB_CATALOG_PATH = EXAMPLES_DIR / "collections" / "github_mcp_rest_paths.json"
LIBRARY_MANIFEST_PATH = EXAMPLES_DIR / "pypost-library.yaml"
EXAMPLES_README_PATH = EXAMPLES_DIR / "README.md"

GITHUB_COLLECTION_ID = "github-mcp"
GITHUB_COLLECTION_NAME = "GitHub MCP"
GITHUB_ENVIRONMENT_ID = "github-mcp-environment"
GITHUB_ENVIRONMENT_NAME = "GitHub MCP"
GITHUB_TOOL_COUNT = 30
GITHUB_API_VERSION = "2022-11-28"

PLACEHOLDER_API_URL = "https://api.github.com"
PLACEHOLDER_OWNER = "your-org"
PLACEHOLDER_REPO = "your-repo"
PLACEHOLDER_TOKEN = "your-github-token"
GITHUB_ENV_KEYS = frozenset({"github_api_url", "github_owner", "github_repo", "github_token"})
GITHUB_HIDDEN_KEYS = frozenset({"github_token"})
GITHUB_OVERRIDABLE_KEYS = frozenset({"github_owner", "github_repo"})

GITHUB_ACCEPT = "application/vnd.github+json"
GITHUB_AUTH_HEADER = "Bearer {{ github_token }}"
_OVERRIDE_PROPERTY = {
    "type": "string",
    "description": "Environment variable override (optional).",
}
_INTEGER_OR_STRING_SCHEMA = {
    "anyOf": [
        {"type": "integer"},
        {"type": "string", "pattern": "^[+-]?[0-9]+$"},
    ]
}

# Jinja ``a.b`` tries getattr first, so these names would resolve to dict methods.
_DICT_ATTRIBUTE_NAMES = frozenset(name for name in dir(dict) if not name.startswith("_"))

# GitHub token prefixes: classic PAT ghp_, OAuth gho_, user-to-server ghu_,
# server-to-server ghs_, refresh ghr_, fine-grained PAT github_pat_.
GITHUB_TOKEN_PATTERN = re.compile(
    r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})"
)

_MCP_REQUEST_NAME_PATTERN = re.compile(r"mcp\.request\.([A-Za-z0-9_]+)")
_TEMPLATE_MARKERS = ("{{", "}}", "{%", "%}")


# ---------------------------------------------------------------------------
# Locked tool table (20-architecture.md, Q7). It is the test-side source of
# truth; the shipped catalog and collection must both equal it.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Arg:
    """Expected MCP argument metadata (descriptions are checked separately)."""

    type: str
    required: bool
    default: Any = None


S_REQ = Arg("string", True)
S_OPT = Arg("string", False)
ID_REQ = Arg("integer_or_string", True)
INT_OPT = Arg("integer_or_string", False)
BOOL_OPT = Arg("boolean", False)
ARRAY_OPT = Arg("array", False)
OBJECT_OPT = Arg("object", False)
_PAGINATION = {
    "page": Arg("integer_or_string", False, 1),
    "per_page": Arg("integer_or_string", False, 30),
}
_PAGINATION_KEYS = ("page", "per_page")


@dataclass(frozen=True)
class ToolSpec:
    """One documented GitHub MCP tool."""

    tool: str
    capability: str
    method: str
    path: str
    args: Mapping[str, Arg] = field(default_factory=dict)
    query: tuple[str, ...] = ()
    body_required: tuple[str, ...] = ()
    body_optional: tuple[str, ...] = ()

    @property
    def request_id(self) -> str:
        """Collection request id: the kebab-case form of the tool name."""
        return self.tool.replace("_", "-")

    @property
    def repository_scoped(self) -> bool:
        """Whether the path is under the default ``github_owner``/``github_repo``."""
        return "{{ urlencode(github_owner) }}" in self.path

    @property
    def body_args(self) -> tuple[str, ...]:
        """Required then optional JSON body fields."""
        return self.body_required + self.body_optional

    @property
    def is_write(self) -> bool:
        """Whether the tool sends a JSON body (any non-GET method)."""
        return self.method != "GET"


_R = "/repos/{{ urlencode(github_owner) }}/{{ urlencode(github_repo) }}"
_WORKFLOW = _R + "/actions/workflows/{{ urlencode(mcp.request.workflow_id) }}"
_RUN = _R + "/actions/runs/{{ to_int(mcp.request.run_id) }}"
_PULL = _R + "/pulls/{{ to_int(mcp.request.pull_number) }}"
_PULL_AS_ISSUE = _R + "/issues/{{ to_int(mcp.request.pull_number) }}"
_ISSUE = _R + "/issues/{{ to_int(mcp.request.issue_number) }}"


def _opt(*names: str) -> dict[str, Arg]:
    return {name: S_OPT for name in names}


_RUN_FILTERS = ("branch", "status", "event")

GITHUB_TOOL_SPECS: tuple[ToolSpec, ...] = (
    ToolSpec("github_get_authenticated_user", "Identity", "GET", "/user"),
    ToolSpec("github_get_repository", "Repository: get", "GET", _R),
    ToolSpec(
        "github_list_workflows", "Actions: list workflows", "GET", _R + "/actions/workflows",
        dict(_PAGINATION), _PAGINATION_KEYS,
    ),
    ToolSpec(
        "github_list_workflow_runs", "Actions: list runs (repository)", "GET",
        _R + "/actions/runs",
        {**_opt(*_RUN_FILTERS), **_PAGINATION}, (*_RUN_FILTERS, *_PAGINATION_KEYS),
    ),
    ToolSpec(
        "github_list_workflow_runs_for_workflow", "Actions: list runs (workflow)", "GET",
        _WORKFLOW + "/runs",
        {"workflow_id": S_REQ, **_opt(*_RUN_FILTERS), **_PAGINATION},
        (*_RUN_FILTERS, *_PAGINATION_KEYS),
    ),
    ToolSpec("github_get_workflow_run", "Actions: get run", "GET", _RUN, {"run_id": ID_REQ}),
    ToolSpec(
        "github_rerun_workflow_run", "Actions: re-run run", "POST", _RUN + "/rerun",
        {"run_id": ID_REQ, "enable_debug_logging": BOOL_OPT},
        body_optional=("enable_debug_logging",),
    ),
    ToolSpec(
        "github_cancel_workflow_run", "Actions: cancel run", "POST", _RUN + "/cancel",
        {"run_id": ID_REQ},
    ),
    ToolSpec(
        "github_list_workflow_run_jobs", "Actions: list jobs", "GET", _RUN + "/jobs",
        {"run_id": ID_REQ, **_opt("filter"), **_PAGINATION}, ("filter", *_PAGINATION_KEYS),
    ),
    ToolSpec(
        "github_get_workflow_job", "Actions: get job", "GET",
        _R + "/actions/jobs/{{ to_int(mcp.request.job_id) }}", {"job_id": ID_REQ},
    ),
    ToolSpec(
        "github_dispatch_workflow", "Actions: dispatch", "POST", _WORKFLOW + "/dispatches",
        {"workflow_id": S_REQ, "ref": S_REQ, "inputs": OBJECT_OPT},
        body_required=("ref",), body_optional=("inputs",),
    ),
    ToolSpec(
        "github_list_pull_requests", "PRs: list", "GET", _R + "/pulls",
        {**_opt("state", "head", "base"), **_PAGINATION},
        ("state", "head", "base", *_PAGINATION_KEYS),
    ),
    ToolSpec("github_get_pull_request", "PRs: get", "GET", _PULL, {"pull_number": ID_REQ}),
    ToolSpec(
        "github_create_pull_request", "PRs: create", "POST", _R + "/pulls",
        {"title": S_REQ, "head": S_REQ, "base": S_REQ, "body": S_OPT, "draft": BOOL_OPT},
        body_required=("title", "head", "base"), body_optional=("body", "draft"),
    ),
    ToolSpec(
        "github_update_pull_request", "PRs: update/close/reopen", "PATCH", _PULL,
        {"pull_number": ID_REQ, **_opt("title", "body", "state", "base")},
        body_optional=("title", "body", "state", "base"),
    ),
    ToolSpec(
        "github_list_pull_request_files", "PR contents: files", "GET", _PULL + "/files",
        {"pull_number": ID_REQ, **_PAGINATION}, _PAGINATION_KEYS,
    ),
    ToolSpec(
        "github_list_pull_request_commits", "PR contents: commits", "GET", _PULL + "/commits",
        {"pull_number": ID_REQ, **_PAGINATION}, _PAGINATION_KEYS,
    ),
    ToolSpec(
        "github_list_pull_request_review_comments", "PR discussion: list review comments",
        "GET", _PULL + "/comments",
        {"pull_number": ID_REQ, **_PAGINATION}, _PAGINATION_KEYS,
    ),
    ToolSpec(
        "github_create_pull_request_review_comment", "PR discussion: create review comment",
        "POST", _PULL + "/comments",
        {
            "pull_number": ID_REQ, "body": S_REQ, "commit_id": S_REQ, "path": S_REQ,
            "line": INT_OPT, "side": S_OPT, "start_line": INT_OPT, "start_side": S_OPT,
            "subject_type": S_OPT,
        },
        body_required=("body", "commit_id", "path"),
        body_optional=("line", "side", "start_line", "start_side", "subject_type"),
    ),
    ToolSpec(
        "github_reply_to_pull_request_review_comment",
        "PR discussion: reply to review comment", "POST",
        _PULL + "/comments/{{ to_int(mcp.request.comment_id) }}/replies",
        {"pull_number": ID_REQ, "comment_id": ID_REQ, "body": S_REQ},
        body_required=("body",),
    ),
    ToolSpec(
        "github_list_pull_request_comments", "PR discussion: list conversation comments",
        "GET", _PULL_AS_ISSUE + "/comments",
        {"pull_number": ID_REQ, **_PAGINATION}, _PAGINATION_KEYS,
    ),
    ToolSpec(
        "github_create_pull_request_comment", "PR discussion: create conversation comment",
        "POST", _PULL_AS_ISSUE + "/comments",
        {"pull_number": ID_REQ, "body": S_REQ}, body_required=("body",),
    ),
    ToolSpec(
        "github_list_pull_request_reviews", "PR reviews: list", "GET", _PULL + "/reviews",
        {"pull_number": ID_REQ, **_PAGINATION}, _PAGINATION_KEYS,
    ),
    ToolSpec(
        "github_create_pull_request_review", "PR reviews: create (submitted only)", "POST",
        _PULL + "/reviews",
        {"pull_number": ID_REQ, "event": S_REQ, "body": S_OPT, "commit_id": S_OPT},
        body_required=("event",), body_optional=("body", "commit_id"),
    ),
    ToolSpec(
        "github_list_issues", "Issues: list", "GET", _R + "/issues",
        {**_opt("state", "labels", "assignee", "creator"), **_PAGINATION},
        ("state", "labels", "assignee", "creator", *_PAGINATION_KEYS),
    ),
    ToolSpec("github_get_issue", "Issues: get", "GET", _ISSUE, {"issue_number": ID_REQ}),
    ToolSpec(
        "github_create_issue", "Issues: create", "POST", _R + "/issues",
        {"title": S_REQ, "body": S_OPT, "labels": ARRAY_OPT, "assignees": ARRAY_OPT},
        body_required=("title",), body_optional=("body", "labels", "assignees"),
    ),
    ToolSpec(
        "github_update_issue", "Issues: update/close/reopen", "PATCH", _ISSUE,
        {
            "issue_number": ID_REQ, **_opt("title", "body", "state", "state_reason"),
            "labels": ARRAY_OPT, "assignees": ARRAY_OPT,
        },
        body_optional=("title", "body", "state", "state_reason", "labels", "assignees"),
    ),
    ToolSpec(
        "github_list_issue_comments", "Issue comments: list", "GET", _ISSUE + "/comments",
        {"issue_number": ID_REQ, **_PAGINATION}, _PAGINATION_KEYS,
    ),
    ToolSpec(
        "github_create_issue_comment", "Issue comments: create", "POST", _ISSUE + "/comments",
        {"issue_number": ID_REQ, "body": S_REQ}, body_required=("body",),
    ),
)
SPECS_BY_TOOL: dict[str, ToolSpec] = {spec.tool: spec for spec in GITHUB_TOOL_SPECS}
EXPECTED_GITHUB_TOOLS = frozenset(SPECS_BY_TOOL)
assert len(GITHUB_TOOL_SPECS) == len(EXPECTED_GITHUB_TOOLS) == GITHUB_TOOL_COUNT

# (tool, argument) pairs whose argument is a numeric path identifier.
GITHUB_NUMERIC_PATH_IDS: frozenset[tuple[str, str]] = frozenset(
    (spec.tool, name)
    for spec in GITHUB_TOOL_SPECS
    for name, arg in spec.args.items()
    if arg.type == "integer_or_string" and f"to_int(mcp.request.{name})" in spec.path
)
# (tool, argument) pairs whose argument is an integer JSON body field.
GITHUB_NUMERIC_BODY_FIELDS: frozenset[tuple[str, str]] = frozenset(
    (spec.tool, name)
    for spec in GITHUB_TOOL_SPECS
    for name in spec.body_args
    if spec.args[name].type == "integer_or_string"
)

# Sample values per argument; quotes/backslashes prove JSON escaping in bodies.
_SAMPLE_VALUES: dict[str, Any] = {
    "pull_number": 7,
    "issue_number": "42",
    "run_id": 30433642,
    "job_id": "399444496",
    "comment_id": 99,
    "page": 2,
    "per_page": "50",
    "line": "12",
    "start_line": 10,
    "workflow_id": "ci.yml",
    "ref": "main",
    "event": "COMMENT",
    "state": "open",
    "state_reason": "completed",
    "filter": "latest",
    "head": "octo:feature/x",
    "base": "main",
    "side": "RIGHT",
    "start_side": "RIGHT",
    "subject_type": "line",
    "commit_id": "6dcb09b5b57875f334f61aebed695e2e4193db5e",
    "path": "src/app/main.py",
    "title": 'Fix "quoted" title \\ with backslash',
    "body": 'Line one\nLooks "good" & done',
}
# Typed samples (array/object/boolean args); a query ``labels`` stays a string.
_ARRAY_SAMPLES: dict[str, list[str]] = {
    "labels": ["bug", 'needs "triage"'],
    "assignees": ["octocat"],
}
_OBJECT_SAMPLES: dict[str, dict[str, Any]] = {
    "inputs": {"env": "prod", "dry_run": True, "count": 3},
}
_BOOLEAN_SAMPLES: dict[str, bool] = {"draft": True, "enable_debug_logging": False}
_STRING_SAMPLES_BY_NAME: dict[str, str] = {"labels": "bug,help wanted"}

OFFLINE_ENV: dict[str, str] = {
    "github_api_url": "https://api.github.example.test",
    "github_owner": "octo-org",
    "github_repo": "hello-world",
    "github_token": "offline-placeholder-token",
}
_OFFLINE_REPO_PREFIX = "https://api.github.example.test/repos/octo-org/hello-world"


def _sample(name: str, arg: Arg) -> Any:
    if arg.type == "array":
        return list(_ARRAY_SAMPLES[name])
    if arg.type == "object":
        return dict(_OBJECT_SAMPLES[name])
    if arg.type == "boolean":
        return _BOOLEAN_SAMPLES[name]
    if name in _STRING_SAMPLES_BY_NAME:
        return _STRING_SAMPLES_BY_NAME[name]
    return _SAMPLE_VALUES.get(name, f"sample-{name.replace('_', '-')}")


def _full_args(spec: ToolSpec) -> dict[str, Any]:
    return {name: _sample(name, arg) for name, arg in spec.args.items()}


def _required_args(spec: ToolSpec) -> dict[str, Any]:
    return {name: _sample(name, arg) for name, arg in spec.args.items() if arg.required}


def _expected_body_value(arg: Arg, value: Any) -> Any:
    """JSON value GitHub must receive for one MCP argument value."""
    if arg.type == "integer_or_string":
        return int(value)
    if arg.type == "boolean":
        return value
    if arg.type == "array":
        return [str(item) for item in value]
    if arg.type == "object":
        return {
            str(key): ("true" if item is True else "false" if item is False else str(item))
            for key, item in value.items()
        }
    return value


# ---------------------------------------------------------------------------
# Guarded loaders — every missing artifact becomes a named assertion.
# ---------------------------------------------------------------------------


def _require_file(path: Path) -> None:
    assert path.is_file(), f"{path.relative_to(REPO_ROOT)} missing (PYPOST-1334)"


def _load_github_collection() -> Collection:
    _require_file(GITHUB_COLLECTION_PATH)
    collections, parse_errors = load_collection_import_candidates(GITHUB_COLLECTION_PATH)
    assert parse_errors == [], f"github_mcp.json parse errors: {parse_errors}"
    assert len(collections) == 1
    collection = collections[0]
    assert collection.id == GITHUB_COLLECTION_ID
    return collection


def _load_github_environment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Environment:
    _require_file(GITHUB_ENV_PATH)
    monkeypatch.delenv("PYPOST_ENV_ENCRYPTION_ENABLED", raising=False)
    monkeypatch.delenv("PYPOST_ENV_ENCRYPTION_KEY", raising=False)
    storage = StorageManager(data_dir=tmp_path / "pypost-data")
    environments, parse_errors = load_import_candidates(GITHUB_ENV_PATH, storage)
    assert parse_errors == [], f"github.json parse errors: {parse_errors}"
    assert len(environments) == 1
    return environments[0]


def _load_github_catalog() -> dict[str, Any]:
    _require_file(GITHUB_CATALOG_PATH)
    payload = json.loads(GITHUB_CATALOG_PATH.read_text(encoding="utf-8"))
    assert isinstance(payload, dict), "github_mcp_rest_paths.json must be a JSON object"
    for key in ("version", "description", "reviewed_on", "api_version"):
        assert payload.get(key), f"github_mcp_rest_paths.json missing {key!r}"
    doc_refs = payload.get("doc_refs")
    assert isinstance(doc_refs, list) and doc_refs, "doc_refs must be a non-empty list"
    tools = payload.get("tools")
    assert isinstance(tools, list) and tools, "tools must be a non-empty list"
    return payload


def _load_manifest() -> LibraryManifest:
    manifest, _ = find_and_read_manifest(EXAMPLES_DIR)
    return manifest


def _requests_by_tool(collection: Collection) -> dict[str, RequestData]:
    return {normalize_mcp_tool_name(request.name): request for request in collection.requests}


def _request_for(collection: Collection, tool: str) -> RequestData:
    by_tool = _requests_by_tool(collection)
    assert tool in by_tool, f"github_mcp.json has no request publishing tool {tool}"
    return by_tool[tool]


def _execution_variables(
    request: RequestData,
    args: Mapping[str, Any],
    env: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Build call variables exactly like ``MCPServerImpl`` (defaults + overrides)."""
    impl = MCPServerImpl(template_service=TemplateService())
    return impl._build_execution_variables(
        dict(args),
        dict(env if env is not None else OFFLINE_ENV),
        set(GITHUB_HIDDEN_KEYS),
        set(GITHUB_OVERRIDABLE_KEYS),
        request_data=request,
    )


def _render(content: str, variables: Mapping[str, Any]) -> str:
    return TemplateService().render_string_strict_conversion(content, dict(variables), "mcp")


def _prepare(request: RequestData, variables: Mapping[str, Any]) -> dict[str, Any]:
    kwargs, _ = HTTPClient()._prepare_request_kwargs(request, dict(variables))
    return kwargs


def _render_body_json(request: RequestData, args: Mapping[str, Any], label: str) -> Any:
    rendered = _render(request.body, _execution_variables(request, args))
    try:
        return json.loads(rendered)
    except json.JSONDecodeError as exc:
        raise AssertionError(
            f"{normalize_mcp_tool_name(request.name)} [{label}] body is not valid JSON: "
            f"{rendered!r}"
        ) from exc


# ---------------------------------------------------------------------------
# Shared checkers (each one has a synthetic mutation twin below).
# ---------------------------------------------------------------------------


def _template_fields(request: RequestData) -> list[str]:
    fields = [request.url, request.body, *request.headers.values(), *request.params.values()]
    return [content for content in fields if content]


def assert_github_auth_convention(
    requests_: Sequence[RequestData], api_version: str = GITHUB_API_VERSION
) -> None:
    """Every request sends Bearer auth, the GitHub media type and the pinned version."""
    for request in requests_:
        auth = request.headers.get("Authorization")
        assert auth == GITHUB_AUTH_HEADER, (
            f"Request {request.id} auth convention breach: expected "
            f"{GITHUB_AUTH_HEADER!r}, got {auth!r}"
        )
        accept = request.headers.get("Accept")
        assert accept == GITHUB_ACCEPT, (
            f"Request {request.id} Accept must be {GITHUB_ACCEPT!r}, got {accept!r}"
        )
        version = request.headers.get("X-GitHub-Api-Version")
        assert version == api_version, (
            f"Request {request.id} X-GitHub-Api-Version must be {api_version!r}, got {version!r}"
        )
        token_headers = sorted(
            name
            for name, value in request.headers.items()
            if name != "Authorization" and "github_token" in value
        )
        assert not token_headers, f"Request {request.id} leaks the token in {token_headers}"
        token_params = sorted(
            name
            for name, value in request.params.items()
            if "token" in name.lower() or "github_token" in value
        )
        assert not token_params, f"Request {request.id} has token query param(s) {token_params}"
        assert "github_token" not in request.url, f"Request {request.id} puts the token in the URL"
        assert "github_token" not in (request.body or ""), (
            f"Request {request.id} puts the token in the body"
        )


def assert_github_mcp_params_declared_and_used(request: RequestData) -> None:
    """Every ``mcp.request.X`` is declared and every declared param is referenced."""
    referenced: set[str] = set()
    for content in _template_fields(request):
        referenced.update(_MCP_REQUEST_NAME_PATTERN.findall(content))
    declared = set(request.mcp_params)
    dangling = sorted(referenced - declared)
    dead = sorted(declared - referenced)
    assert not dangling, f"Request {request.id} undeclared mcp.request name(s): {dangling}"
    assert not dead, f"Request {request.id} declared but unused mcp_params: {dead}"


def assert_github_catalog_matches_collection(
    collection_requests: Sequence[RequestData], catalog_tools: Sequence[Mapping[str, Any]]
) -> None:
    """Request ids, tool names, methods and paths equal the locked catalog exactly."""
    by_id = {request.id: request for request in collection_requests}
    catalog_ids = {entry["id"] for entry in catalog_tools}
    missing = sorted(catalog_ids - set(by_id))
    extra = sorted(set(by_id) - catalog_ids)
    assert not missing, f"github_mcp.json missing catalog request id(s): {missing}"
    assert not extra, f"github_mcp.json has request id(s) not in the catalog: {extra}"
    for entry in catalog_tools:
        request = by_id[entry["id"]]
        tool = normalize_mcp_tool_name(request.name)
        assert tool == entry["tool"], (
            f"{entry['id']} publishes {tool!r}, catalog locks {entry['tool']!r}"
        )
        assert request.method.upper() == entry["method"], (
            f"{entry['tool']} method drifted: expected {entry['method']}, got {request.method}"
        )
        expected_url = "{{ github_api_url }}" + entry["path"]
        assert request.url == expected_url, (
            f"{entry['tool']} path drifted: expected {expected_url!r}, got {request.url!r}"
        )


def assert_query_single_keys_on_wire(
    prepared_url: str, expected_path: str, expected_query: Mapping[str, list[str]]
) -> None:
    """Reserved characters in query values must not split keys or cut a fragment."""
    parts = urlsplit(prepared_url)
    assert parts.fragment == "", f"query value leaked a fragment: {parts.fragment!r}"
    assert parts.path == expected_path, f"path changed on the wire: {parts.path!r}"
    parsed = parse_qs(parts.query, keep_blank_values=True)
    assert parsed == dict(expected_query), (
        f"query keys/values altered on the wire: {parsed!r} != {dict(expected_query)!r}"
    )


def find_github_token_like_values(text: str) -> list[str]:
    """Return every substring that looks like a real GitHub token."""
    return GITHUB_TOKEN_PATTERN.findall(text)


def _readme_section(readme: str, heading: str) -> str:
    marker = f"## {heading}\n"
    assert marker in readme, f"examples/README.md missing GitHub section '## {heading}'"
    start = readme.index(marker) + len(marker)
    next_heading = re.search(r"^## ", readme[start:], flags=re.MULTILINE)
    end = start + next_heading.start() if next_heading else len(readme)
    return readme[start:end]


def _expected_headers(spec: ToolSpec) -> dict[str, str]:
    headers = {
        "Accept": GITHUB_ACCEPT,
        "X-GitHub-Api-Version": GITHUB_API_VERSION,
        "Authorization": GITHUB_AUTH_HEADER,
    }
    if spec.method in {"POST", "PATCH"}:
        headers["Content-Type"] = "application/json"
    return headers


def _expected_query(spec: ToolSpec) -> dict[str, str]:
    return {
        name: (
            f"{{{{ to_int(mcp.request.{name}) }}}}"
            if name in _PAGINATION
            else f"{{{{ mcp.request.{name} }}}}"
        )
        for name in spec.query
    }


def _synthetic_request(spec: ToolSpec) -> RequestData:
    """Build an in-memory request that satisfies ``spec`` (for checker twins)."""
    body = ""
    if spec.is_write:
        body = "{" + ", ".join(
            f'"{name}": {{{{ to_json_string(mcp.request.{name}) }}}}' for name in spec.body_args
        ) + "}"
    return RequestData(
        id=spec.request_id,
        name=spec.tool,
        method=spec.method,
        url="{{ github_api_url }}" + spec.path,
        headers=_expected_headers(spec),
        params=_expected_query(spec),
        body=body,
        expose_as_mcp=True,
        mcp_description=f"Synthetic {spec.tool}",
        mcp_params={
            name: McpToolParam(
                type=arg.type, description=name, required=arg.required, default=arg.default
            )
            for name, arg in spec.args.items()
        },
    )


def _catalog_entry(spec: ToolSpec) -> dict[str, str]:
    return {
        "id": spec.request_id,
        "tool": spec.tool,
        "capability": spec.capability,
        "method": spec.method,
        "path": spec.path,
    }


# ---------------------------------------------------------------------------
# 1. Format and load
# ---------------------------------------------------------------------------


def test_github_mcp_collection_imports_via_native_loader():
    collection = _load_github_collection()
    assert collection.name == GITHUB_COLLECTION_NAME
    assert collection.version == "1.0.0"
    assert str(GITHUB_TOOL_COUNT) in collection.description
    assert "GitHub Enterprise Server" in collection.description
    assert len(collection.requests) == GITHUB_TOOL_COUNT

    for request in collection.requests:
        assert request.expose_as_mcp is True, f"{request.id} not exposed via MCP"
        assert request.mcp_description.strip(), f"{request.id} has an empty mcp_description"
        assert request.body_type == "json", f"{request.id} body_type must be json"
        assert request.retry_policy is None, f"{request.id} must not set a retry_policy"

    variables = {variable.name: variable for variable in collection.variables}
    assert set(variables) == GITHUB_ENV_KEYS
    assert variables["github_token"].secret is True
    assert variables["github_token"].required is True
    assert variables["github_token"].default == ""
    for name in ("github_api_url", "github_owner", "github_repo"):
        assert variables[name].secret is False, f"{name} must not be secret"


def test_github_environment_imports_with_placeholders(tmp_path, monkeypatch):
    environment = _load_github_environment(tmp_path, monkeypatch)
    assert environment.id == GITHUB_ENVIRONMENT_ID
    assert environment.name == GITHUB_ENVIRONMENT_NAME
    assert environment.variables == {
        "github_api_url": PLACEHOLDER_API_URL,
        "github_owner": PLACEHOLDER_OWNER,
        "github_repo": PLACEHOLDER_REPO,
        "github_token": PLACEHOLDER_TOKEN,
    }
    assert environment.hidden_keys == set(GITHUB_HIDDEN_KEYS)
    assert environment.mcp_overridable_keys == set(GITHUB_OVERRIDABLE_KEYS)
    assert "github_token" not in environment.mcp_overridable_keys
    assert environment.enable_mcp is True


# ---------------------------------------------------------------------------
# 2. Tool publication and exact schemas
# ---------------------------------------------------------------------------


def _expected_schema(spec: ToolSpec) -> dict[str, Any]:
    properties: dict[str, Any] = {}
    for name, arg in spec.args.items():
        prop: dict[str, Any] = (
            json.loads(json.dumps(_INTEGER_OR_STRING_SCHEMA))
            if arg.type == "integer_or_string"
            else {"type": arg.type}
        )
        if arg.default is not None:
            prop["default"] = arg.default
        properties[name] = prop
    if spec.repository_scoped:
        for key in sorted(GITHUB_OVERRIDABLE_KEYS):
            properties[key] = dict(_OVERRIDE_PROPERTY)
    return {
        "type": "object",
        "properties": properties,
        "required": sorted(name for name, arg in spec.args.items() if arg.required),
    }


def _schema_without_arg_descriptions(tool: str, schema: dict[str, Any]) -> dict[str, Any]:
    properties: dict[str, Any] = {}
    for name, prop in schema.get("properties", {}).items():
        prop = dict(prop)
        if name not in GITHUB_OVERRIDABLE_KEYS:
            description = prop.pop("description", "")
            assert description.strip(), f"{tool}.{name} has no agent-facing description"
        properties[name] = prop
    return {
        "type": schema.get("type"),
        "properties": properties,
        "required": sorted(schema.get("required", [])),
    }


def test_github_mcp_published_tools_match_documented_set():
    collection = _load_github_collection()
    impl = MCPServerImpl(
        template_service=TemplateService(),
        variable_supplier=lambda: dict(OFFLINE_ENV),
        hidden_keys_supplier=lambda: set(GITHUB_HIDDEN_KEYS),
        overridable_keys_supplier=lambda: set(GITHUB_OVERRIDABLE_KEYS),
    )
    impl.register_tools(collection.requests)

    published = set(impl.tools_map)
    assert published == EXPECTED_GITHUB_TOOLS, (
        f"missing tools {sorted(EXPECTED_GITHUB_TOOLS - published)}, "
        f"undocumented tools {sorted(published - EXPECTED_GITHUB_TOOLS)}"
    )
    assert len(collection.requests) == len(published), "tool names must be unique"
    for name in published:
        assert len(name) <= 64
        assert re.fullmatch(r"github_[a-z_]+", name), name

    for tool, request in impl.tools_map.items():
        assert isinstance(request, RequestData)
        spec = SPECS_BY_TOOL[tool]
        assert request.id == spec.request_id, f"{tool} request id must be {spec.request_id}"
        schema = impl._generate_schema(request)
        properties = schema.get("properties", {})
        assert "github_token" not in properties, f"{tool} publishes the token"
        assert "github_api_url" not in properties, f"{tool} publishes github_api_url"
        actual = _schema_without_arg_descriptions(tool, schema)
        assert actual == _expected_schema(spec), f"{tool} schema drifted"

    review = impl._generate_schema(impl.tools_map["github_create_pull_request_review"])
    assert sorted(review["required"]) == ["event", "pull_number"]
    assert review["properties"]["event"]["type"] == "string"


def test_github_create_pull_request_review_documents_event_and_pending_gap():
    collection = _load_github_collection()
    request = _request_for(collection, "github_create_pull_request_review")
    for text in (request.mcp_description, request.mcp_params["event"].description):
        for value in ("APPROVE", "REQUEST_CHANGES", "COMMENT"):
            assert value in text, f"review create description lacks {value!r}: {text!r}"
    assert "pending" in request.mcp_description.lower(), (
        "github_create_pull_request_review must say pending reviews are not supported"
    )


# ---------------------------------------------------------------------------
# 3. HTTP contracts (method, path, query, body)
# ---------------------------------------------------------------------------


def test_github_mcp_http_contracts_match_locked_catalog():
    catalog = _load_github_catalog()
    assert catalog["api_version"] == GITHUB_API_VERSION, (
        f"github_mcp_rest_paths.json api_version must be {GITHUB_API_VERSION}"
    )
    expected_entries = sorted(
        (_catalog_entry(spec) for spec in GITHUB_TOOL_SPECS), key=lambda entry: entry["id"]
    )
    actual_entries = sorted(
        (
            {key: entry.get(key) for key in ("id", "tool", "capability", "method", "path")}
            for entry in catalog["tools"]
        ),
        key=lambda entry: str(entry["id"]),
    )
    assert actual_entries == expected_entries, "github_mcp_rest_paths.json drifted from design"

    collection = _load_github_collection()
    assert_github_catalog_matches_collection(collection.requests, catalog["tools"])


def test_github_mcp_catalog_check_rejects_path_drift():
    """Mutation twin (green by design): the catalog checker flags a drifted path."""
    requests_ = [_synthetic_request(spec) for spec in GITHUB_TOOL_SPECS]
    catalog_tools = [_catalog_entry(spec) for spec in GITHUB_TOOL_SPECS]
    assert_github_catalog_matches_collection(requests_, catalog_tools)

    drifted = next(
        request
        for request in requests_
        if request.id == "github-reply-to-pull-request-review-comment"
    )
    observed = drifted.url.replace("/replies", "")
    drifted.url = observed
    with pytest.raises(AssertionError) as excinfo:
        assert_github_catalog_matches_collection(requests_, catalog_tools)
    message = str(excinfo.value)
    assert "github_reply_to_pull_request_review_comment" in message
    assert observed in message

    method_drift = [_synthetic_request(spec) for spec in GITHUB_TOOL_SPECS]
    patched = next(request for request in method_drift if request.id == "github-update-issue")
    patched.method = "PUT"
    with pytest.raises(AssertionError, match=r"github_update_issue method drifted"):
        assert_github_catalog_matches_collection(method_drift, catalog_tools)


_GITHUB_PATH_FRESHNESS_TARGET = "check-github-mcp-path-freshness"
_GITHUB_PATH_FRESHNESS_NODES = (
    "tests/test_github_mcp_collection.py::test_github_mcp_http_contracts_match_locked_catalog",
    "tests/test_github_mcp_collection.py::test_github_mcp_catalog_check_rejects_path_drift",
)


def _makefile_phony_targets(text: str) -> set[str]:
    """Return every target named in the (possibly backslash-continued) .PHONY lines."""
    joined = text.replace("\\\n", " ")
    targets: set[str] = set()
    for line in joined.splitlines():
        if line.startswith(".PHONY:"):
            targets.update(line.removeprefix(".PHONY:").split())
    return targets


def test_github_makefile_path_freshness_target_declared():
    """Design Q8: offline path-freshness gate mirroring check-gitlab-mcp-path-freshness."""
    makefile_path = REPO_ROOT / "Makefile"
    assert makefile_path.is_file(), f"{makefile_path} missing"
    text = makefile_path.read_text(encoding="utf-8")
    target = _GITHUB_PATH_FRESHNESS_TARGET

    assert target in _makefile_phony_targets(text), (
        f"Makefile .PHONY does not declare {target} (PYPOST-1334)"
    )

    lines = text.splitlines()
    header_index = next(
        (index for index, line in enumerate(lines) if line.startswith(f"{target}:")), None
    )
    assert header_index is not None, f"Makefile has no '{target}:' rule (PYPOST-1334)"
    header = lines[header_index]
    prerequisites, _, help_text = header.removeprefix(f"{target}:").partition("##")
    assert prerequisites.split() == ["$(VENV_MARKER)", "venv-test", "venv-otel"], (
        f"{target} must depend on $(VENV_MARKER) venv-test venv-otel: {prerequisites!r}"
    )
    assert help_text.strip(), f"{target} needs a '## <help text>' comment"

    recipe_lines: list[str] = []
    for line in lines[header_index + 1:]:
        if not line.startswith("\t"):
            break
        recipe_lines.append(line.strip().removesuffix("\\").strip())
    tokens = " ".join(recipe_lines).split()
    assert tokens[:4] == ["QT_QPA_PLATFORM=offscreen", "$(BIN)/python", "-m", "pytest"], (
        f"{target} recipe must run 'QT_QPA_PLATFORM=offscreen $(BIN)/python -m pytest': {tokens}"
    )
    assert tokens[4:] == [*_GITHUB_PATH_FRESHNESS_NODES, "-q"], (
        f"{target} recipe must select exactly the catalog freshness nodes with -q: {tokens}"
    )


def test_github_mcp_query_params_match_documented_set():
    collection = _load_github_collection()
    for spec in GITHUB_TOOL_SPECS:
        request = _request_for(collection, spec.tool)
        assert request.params == _expected_query(spec), f"{spec.tool} query params drifted"
        for value in request.params.values():
            assert "urlencode(" not in value, f"{spec.tool} double-encodes a query value"


def _body_subsets(spec: ToolSpec) -> list[tuple[str, dict[str, Any]]]:
    required = _required_args(spec)
    subsets = [("all", _full_args(spec)), ("minimal", required)]
    subsets.extend(
        (f"only-{name}", {**required, name: _sample(name, spec.args[name])})
        for name in spec.body_optional
    )
    return subsets


def test_github_mcp_bodies_render_documented_json_fields():
    collection = _load_github_collection()
    write_specs = [spec for spec in GITHUB_TOOL_SPECS if spec.is_write]
    assert len(write_specs) == 12
    for spec in write_specs:
        request = _request_for(collection, spec.tool)
        for label, args in _body_subsets(spec):
            payload = _render_body_json(request, args, label)
            expected = {
                name: _expected_body_value(spec.args[name], args[name])
                for name in spec.body_args
                if name in args
            }
            assert payload == expected, f"{spec.tool} [{label}] body drifted: {payload!r}"


def test_github_mcp_body_value_types_are_native_json():
    collection = _load_github_collection()
    checks = (
        ("github_create_pull_request_review_comment", "line", int),
        ("github_create_pull_request_review_comment", "start_line", int),
        ("github_create_pull_request", "draft", bool),
        ("github_rerun_workflow_run", "enable_debug_logging", bool),
        ("github_create_issue", "labels", list),
        ("github_create_issue", "assignees", list),
        ("github_update_issue", "labels", list),
        ("github_update_issue", "assignees", list),
        ("github_dispatch_workflow", "inputs", dict),
    )
    for tool, name, expected_type in checks:
        spec = SPECS_BY_TOOL[tool]
        request = _request_for(collection, tool)
        payload = _render_body_json(request, _full_args(spec), "all")
        assert isinstance(payload.get(name), expected_type), (
            f"{tool}.{name} must be a JSON {expected_type.__name__}: {payload.get(name)!r}"
        )
    dispatch = _render_body_json(
        _request_for(collection, "github_dispatch_workflow"),
        _full_args(SPECS_BY_TOOL["github_dispatch_workflow"]),
        "all",
    )
    assert all(isinstance(value, str) for value in dispatch["inputs"].values()), (
        f"dispatch inputs must be sent as strings: {dispatch['inputs']!r}"
    )
    empty_labels = _render_body_json(
        _request_for(collection, "github_update_issue"),
        {"issue_number": 1, "labels": []},
        "empty-labels",
    )
    assert empty_labels == {"labels": []}, f"empty labels must clear: {empty_labels!r}"


def test_github_create_pull_request_review_body_always_carries_event():
    collection = _load_github_collection()
    spec = SPECS_BY_TOOL["github_create_pull_request_review"]
    request = _request_for(collection, spec.tool)
    minimal = _render_body_json(request, _required_args(spec), "minimal")
    assert minimal == {"event": _SAMPLE_VALUES["event"]}, f"minimal review body: {minimal!r}"
    for label, args in _body_subsets(spec):
        payload = _render_body_json(request, args, label)
        assert payload.get("event") == args["event"], (
            f"review body [{label}] lacks event (would create a PENDING review): {payload!r}"
        )


def test_github_cancel_and_rerun_send_json_object_bodies():
    collection = _load_github_collection()
    cancel = _request_for(collection, "github_cancel_workflow_run")
    assert json.loads(cancel.body) == {}, "cancel must send the static body '{}'"
    rerun = _request_for(collection, "github_rerun_workflow_run")
    assert _render_body_json(rerun, {"run_id": 1}, "no-debug") == {}


# ---------------------------------------------------------------------------
# 4. Headers and auth convention
# ---------------------------------------------------------------------------


def test_github_mcp_requests_send_github_headers():
    catalog = _load_github_catalog()
    collection = _load_github_collection()
    assert_github_auth_convention(collection.requests, catalog["api_version"])
    for spec in GITHUB_TOOL_SPECS:
        request = _request_for(collection, spec.tool)
        expected = _expected_headers(spec)
        expected["X-GitHub-Api-Version"] = catalog["api_version"]
        assert request.headers == expected, f"{spec.tool} headers drifted: {request.headers!r}"
        if spec.is_write:
            assert request.body.strip(), f"write tool {spec.tool} must send a JSON body"
        else:
            assert request.body == "", f"read tool {spec.tool} must not send a body"


def test_github_mcp_auth_convention_rejects_token_scheme_and_missing_version():
    """Mutation twin (green by design): the header checker rejects other conventions."""
    request = _synthetic_request(SPECS_BY_TOOL["github_get_repository"])
    assert_github_auth_convention([request])

    token_scheme = request.model_copy(deep=True)
    token_scheme.headers["Authorization"] = "token {{ github_token }}"
    with pytest.raises(AssertionError, match=r"github-get-repository auth convention"):
        assert_github_auth_convention([token_scheme])

    missing_version = request.model_copy(deep=True)
    del missing_version.headers["X-GitHub-Api-Version"]
    with pytest.raises(AssertionError, match=r"X-GitHub-Api-Version"):
        assert_github_auth_convention([missing_version])

    other_version = request.model_copy(deep=True)
    other_version.headers["X-GitHub-Api-Version"] = "2026-03-10"
    with pytest.raises(AssertionError, match=r"X-GitHub-Api-Version"):
        assert_github_auth_convention([other_version])

    wrong_accept = request.model_copy(deep=True)
    wrong_accept.headers["Accept"] = "application/json"
    with pytest.raises(AssertionError, match=r"Accept"):
        assert_github_auth_convention([wrong_accept])

    query_token = request.model_copy(deep=True)
    query_token.params["access_token"] = "{{ github_token }}"
    with pytest.raises(AssertionError, match=r"access_token"):
        assert_github_auth_convention([query_token])


# ---------------------------------------------------------------------------
# 5. Placeholder integrity
# ---------------------------------------------------------------------------


def test_github_mcp_params_declared_and_used():
    collection = _load_github_collection()
    for request in collection.requests:
        assert_github_mcp_params_declared_and_used(request)


def test_github_mcp_params_checker_rejects_dangling_and_dead_arguments():
    """Mutation twin (green by design): both directions of the check can fail."""
    request = _synthetic_request(SPECS_BY_TOOL["github_get_workflow_run"])
    assert_github_mcp_params_declared_and_used(request)

    dangling = request.model_copy(deep=True)
    del dangling.mcp_params["run_id"]
    with pytest.raises(AssertionError, match=r"github-get-workflow-run.*undeclared.*run_id"):
        assert_github_mcp_params_declared_and_used(dangling)

    dead = request.model_copy(deep=True)
    dead.mcp_params["unused_arg"] = McpToolParam(type="string", description="x", required=False)
    with pytest.raises(AssertionError, match=r"github-get-workflow-run.*unused.*unused_arg"):
        assert_github_mcp_params_declared_and_used(dead)


def test_github_mcp_companion_env_covers_referenced_names(tmp_path, monkeypatch):
    collection = _load_github_collection()
    environment = _load_github_environment(tmp_path, monkeypatch)
    template_service = TemplateService()
    referenced: set[str] = set()
    for request in collection.requests:
        referenced.update(
            McpSecretsPolicy.extract_environment_variable_names(request, template_service)
        )
    assert referenced == set(GITHUB_ENV_KEYS), f"env references drifted: {sorted(referenced)}"
    missing = referenced - set(environment.variables)
    assert not missing, f"Missing companion key(s): {sorted(missing)}"


def test_github_mcp_argument_names_do_not_shadow_dict_attributes():
    collection = _load_github_collection()
    for request in collection.requests:
        shadowing = sorted(set(request.mcp_params) & _DICT_ATTRIBUTE_NAMES)
        assert not shadowing, f"{request.id} argument(s) shadow dict attributes: {shadowing}"


def test_github_mcp_full_render_leaves_no_template_markers():
    collection = _load_github_collection()
    for spec in GITHUB_TOOL_SPECS:
        request = _request_for(collection, spec.tool)
        for label, args in (("full", _full_args(spec)), ("minimal", _required_args(spec))):
            kwargs = _prepare(request, _execution_variables(request, args))
            rendered = [kwargs["url"], *kwargs["headers"].values(), *kwargs["params"].values()]
            rendered.append(json.dumps(kwargs.get("json", kwargs.get("data", ""))))
            for content in rendered:
                for marker in _TEMPLATE_MARKERS:
                    assert marker not in str(content), (
                        f"{spec.tool} [{label}] left {marker!r} after render: {content!r}"
                    )
            assert kwargs["url"].startswith(OFFLINE_ENV["github_api_url"] + "/")
            if spec.repository_scoped:
                assert kwargs["url"].startswith(_OFFLINE_REPO_PREFIX), (
                    f"{spec.tool} must start with the encoded default repository prefix"
                )
            expected_keys = {name for name in spec.query if name in args or name in _PAGINATION}
            assert set(kwargs["params"]) == expected_keys, (
                f"{spec.tool} [{label}] query keys {sorted(kwargs['params'])}"
            )


# ---------------------------------------------------------------------------
# 6. Encoding (template layer)
# ---------------------------------------------------------------------------

_GHES_API_URL = "https://ghe.example.com/api/v3"

_ENCODING_CASES = (
    pytest.param(
        "github_get_repository", {"github_owner": "my org/x#y"}, {},
        "https://api.github.example.test/repos/my%20org%2Fx%23y/hello-world",
        id="owner-reserved-characters",
    ),
    pytest.param(
        "github_get_repository", {"github_repo": "repo?a=b%c+d"}, {},
        "https://api.github.example.test/repos/octo-org/repo%3Fa%3Db%25c%2Bd",
        id="repo-reserved-characters",
    ),
    pytest.param(
        "github_list_issues", {}, {"github_owner": "env org/x", "github_repo": "r#1"},
        "https://api.github.example.test/repos/env%20org%2Fx/r%231/issues",
        id="environment-owner-repo-encoded",
    ),
    pytest.param(
        "github_list_workflow_runs_for_workflow", {"workflow_id": "ci.yml"}, {},
        f"{_OFFLINE_REPO_PREFIX}/actions/workflows/ci.yml/runs",
        id="workflow-file-name",
    ),
    pytest.param(
        "github_list_workflow_runs_for_workflow", {"workflow_id": "dir/ci.yml"}, {},
        f"{_OFFLINE_REPO_PREFIX}/actions/workflows/dir%2Fci.yml/runs",
        id="workflow-file-name-with-slash",
    ),
    pytest.param(
        "github_list_workflow_runs_for_workflow", {"workflow_id": "161335"}, {},
        f"{_OFFLINE_REPO_PREFIX}/actions/workflows/161335/runs",
        id="workflow-numeric-id-string",
    ),
    pytest.param(
        "github_dispatch_workflow", {"workflow_id": "a b#c?d%e+f.yml", "ref": "main"}, {},
        f"{_OFFLINE_REPO_PREFIX}/actions/workflows/a%20b%23c%3Fd%25e%2Bf.yml/dispatches",
        id="dispatch-workflow-reserved-characters",
    ),
    pytest.param(
        "github_get_pull_request", {"pull_number": 7}, {},
        f"{_OFFLINE_REPO_PREFIX}/pulls/7",
        id="pull-number-integer",
    ),
    pytest.param(
        "github_get_pull_request", {"pull_number": "7"}, {},
        f"{_OFFLINE_REPO_PREFIX}/pulls/7",
        id="pull-number-decimal-string",
    ),
    pytest.param(
        "github_list_pull_request_comments", {"pull_number": "8"}, {},
        f"{_OFFLINE_REPO_PREFIX}/issues/8/comments",
        id="pull-conversation-comments-use-issue-path",
    ),
    pytest.param(
        "github_get_issue", {"issue_number": "42"}, {},
        f"{_OFFLINE_REPO_PREFIX}/issues/42",
        id="issue-number-decimal-string",
    ),
    pytest.param(
        "github_get_workflow_run", {"run_id": 30433642}, {},
        f"{_OFFLINE_REPO_PREFIX}/actions/runs/30433642",
        id="run-id-integer",
    ),
    pytest.param(
        "github_get_workflow_job", {"job_id": "399444496"}, {},
        f"{_OFFLINE_REPO_PREFIX}/actions/jobs/399444496",
        id="job-id-decimal-string",
    ),
    pytest.param(
        "github_reply_to_pull_request_review_comment",
        {"pull_number": 3, "comment_id": "99", "body": "ok"}, {},
        f"{_OFFLINE_REPO_PREFIX}/pulls/3/comments/99/replies",
        id="comment-id-decimal-string",
    ),
    pytest.param(
        "github_get_authenticated_user", {}, {"github_api_url": _GHES_API_URL},
        "https://ghe.example.com/api/v3/user",
        id="ghes-api-url-user",
    ),
    pytest.param(
        "github_get_repository", {}, {"github_api_url": _GHES_API_URL},
        "https://ghe.example.com/api/v3/repos/octo-org/hello-world",
        id="ghes-api-url-repository",
    ),
)


@pytest.mark.parametrize(("tool", "args", "env_overrides", "expected_url"), _ENCODING_CASES)
def test_github_template_encoding(
    tool: str, args: dict[str, Any], env_overrides: dict[str, str], expected_url: str
):
    collection = _load_github_collection()
    request = _request_for(collection, tool)
    env = {**OFFLINE_ENV, **env_overrides}
    rendered = _render(request.url, _execution_variables(request, args, env))
    assert rendered == expected_url


_BODY_ENCODING_CASES = (
    pytest.param(
        "github_dispatch_workflow", {"workflow_id": "ci.yml", "ref": 'feature/x"y'},
        {"ref": 'feature/x"y'},
        id="dispatch-ref-verbatim-json-string",
    ),
    pytest.param(
        "github_create_issue", {"title": "t", "labels": ["bug", 'a"b']},
        {"title": "t", "labels": ["bug", 'a"b']},
        id="labels-array-with-quote",
    ),
    pytest.param(
        "github_dispatch_workflow",
        {"workflow_id": "ci.yml", "ref": "main", "inputs": {"env": "prod", "dry": True, "n": 3}},
        {"ref": "main", "inputs": {"env": "prod", "dry": "true", "n": "3"}},
        id="dispatch-inputs-stringified",
    ),
    pytest.param(
        "github_dispatch_workflow",
        {"workflow_id": "ci.yml", "ref": "main", "inputs": {'k"ey': 'v"al', "off": False}},
        {"ref": "main", "inputs": {'k"ey': 'v"al', "off": "false"}},
        id="dispatch-inputs-escaped-keys",
    ),
    pytest.param(
        "github_create_pull_request_review_comment",
        {"pull_number": 1, "body": "b", "commit_id": "abc", "path": "a.py", "line": "12"},
        {"body": "b", "commit_id": "abc", "path": "a.py", "line": 12},
        id="line-decimal-string-to-int",
    ),
    pytest.param(
        "github_create_pull_request",
        {"title": "t", "head": "octo:feature/x", "base": "main", "draft": False},
        {"title": "t", "head": "octo:feature/x", "base": "main", "draft": False},
        id="draft-false-boolean",
    ),
)


@pytest.mark.parametrize(("tool", "args", "expected_payload"), _BODY_ENCODING_CASES)
def test_github_body_value_encoding(
    tool: str, args: dict[str, Any], expected_payload: dict[str, Any]
):
    collection = _load_github_collection()
    request = _request_for(collection, tool)
    assert _render_body_json(request, args, "encoding") == expected_payload


_INVALID_NUMERIC_VALUES = ("7a", "1.5", "")

_INVALID_NUMERIC_CASES = tuple(
    pytest.param(tool, arg, value, id=f"{tool}-{arg}-{value or 'empty'}")
    for tool, arg in sorted(GITHUB_NUMERIC_PATH_IDS)
    for value in _INVALID_NUMERIC_VALUES
)


@pytest.mark.parametrize(("tool", "arg", "value"), _INVALID_NUMERIC_CASES)
def test_github_numeric_path_ids_reject_non_decimal(tool: str, arg: str, value: str):
    collection = _load_github_collection()
    request = _request_for(collection, tool)
    args = {**_required_args(SPECS_BY_TOOL[tool]), arg: value}
    variables = {**OFFLINE_ENV, "mcp": {"request": args}}
    with pytest.raises(IntegerConversionError):
        _render(request.url, variables)


_INVALID_BODY_INTEGER_CASES = tuple(
    pytest.param(tool, arg, value, id=f"{tool}-{arg}-{value or 'empty'}")
    for tool, arg in sorted(GITHUB_NUMERIC_BODY_FIELDS)
    for value in _INVALID_NUMERIC_VALUES
)


@pytest.mark.parametrize(("tool", "arg", "value"), _INVALID_BODY_INTEGER_CASES)
def test_github_body_integers_reject_non_decimal(tool: str, arg: str, value: str):
    """Non-decimal body integers fail closed at both the MCP and template layers."""
    collection = _load_github_collection()
    request = _request_for(collection, tool)
    assert request.mcp_params[arg].type == "integer_or_string"
    args = {**_required_args(SPECS_BY_TOOL[tool]), arg: value}

    # MCP boundary: the integer_or_string contract rejects the value before rendering.
    with pytest.raises(McpArgumentValidationError) as excinfo:
        _execution_variables(request, args)
    assert excinfo.value.parameter_name == arg
    assert excinfo.value.expected_type == "integer_or_string"
    assert excinfo.value.kind == "invalid"

    # Template layer: the body's to_int(...) conversion is strict on raw variables.
    variables = {**OFFLINE_ENV, "mcp": {"request": args}}
    with pytest.raises(IntegerConversionError):
        _render(request.body, variables)


def test_github_numeric_identifier_paths_accept_decimal_strings_and_integers():
    collection = _load_github_collection()
    union_rows = {
        (normalize_mcp_tool_name(request.name), name)
        for request in collection.requests
        for name, parameter in request.mcp_params.items()
        if parameter.type == "integer_or_string" and f"to_int(mcp.request.{name})" in request.url
    }
    assert union_rows == set(GITHUB_NUMERIC_PATH_IDS)
    for tool, name in GITHUB_NUMERIC_PATH_IDS:
        parameter = _request_for(collection, tool).mcp_params[name]
        description = parameter.description.lower()
        for word in ("decimal", "string", "integer"):
            assert word in description, f"{tool}.{name} description lacks {word!r}"
        if name in {"pull_number", "issue_number"}:
            assert "number" in description and "repository" in description, (
                f"{tool}.{name} must say it is a repository-scoped number"
            )

    for spec in GITHUB_TOOL_SPECS:
        if "workflow_id" in spec.args:
            parameter = _request_for(collection, spec.tool).mcp_params["workflow_id"]
            lowered = parameter.description.lower()
            assert "file name" in lowered and "id" in lowered, (
                f"{spec.tool}.workflow_id must accept a numeric ID or a file name"
            )


def test_github_repository_scoped_descriptions_explain_override():
    collection = _load_github_collection()
    scoped = [spec for spec in GITHUB_TOOL_SPECS if spec.repository_scoped]
    assert len(scoped) == GITHUB_TOOL_COUNT - 1
    for spec in scoped:
        description = _request_for(collection, spec.tool).mcp_description
        for key in sorted(GITHUB_OVERRIDABLE_KEYS):
            assert key in description, f"{spec.tool} must mention {key}"


# ---------------------------------------------------------------------------
# 7. Wire layer (prepared request 7b, loopback 7a)
# ---------------------------------------------------------------------------

_DEFAULT_PAGES = {"page": ["1"], "per_page": ["30"]}

_WIRE_QUERY_CASES = (
    pytest.param(
        "github_list_workflow_runs",
        {"branch": "feature/x&y=1#z"},
        {"branch": ["feature/x&y=1#z"], **_DEFAULT_PAGES},
        id="list-runs-branch",
    ),
    pytest.param(
        "github_list_pull_requests",
        {"head": "octo:feature/x", "base": "release/1.0&x"},
        {"head": ["octo:feature/x"], "base": ["release/1.0&x"], **_DEFAULT_PAGES},
        id="list-pulls-head-base",
    ),
    pytest.param(
        "github_list_issues",
        {"labels": "bug,help wanted&x=1#y"},
        {"labels": ["bug,help wanted&x=1#y"], **_DEFAULT_PAGES},
        id="list-issues-labels",
    ),
)


@pytest.mark.parametrize(("tool", "args", "expected_query"), _WIRE_QUERY_CASES)
def test_github_query_reserved_characters_stay_single_key_on_wire(
    tool: str, args: dict[str, Any], expected_query: dict[str, list[str]]
):
    collection = _load_github_collection()
    request = _request_for(collection, tool)
    kwargs = _prepare(request, _execution_variables(request, args))
    prepared = requests.Request(kwargs["method"], kwargs["url"], params=kwargs["params"]).prepare()
    assert prepared.url is not None
    assert_query_single_keys_on_wire(prepared.url, urlsplit(kwargs["url"]).path, expected_query)


def test_github_query_wire_checker_rejects_prejoined_reserved_value():
    """Mutation twin (green by design): a raw pre-joined value splits the query."""
    url = "https://api.github.example.test/repos/octo-org/hello-world/actions/runs"
    prepared = requests.Request("GET", url + "?branch=feature/x&y=1#z").prepare()
    assert prepared.url is not None
    with pytest.raises(AssertionError):
        assert_query_single_keys_on_wire(
            prepared.url, urlsplit(url).path, {"branch": ["feature/x&y=1#z"]}
        )


def _successful_envelope(result: Any, operation: str) -> dict[str, Any]:
    try:
        envelope = json.loads(result.content[0].text)
    except (AttributeError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise AssertionError(f"{operation} did not return a JSON MCP envelope") from exc
    assert result.isError is False, f"{operation} returned an MCP error"
    assert envelope.get("error") is False, f"{operation} returned a request error: {envelope}"
    assert envelope.get("status") == 200, f"{operation} did not reach the stub: {envelope}"
    return envelope


_LOOPBACK_CALLS: tuple[tuple[str, dict[str, Any]], ...] = (
    (
        "github_list_workflow_runs_for_workflow",
        {"github_owner": "my org/x", "workflow_id": "dir/ci.yml", "branch": "feature/x&y=1#z"},
    ),
    ("github_create_issue", {"title": "Bug", "labels": ["bug", 'a"b'], "assignees": ["octocat"]}),
    (
        "github_dispatch_workflow",
        {"workflow_id": "ci.yml", "ref": "main", "inputs": {"env": "prod", "dry": True}},
    ),
    ("github_cancel_workflow_run", {"run_id": "123"}),
)

_LOOPBACK_CALL_TIMEOUT_SECONDS = 10


async def _run_loopback_calls(mcp_url: str) -> None:
    for tool, arguments in _LOOPBACK_CALLS:
        with anyio.fail_after(_LOOPBACK_CALL_TIMEOUT_SECONDS):
            result = await _mcp_call_tool_result(mcp_url, tool, arguments)
        _successful_envelope(result, tool)


@pytest.mark.timeout(60)
def test_github_mcp_loopback_e2e_wire_contract():
    collection = _load_github_collection()
    token = "offline-only-github-token"
    with stub_github_mcp_collection_http() as stub:
        variables = {
            "github_api_url": stub.base_url,
            "github_owner": PLACEHOLDER_OWNER,
            "github_repo": PLACEHOLDER_REPO,
            "github_token": token,
        }
        with live_mcp_server(collection.requests) as server:
            server.impl.set_variable_supplier(lambda: dict(variables))
            server.impl.set_hidden_keys_supplier(lambda: set(GITHUB_HIDDEN_KEYS))
            server.impl.set_overridable_keys_supplier(lambda: set(GITHUB_OVERRIDABLE_KEYS))
            anyio.run(_run_loopback_calls, server.mcp_url)

    captured = stub.requests
    assert [(request.method, request.raw_path) for request in captured] == [
        ("GET", "/repos/my%20org%2Fx/your-repo/actions/workflows/dir%2Fci.yml/runs"),
        ("POST", "/repos/your-org/your-repo/issues"),
        ("POST", "/repos/your-org/your-repo/actions/workflows/ci.yml/dispatches"),
        ("POST", "/repos/your-org/your-repo/actions/runs/123/cancel"),
    ]
    assert [request.query for request in captured] == [
        {"branch": ["feature/x&y=1#z"], "page": ["1"], "per_page": ["30"]},
        {},
        {},
        {},
    ]
    assert [request.body for request in captured] == [
        None,
        {"title": "Bug", "labels": ["bug", 'a"b'], "assignees": ["octocat"]},
        {"ref": "main", "inputs": {"env": "prod", "dry": "true"}},
        {},
    ]
    assert all(request.authorization == f"Bearer {token}" for request in captured)
    assert all(request.accept == GITHUB_ACCEPT for request in captured)
    assert all(request.api_version == GITHUB_API_VERSION for request in captured)


# ---------------------------------------------------------------------------
# 8. Library manifest and README parity
# ---------------------------------------------------------------------------


def test_github_library_manifest_lists_collection_variables_and_preset():
    manifest = _load_manifest()
    collections = list(manifest.collections)
    assert "collections/github_mcp.json" in collections, (
        "examples/pypost-library.yaml does not list collections/github_mcp.json"
    )
    assert collections == [
        "collections/jira_mcp.json",
        "collections/gitlab_mcp.json",
        "collections/github_mcp.json",
        "collections/mcp.json",
    ]
    assert validate_manifest_collections(manifest, EXAMPLES_DIR) == []
    assert "github" in manifest.description.lower()
    assert manifest.version == "2.0.0"

    variables = {variable.name: variable for variable in manifest.variables}
    missing = sorted(GITHUB_ENV_KEYS - set(variables))
    assert not missing, f"examples/pypost-library.yaml missing GitHub variable(s): {missing}"
    assert variables["github_api_url"].default == PLACEHOLDER_API_URL
    assert variables["github_owner"].default == PLACEHOLDER_OWNER
    assert variables["github_repo"].default == PLACEHOLDER_REPO
    for name in ("github_api_url", "github_owner", "github_repo"):
        assert variables[name].secret is False, f"{name} must not be secret"
    assert variables["github_token"].secret is True
    assert variables["github_token"].default == ""
    for other_name in (
        "jira_base_url", "jira_project_key", "jira_credentials",
        "gitlab_base_url", "gitlab_project", "gitlab_token",
    ):
        assert other_name in variables, f"variable {other_name} must stay in the manifest"

    assert "github_com" in manifest.presets, "examples/pypost-library.yaml missing github_com"
    assert manifest.presets["github_com"] == {
        "github_api_url": PLACEHOLDER_API_URL,
        "github_owner": PLACEHOLDER_OWNER,
        "github_repo": PLACEHOLDER_REPO,
    }
    for preset_name, preset in manifest.presets.items():
        assert "github_token" not in preset, f"preset {preset_name} must not carry the token"
    assert manifest.presets["jira_cloud"] == {
        "jira_base_url": "https://your-company.atlassian.net",
        "jira_project_key": "DEMO",
    }
    assert manifest.presets["gitlab_com"] == {
        "gitlab_base_url": "https://gitlab.com",
        "gitlab_project": "your-group/your-project",
    }

    collection = _load_github_collection()
    collection_secrets = {variable.name: variable.secret for variable in collection.variables}
    manifest_secrets = {name: variables[name].secret for name in GITHUB_ENV_KEYS}
    assert collection_secrets == manifest_secrets


def test_github_library_manifest_repo_defaults_match_environment_placeholders(
    tmp_path, monkeypatch
):
    manifest = _load_manifest()
    variables = {variable.name: variable for variable in manifest.variables}
    for name in ("github_owner", "github_repo"):
        assert name in variables, f"examples/pypost-library.yaml missing variable {name}"
        default = variables[name].default
        assert isinstance(default, str) and default.strip(), f"{name} default must be set"

    environment = _load_github_environment(tmp_path, monkeypatch)
    assert "github_com" in manifest.presets, "examples/pypost-library.yaml missing github_com"
    preset = manifest.presets["github_com"]
    expected = {"github_owner": PLACEHOLDER_OWNER, "github_repo": PLACEHOLDER_REPO}
    for name, placeholder in expected.items():
        assert variables[name].default == environment.variables[name] == placeholder
        assert preset[name] == placeholder


_README_GITHUB_SECTIONS = (
    "Recommended import order (GitHub pair)",
    "GitHub authentication",
    "GitHub.com vs GitHub Enterprise Server",
    "GitHub default repository and identifiers",
    "GitHub coverage vs gaps",
)
_README_REQUIRED_TERMS = (
    "github.json",
    "github_token",
    "hidden",
    "fine-grained",
    "classic",
    "`repo`",
    "X-GitHub-Api-Version: 2022-11-28",
    PLACEHOLDER_API_URL,
    "/api/v3",
    "not a security boundary",
    PLACEHOLDER_TOKEN,
    "make check-github-mcp-path-freshness",
    "github_com",
)
_README_TOOL_PATTERN = re.compile(
    r"\bgithub_(?:get|list|create|update|rerun|cancel|dispatch|reply)_[a-z_]+"
)


def test_github_readme_documents_inventory_and_tool_parity():
    readme = EXAMPLES_README_PATH.read_text(encoding="utf-8")
    sections = {heading: _readme_section(readme, heading) for heading in _README_GITHUB_SECTIONS}
    missing_terms = [term for term in _README_REQUIRED_TERMS if term not in readme]
    assert not missing_terms, f"examples/README.md missing GitHub term(s): {missing_terms}"

    inventory = _readme_section(readme, "Standalone Inventory")
    assert "collections/github_mcp.json" in inventory
    assert "collections/github_mcp_rest_paths.json" in inventory
    assert "environments/github.json" in inventory
    assert f"({GITHUB_TOOL_COUNT} REST tools)" in inventory

    library = _readme_section(readme, "Git Collection Library")
    assert "collections/github_mcp.json" in library
    assert "github_com" in library

    coverage = sections["GitHub coverage vs gaps"]
    lowered_coverage = coverage.lower()
    for term in ("merge", "pending", "return_run_details"):
        assert term in lowered_coverage, f"GitHub coverage vs gaps must mention {term!r}"
    for value in ("APPROVE", "REQUEST_CHANGES", "COMMENT"):
        assert value in coverage, f"GitHub coverage vs gaps must list review event {value}"

    for tool in sorted(EXPECTED_GITHUB_TOOLS):
        assert tool in readme, f"examples/README.md does not mention {tool}"
    coverage_tools = {name.rstrip("_") for name in _README_TOOL_PATTERN.findall(coverage)}
    catalog = _load_github_catalog()
    catalog_tools = {entry["tool"] for entry in catalog["tools"]}
    assert coverage_tools == catalog_tools, (
        f"README coverage tools differ from catalog: "
        f"missing {sorted(catalog_tools - coverage_tools)}, "
        f"extra {sorted(coverage_tools - catalog_tools)}"
    )
    assert len(catalog_tools) == GITHUB_TOOL_COUNT
    collection = _load_github_collection()
    assert len(collection.requests) == len(catalog["tools"]) == GITHUB_TOOL_COUNT


# ---------------------------------------------------------------------------
# 9. Secret hygiene
# ---------------------------------------------------------------------------

_SECRET_SCAN_PATHS = (
    GITHUB_COLLECTION_PATH,
    GITHUB_ENV_PATH,
    GITHUB_CATALOG_PATH,
    LIBRARY_MANIFEST_PATH,
    EXAMPLES_README_PATH,
)


def test_github_fixtures_contain_no_real_tokens():
    missing = [
        str(path.relative_to(REPO_ROOT)) for path in _SECRET_SCAN_PATHS if not path.is_file()
    ]
    assert not missing, f"GitHub artifact(s) missing (PYPOST-1334): {missing}"
    for path in _SECRET_SCAN_PATHS:
        matches = find_github_token_like_values(path.read_text(encoding="utf-8"))
        assert not matches, f"{path.relative_to(REPO_ROOT)} contains token-like value(s)"
    assert PLACEHOLDER_TOKEN in GITHUB_ENV_PATH.read_text(encoding="utf-8")


def test_github_fixtures_secret_scan_rejects_ghp_and_github_pat_values():
    """Mutation twin (green by design): the scanner flags realistic GitHub tokens."""
    classic = "ghp_" + "A1b2C3d4E5f6G7h8I9j0" * 2
    classic = classic[:len("ghp_") + 36]
    fine_grained = "github_pat_" + ("A1b2C3d4E5_" * 8)[:82]
    assert len(classic) == 40 and len(fine_grained) == 93
    for token in (classic, fine_grained):
        synthetic = f'{{"github_token": "{token}"}}'
        assert find_github_token_like_values(synthetic) == [token]
    for prefix in ("gho_", "ghu_", "ghs_", "ghr_"):
        assert find_github_token_like_values(f"x {prefix}{'Z9' * 18} y")
    assert not find_github_token_like_values(f'{{"github_token": "{PLACEHOLDER_TOKEN}"}}')
    assert not find_github_token_like_values("never commit ghp_… or github_pat_… values")
