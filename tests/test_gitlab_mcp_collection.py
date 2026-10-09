"""Offline contracts for the GitLab MCP example collection (PYPOST-1316).

The GitLab pair (``examples/collections/gitlab_mcp.json`` +
``examples/environments/gitlab.json``), its locked REST path catalog
(``examples/collections/gitlab_mcp_rest_paths.json``), the library manifest
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
from pypost.core.mcp_tool_contract import normalize_mcp_tool_name
from pypost.core.storage import StorageManager
from pypost.core.template_expression_types import IntegerConversionError
from pypost.core.template_service import TemplateService
from pypost.models.library_manifest import LibraryManifest
from pypost.models.models import Collection, Environment, McpToolParam, RequestData
from tests.helpers.gitlab_mcp_collection_http import stub_gitlab_mcp_collection_http
from tests.helpers.mcp_live_server import live_mcp_server
from tests.test_mcp_server_integration import _mcp_call_tool_result

pytestmark = pytest.mark.timeout(30)

REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_DIR = REPO_ROOT / "examples"
GITLAB_COLLECTION_PATH = EXAMPLES_DIR / "collections" / "gitlab_mcp.json"
GITLAB_ENV_PATH = EXAMPLES_DIR / "environments" / "gitlab.json"
GITLAB_CATALOG_PATH = EXAMPLES_DIR / "collections" / "gitlab_mcp_rest_paths.json"
LIBRARY_MANIFEST_PATH = EXAMPLES_DIR / "pypost-library.yaml"
EXAMPLES_README_PATH = EXAMPLES_DIR / "README.md"

GITLAB_COLLECTION_ID = "gitlab-mcp"
GITLAB_COLLECTION_NAME = "GitLab MCP"
GITLAB_ENVIRONMENT_ID = "gitlab-mcp-environment"
GITLAB_ENVIRONMENT_NAME = "GitLab MCP"
GITLAB_TOOL_COUNT = 25

PLACEHOLDER_BASE_URL = "https://gitlab.com"
PLACEHOLDER_PROJECT = "your-group/your-project"
PLACEHOLDER_TOKEN = "your-gitlab-access-token"
GITLAB_ENV_KEYS = frozenset({"gitlab_base_url", "gitlab_project", "gitlab_token"})
GITLAB_HIDDEN_KEYS = frozenset({"gitlab_token"})
GITLAB_OVERRIDABLE_KEYS = frozenset({"gitlab_project"})

GITLAB_AUTH_HEADER = "Bearer {{ gitlab_token }}"
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

# GitLab token prefixes (https://docs.gitlab.com/security/tokens/).
GITLAB_TOKEN_PATTERN = re.compile(
    r"\bgl(?:pat|oas|dt|rt|cbt|ptt|ft|imt|agent|soat)-[A-Za-z0-9_\-]{8,}"
)

_MCP_REQUEST_NAME_PATTERN = re.compile(r"mcp\.request\.([A-Za-z0-9_]+)")
_TEMPLATE_MARKERS = ("{{", "}}", "{%", "%}")


# ---------------------------------------------------------------------------
# Locked tool table (20-architecture.md, Q4). It is the test-side source of
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
_PAGINATION = {
    "page": Arg("integer_or_string", False, 1),
    "per_page": Arg("integer_or_string", False, 20),
}
_PAGINATION_KEYS = ("page", "per_page")

# JSON body key for an MCP argument when it differs from the argument name.
_BODY_KEY_FOR_ARG = {"note_body": "body"}


@dataclass(frozen=True)
class ToolSpec:
    """One documented GitLab MCP tool."""

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
        return self.tool.replace("_", "-")

    @property
    def project_scoped(self) -> bool:
        return "{{ urlencode(gitlab_project) }}" in self.path

    @property
    def body_args(self) -> tuple[str, ...]:
        return self.body_required + self.body_optional


_P = "/api/v4/projects/{{ urlencode(gitlab_project) }}"
_ISSUE = _P + "/issues/{{ to_int(mcp.request.issue_iid) }}"
_MR = _P + "/merge_requests/{{ to_int(mcp.request.merge_request_iid) }}"
_PIPELINE = _P + "/pipelines/{{ to_int(mcp.request.pipeline_id) }}"


def _opt(*names: str) -> dict[str, Arg]:
    return {name: S_OPT for name in names}


GITLAB_TOOL_SPECS: tuple[ToolSpec, ...] = (
    ToolSpec("gitlab_get_current_user", "Identity", "GET", "/api/v4/user"),
    ToolSpec(
        "gitlab_list_projects", "Projects: search/list", "GET", "/api/v4/projects",
        {**_opt("search", "membership"), **_PAGINATION},
        ("search", "membership", *_PAGINATION_KEYS),
    ),
    ToolSpec("gitlab_get_project", "Projects: get by ID/path", "GET", _P),
    ToolSpec(
        "gitlab_list_branches", "Branches: list", "GET", _P + "/repository/branches",
        {**_opt("search"), **_PAGINATION}, ("search", *_PAGINATION_KEYS),
    ),
    ToolSpec(
        "gitlab_get_branch", "Branches: get", "GET",
        _P + "/repository/branches/{{ urlencode(mcp.request.branch) }}",
        {"branch": S_REQ},
    ),
    ToolSpec(
        "gitlab_get_file", "Files: read at ref", "GET",
        _P + "/repository/files/{{ urlencode(mcp.request.file_path) }}/raw",
        {"file_path": S_REQ, "ref": S_OPT}, ("ref",),
    ),
    ToolSpec(
        "gitlab_list_repository_tree", "Files: tree at ref", "GET", _P + "/repository/tree",
        {**_opt("path", "ref", "recursive"), **_PAGINATION},
        ("path", "ref", "recursive", *_PAGINATION_KEYS),
    ),
    ToolSpec(
        "gitlab_list_commits", "Commits: list (ref/path filter)", "GET",
        _P + "/repository/commits",
        {**_opt("ref_name", "path", "since", "until"), **_PAGINATION},
        ("ref_name", "path", "since", "until", *_PAGINATION_KEYS),
    ),
    ToolSpec(
        "gitlab_get_commit", "Commits: get", "GET",
        _P + "/repository/commits/{{ urlencode(mcp.request.sha) }}",
        {"sha": S_REQ},
    ),
    ToolSpec(
        "gitlab_list_issues", "Issues: list", "GET", _P + "/issues",
        {**_opt("state", "labels", "search"), **_PAGINATION},
        ("state", "labels", "search", *_PAGINATION_KEYS),
    ),
    ToolSpec("gitlab_get_issue", "Issues: get", "GET", _ISSUE, {"issue_iid": ID_REQ}),
    ToolSpec(
        "gitlab_create_issue", "Issues: create", "POST", _P + "/issues",
        {"title": S_REQ, **_opt("description", "labels")},
        body_required=("title",), body_optional=("description", "labels"),
    ),
    ToolSpec(
        "gitlab_update_issue", "Issues: update/close/reopen", "PUT", _ISSUE,
        {"issue_iid": ID_REQ, **_opt("title", "description", "labels", "state_event")},
        body_optional=("title", "description", "labels", "state_event"),
    ),
    ToolSpec(
        "gitlab_list_merge_requests", "MRs: list", "GET", _P + "/merge_requests",
        {**_opt("state", "source_branch", "target_branch", "search"), **_PAGINATION},
        ("state", "source_branch", "target_branch", "search", *_PAGINATION_KEYS),
    ),
    ToolSpec(
        "gitlab_get_merge_request", "MRs: get", "GET", _MR, {"merge_request_iid": ID_REQ},
    ),
    ToolSpec(
        "gitlab_create_merge_request", "MRs: create", "POST", _P + "/merge_requests",
        {
            "source_branch": S_REQ, "target_branch": S_REQ, "title": S_REQ,
            **_opt("description", "labels"),
        },
        body_required=("source_branch", "target_branch", "title"),
        body_optional=("description", "labels"),
    ),
    ToolSpec(
        "gitlab_update_merge_request", "MRs: update/close/reopen", "PUT", _MR,
        {
            "merge_request_iid": ID_REQ,
            **_opt("title", "description", "labels", "target_branch", "state_event"),
        },
        body_optional=("title", "description", "labels", "target_branch", "state_event"),
    ),
    ToolSpec(
        "gitlab_list_issue_notes", "Comments: list on issue", "GET", _ISSUE + "/notes",
        {"issue_iid": ID_REQ, **_opt("sort"), **_PAGINATION}, ("sort", *_PAGINATION_KEYS),
    ),
    ToolSpec(
        "gitlab_create_issue_note", "Comments: add on issue", "POST", _ISSUE + "/notes",
        {"issue_iid": ID_REQ, "note_body": S_REQ}, body_required=("note_body",),
    ),
    ToolSpec(
        "gitlab_list_merge_request_notes", "Comments: list on MR", "GET", _MR + "/notes",
        {"merge_request_iid": ID_REQ, **_opt("sort"), **_PAGINATION},
        ("sort", *_PAGINATION_KEYS),
    ),
    ToolSpec(
        "gitlab_create_merge_request_note", "Comments: add on MR", "POST", _MR + "/notes",
        {"merge_request_iid": ID_REQ, "note_body": S_REQ}, body_required=("note_body",),
    ),
    ToolSpec(
        "gitlab_list_pipelines", "CI: list pipelines", "GET", _P + "/pipelines",
        {**_opt("ref", "status"), **_PAGINATION}, ("ref", "status", *_PAGINATION_KEYS),
    ),
    ToolSpec(
        "gitlab_get_pipeline", "CI: get pipeline", "GET", _PIPELINE, {"pipeline_id": ID_REQ},
    ),
    ToolSpec(
        "gitlab_list_pipeline_jobs", "CI: list jobs of pipeline", "GET", _PIPELINE + "/jobs",
        {"pipeline_id": ID_REQ, **_PAGINATION}, _PAGINATION_KEYS,
    ),
    ToolSpec(
        "gitlab_get_job", "CI: get job", "GET",
        _P + "/jobs/{{ to_int(mcp.request.job_id) }}", {"job_id": ID_REQ},
    ),
)
SPECS_BY_TOOL: dict[str, ToolSpec] = {spec.tool: spec for spec in GITLAB_TOOL_SPECS}
EXPECTED_GITLAB_TOOLS = frozenset(SPECS_BY_TOOL)

# (tool, argument) pairs whose argument is a numeric path identifier.
GITLAB_NUMERIC_PATH_IDS: frozenset[tuple[str, str]] = frozenset(
    (spec.tool, name)
    for spec in GITLAB_TOOL_SPECS
    for name, arg in spec.args.items()
    if arg.type == "integer_or_string" and name not in _PAGINATION
)
_GLOBAL_ID_ARGS = frozenset({"pipeline_id", "job_id"})

# Sample values; quotes/backslashes prove JSON escaping in bodies.
_SAMPLE_VALUES: dict[str, Any] = {
    "issue_iid": 7,
    "merge_request_iid": "11",
    "pipeline_id": 1234,
    "job_id": "5678",
    "page": 2,
    "per_page": "50",
    "membership": "true",
    "recursive": "false",
    "state_event": "close",
    "state": "opened",
    "title": 'Fix "quoted" title \\ with backslash',
    "note_body": 'Looks "good" & done',
    "description": "Line one\nLine two",
    "labels": "bug,backend",
}

OFFLINE_ENV: dict[str, str] = {
    "gitlab_base_url": "https://gitlab.example.test",
    "gitlab_project": "group/subgroup/my-project",
    "gitlab_token": "offline-placeholder-token",
}
_OFFLINE_PROJECT_SEGMENT = "group%2Fsubgroup%2Fmy-project"


def _sample(name: str) -> Any:
    return _SAMPLE_VALUES.get(name, f"sample-{name.replace('_', '-')}")


def _full_args(spec: ToolSpec) -> dict[str, Any]:
    return {name: _sample(name) for name in spec.args}


def _required_args(spec: ToolSpec) -> dict[str, Any]:
    return {name: _sample(name) for name, arg in spec.args.items() if arg.required}


# ---------------------------------------------------------------------------
# Guarded loaders — every missing artifact becomes a named assertion.
# ---------------------------------------------------------------------------


def _require_file(path: Path) -> None:
    assert path.is_file(), f"{path.relative_to(REPO_ROOT)} missing (PYPOST-1316)"


def _load_gitlab_collection() -> Collection:
    _require_file(GITLAB_COLLECTION_PATH)
    collections, parse_errors = load_collection_import_candidates(GITLAB_COLLECTION_PATH)
    assert parse_errors == [], f"gitlab_mcp.json parse errors: {parse_errors}"
    assert len(collections) == 1
    collection = collections[0]
    assert collection.id == GITLAB_COLLECTION_ID
    return collection


def _load_gitlab_environment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Environment:
    _require_file(GITLAB_ENV_PATH)
    monkeypatch.delenv("PYPOST_ENV_ENCRYPTION_ENABLED", raising=False)
    monkeypatch.delenv("PYPOST_ENV_ENCRYPTION_KEY", raising=False)
    storage = StorageManager(data_dir=tmp_path / "pypost-data")
    environments, parse_errors = load_import_candidates(GITLAB_ENV_PATH, storage)
    assert parse_errors == [], f"gitlab.json parse errors: {parse_errors}"
    assert len(environments) == 1
    return environments[0]


def _load_gitlab_catalog() -> dict[str, Any]:
    _require_file(GITLAB_CATALOG_PATH)
    payload = json.loads(GITLAB_CATALOG_PATH.read_text(encoding="utf-8"))
    assert isinstance(payload, dict), "gitlab_mcp_rest_paths.json must be a JSON object"
    for key in ("version", "description", "reviewed_on"):
        assert payload.get(key), f"gitlab_mcp_rest_paths.json missing {key!r}"
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
    assert tool in by_tool, f"gitlab_mcp.json has no request publishing tool {tool}"
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
        set(GITLAB_HIDDEN_KEYS),
        set(GITLAB_OVERRIDABLE_KEYS),
        request_data=request,
    )


def _render(content: str, variables: Mapping[str, Any]) -> str:
    return TemplateService().render_string_strict_conversion(content, dict(variables), "mcp")


def _prepare(request: RequestData, variables: Mapping[str, Any]) -> dict[str, Any]:
    kwargs, _ = HTTPClient()._prepare_request_kwargs(request, dict(variables))
    return kwargs


# ---------------------------------------------------------------------------
# Shared checkers (each one has a synthetic mutation twin below).
# ---------------------------------------------------------------------------


def _template_fields(request: RequestData) -> list[str]:
    fields = [request.url, request.body, *request.headers.values(), *request.params.values()]
    return [content for content in fields if content]


def assert_gitlab_auth_convention(requests_: Sequence[RequestData]) -> None:
    """Every request uses one Bearer header and no other token location."""
    for request in requests_:
        auth = request.headers.get("Authorization")
        assert auth == GITLAB_AUTH_HEADER, (
            f"Request {request.id} auth convention breach: expected "
            f"{GITLAB_AUTH_HEADER!r}, got {auth!r}"
        )
        header_names = {name.lower() for name in request.headers}
        assert "private-token" not in header_names, (
            f"Request {request.id} must not send PRIVATE-TOKEN"
        )
        token_params = sorted(name for name in request.params if "token" in name.lower())
        assert not token_params, f"Request {request.id} has token query param(s) {token_params}"
        assert "gitlab_token" not in request.url, f"Request {request.id} puts the token in the URL"


def assert_gitlab_mcp_params_declared_and_used(request: RequestData) -> None:
    """Every ``mcp.request.X`` is declared and every declared param is referenced."""
    referenced: set[str] = set()
    for content in _template_fields(request):
        referenced.update(_MCP_REQUEST_NAME_PATTERN.findall(content))
    declared = set(request.mcp_params)
    dangling = sorted(referenced - declared)
    dead = sorted(declared - referenced)
    assert not dangling, f"Request {request.id} undeclared mcp.request name(s): {dangling}"
    assert not dead, f"Request {request.id} declared but unused mcp_params: {dead}"


def assert_gitlab_catalog_matches_collection(
    collection_requests: Sequence[RequestData], catalog_tools: Sequence[Mapping[str, Any]]
) -> None:
    """Request ids, tool names, methods and paths equal the locked catalog exactly."""
    by_id = {request.id: request for request in collection_requests}
    catalog_ids = {entry["id"] for entry in catalog_tools}
    missing = sorted(catalog_ids - set(by_id))
    extra = sorted(set(by_id) - catalog_ids)
    assert not missing, f"gitlab_mcp.json missing catalog request id(s): {missing}"
    assert not extra, f"gitlab_mcp.json has request id(s) not in the catalog: {extra}"
    for entry in catalog_tools:
        request = by_id[entry["id"]]
        tool = normalize_mcp_tool_name(request.name)
        assert tool == entry["tool"], (
            f"{entry['id']} publishes {tool!r}, catalog locks {entry['tool']!r}"
        )
        assert request.method.upper() == entry["method"], (
            f"{entry['tool']} method drifted: expected {entry['method']}, got {request.method}"
        )
        expected_url = "{{ gitlab_base_url }}" + entry["path"]
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


def find_gitlab_token_like_values(text: str) -> list[str]:
    """Return every substring that looks like a real GitLab token."""
    return GITLAB_TOKEN_PATTERN.findall(text)


def _readme_section(readme: str, heading: str) -> str:
    marker = f"## {heading}\n"
    assert marker in readme, f"examples/README.md missing GitLab section '## {heading}'"
    start = readme.index(marker) + len(marker)
    next_heading = re.search(r"^## ", readme[start:], flags=re.MULTILINE)
    end = start + next_heading.start() if next_heading else len(readme)
    return readme[start:end]


def _synthetic_request(spec: ToolSpec) -> RequestData:
    """Build an in-memory request that satisfies ``spec`` (for checker twins)."""
    params: dict[str, str] = {}
    for name in spec.query:
        params[name] = (
            f"{{{{ to_int(mcp.request.{name}) }}}}"
            if name in _PAGINATION
            else f"{{{{ mcp.request.{name} }}}}"
        )
    body = ""
    if spec.body_args:
        body = "{" + ", ".join(
            f'"{_BODY_KEY_FOR_ARG.get(name, name)}": '
            f"{{{{ to_json_string(mcp.request.{name}) }}}}"
            for name in spec.body_args
        ) + "}"
    return RequestData(
        id=spec.request_id,
        name=spec.tool,
        method=spec.method,
        url="{{ gitlab_base_url }}" + spec.path,
        headers={"Accept": "application/json", "Authorization": GITLAB_AUTH_HEADER},
        params=params,
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


def test_gitlab_mcp_collection_imports_via_native_loader():
    collection = _load_gitlab_collection()
    assert collection.name == GITLAB_COLLECTION_NAME
    assert collection.version == "1.0.0"
    assert str(GITLAB_TOOL_COUNT) in collection.description
    assert len(collection.requests) == GITLAB_TOOL_COUNT

    for request in collection.requests:
        assert request.expose_as_mcp is True, f"{request.id} not exposed via MCP"
        assert request.mcp_description.strip(), f"{request.id} has an empty mcp_description"
        assert request.body_type == "json", f"{request.id} body_type must be json"
        assert request.retry_policy is None, f"{request.id} must not set a retry_policy"

    variables = {variable.name: variable for variable in collection.variables}
    assert set(variables) == GITLAB_ENV_KEYS
    assert variables["gitlab_token"].secret is True
    assert variables["gitlab_token"].required is True
    assert variables["gitlab_token"].default == ""
    assert variables["gitlab_base_url"].secret is False
    assert variables["gitlab_project"].secret is False


def test_gitlab_environment_imports_with_placeholders(tmp_path, monkeypatch):
    environment = _load_gitlab_environment(tmp_path, monkeypatch)
    assert environment.id == GITLAB_ENVIRONMENT_ID
    assert environment.name == GITLAB_ENVIRONMENT_NAME
    assert environment.variables == {
        "gitlab_base_url": PLACEHOLDER_BASE_URL,
        "gitlab_project": PLACEHOLDER_PROJECT,
        "gitlab_token": PLACEHOLDER_TOKEN,
    }
    assert environment.hidden_keys == set(GITLAB_HIDDEN_KEYS)
    assert environment.mcp_overridable_keys == set(GITLAB_OVERRIDABLE_KEYS)
    assert "gitlab_token" not in environment.mcp_overridable_keys
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
    if spec.project_scoped:
        properties["gitlab_project"] = dict(_OVERRIDE_PROPERTY)
    return {
        "type": "object",
        "properties": properties,
        "required": sorted(name for name, arg in spec.args.items() if arg.required),
    }


def _schema_without_arg_descriptions(tool: str, schema: dict[str, Any]) -> dict[str, Any]:
    properties: dict[str, Any] = {}
    for name, prop in schema.get("properties", {}).items():
        prop = dict(prop)
        if name != "gitlab_project":
            description = prop.pop("description", "")
            assert description.strip(), f"{tool}.{name} has no agent-facing description"
        properties[name] = prop
    return {
        "type": schema.get("type"),
        "properties": properties,
        "required": sorted(schema.get("required", [])),
    }


def test_gitlab_mcp_published_tools_match_documented_set():
    collection = _load_gitlab_collection()
    impl = MCPServerImpl(
        template_service=TemplateService(),
        variable_supplier=lambda: dict(OFFLINE_ENV),
        hidden_keys_supplier=lambda: set(GITLAB_HIDDEN_KEYS),
        overridable_keys_supplier=lambda: set(GITLAB_OVERRIDABLE_KEYS),
    )
    impl.register_tools(collection.requests)

    published = set(impl.tools_map)
    assert published == EXPECTED_GITLAB_TOOLS, (
        f"missing tools {sorted(EXPECTED_GITLAB_TOOLS - published)}, "
        f"undocumented tools {sorted(published - EXPECTED_GITLAB_TOOLS)}"
    )
    assert len(collection.requests) == len(published), "tool names must be unique"
    for name in published:
        assert len(name) <= 64
        assert re.fullmatch(r"gitlab_[a-z_]+", name), name

    for tool, request in impl.tools_map.items():
        assert isinstance(request, RequestData)
        schema = impl._generate_schema(request)
        properties = schema.get("properties", {})
        assert "gitlab_token" not in properties, f"{tool} publishes the token"
        assert "gitlab_base_url" not in properties, f"{tool} publishes gitlab_base_url"
        actual = _schema_without_arg_descriptions(tool, schema)
        assert actual == _expected_schema(SPECS_BY_TOOL[tool]), f"{tool} schema drifted"


# ---------------------------------------------------------------------------
# 3. HTTP contracts (method, path, query, body)
# ---------------------------------------------------------------------------


def test_gitlab_mcp_http_contracts_match_locked_catalog():
    catalog = _load_gitlab_catalog()
    expected_entries = sorted(
        (_catalog_entry(spec) for spec in GITLAB_TOOL_SPECS), key=lambda entry: entry["id"]
    )
    actual_entries = sorted(
        (
            {key: entry.get(key) for key in ("id", "tool", "capability", "method", "path")}
            for entry in catalog["tools"]
        ),
        key=lambda entry: str(entry["id"]),
    )
    assert actual_entries == expected_entries, "gitlab_mcp_rest_paths.json drifted from design"

    collection = _load_gitlab_collection()
    assert_gitlab_catalog_matches_collection(collection.requests, catalog["tools"])


def test_gitlab_mcp_catalog_check_rejects_path_drift():
    """Mutation twin (green by design): the catalog checker flags a drifted path."""
    requests_ = [_synthetic_request(spec) for spec in GITLAB_TOOL_SPECS]
    catalog_tools = [_catalog_entry(spec) for spec in GITLAB_TOOL_SPECS]
    assert_gitlab_catalog_matches_collection(requests_, catalog_tools)

    drifted = next(request for request in requests_ if request.id == "gitlab-get-file")
    observed = drifted.url.replace("/raw", "")
    drifted.url = observed
    with pytest.raises(AssertionError) as excinfo:
        assert_gitlab_catalog_matches_collection(requests_, catalog_tools)
    message = str(excinfo.value)
    assert "gitlab_get_file" in message
    assert observed in message


_GITLAB_PATH_FRESHNESS_TARGET = "check-gitlab-mcp-path-freshness"
_GITLAB_PATH_FRESHNESS_NODES = (
    "tests/test_gitlab_mcp_collection.py::test_gitlab_mcp_http_contracts_match_locked_catalog",
    "tests/test_gitlab_mcp_collection.py::test_gitlab_mcp_catalog_check_rejects_path_drift",
)


def _makefile_phony_targets(text: str) -> set[str]:
    """Return every target named in the (possibly backslash-continued) .PHONY lines."""
    joined = text.replace("\\\n", " ")
    targets: set[str] = set()
    for line in joined.splitlines():
        if line.startswith(".PHONY:"):
            targets.update(line.removeprefix(".PHONY:").split())
    return targets


def test_gitlab_makefile_path_freshness_target_declared():
    """Design Q5: offline path-freshness gate mirroring check-jira-mcp-path-freshness."""
    makefile_path = REPO_ROOT / "Makefile"
    assert makefile_path.is_file(), f"{makefile_path} missing"
    text = makefile_path.read_text(encoding="utf-8")
    target = _GITLAB_PATH_FRESHNESS_TARGET

    assert target in _makefile_phony_targets(text), (
        f"Makefile .PHONY does not declare {target} (PYPOST-1316)"
    )

    lines = text.splitlines()
    header_index = next(
        (index for index, line in enumerate(lines) if line.startswith(f"{target}:")), None
    )
    assert header_index is not None, f"Makefile has no '{target}:' rule (PYPOST-1316)"
    header = lines[header_index]
    prerequisites, _, help_text = header.removeprefix(f"{target}:").partition("##")
    assert "$(VENV_MARKER)" in prerequisites.split(), f"{target} must depend on $(VENV_MARKER)"
    assert help_text.strip(), f"{target} needs a '## <help text>' comment"

    recipe_lines: list[str] = []
    for line in lines[header_index + 1 :]:
        if not line.startswith("\t"):
            break
        recipe_lines.append(line.strip().removesuffix("\\").strip())
    tokens = " ".join(recipe_lines).split()
    assert tokens[:4] == ["QT_QPA_PLATFORM=offscreen", "$(BIN)/python", "-m", "pytest"], (
        f"{target} recipe must run 'QT_QPA_PLATFORM=offscreen $(BIN)/python -m pytest': {tokens}"
    )
    assert tokens[4:] == [*_GITLAB_PATH_FRESHNESS_NODES, "-q"], (
        f"{target} recipe must select exactly the catalog freshness nodes with -q: {tokens}"
    )


def test_gitlab_mcp_query_params_match_documented_set():
    collection = _load_gitlab_collection()
    for spec in GITLAB_TOOL_SPECS:
        request = _request_for(collection, spec.tool)
        expected = {
            name: (
                f"{{{{ to_int(mcp.request.{name}) }}}}"
                if name in _PAGINATION
                else f"{{{{ mcp.request.{name} }}}}"
            )
            for name in spec.query
        }
        assert request.params == expected, f"{spec.tool} query params drifted"
        for value in request.params.values():
            assert "urlencode(" not in value, f"{spec.tool} double-encodes a query value"


def test_gitlab_mcp_headers_and_read_bodies_follow_conventions():
    collection = _load_gitlab_collection()
    for spec in GITLAB_TOOL_SPECS:
        request = _request_for(collection, spec.tool)
        expected_headers = {"Accept": "application/json", "Authorization": GITLAB_AUTH_HEADER}
        if spec.method in {"POST", "PUT"}:
            expected_headers["Content-Type"] = "application/json"
        assert request.headers == expected_headers, f"{spec.tool} headers drifted"
        if spec.method == "GET":
            assert request.body == "", f"read tool {spec.tool} must not send a body"
        else:
            assert request.body.strip(), f"write tool {spec.tool} must send a JSON body"


def _body_subsets(spec: ToolSpec) -> list[tuple[str, dict[str, Any]]]:
    required = _required_args(spec)
    subsets = [("all", _full_args(spec)), ("minimal", required)]
    subsets.extend(
        (f"only-{name}", {**required, name: _sample(name)}) for name in spec.body_optional
    )
    return subsets


def test_gitlab_mcp_bodies_render_documented_json_fields():
    collection = _load_gitlab_collection()
    write_specs = [spec for spec in GITLAB_TOOL_SPECS if spec.body_args]
    assert len(write_specs) == 6
    for spec in write_specs:
        request = _request_for(collection, spec.tool)
        for label, args in _body_subsets(spec):
            variables = _execution_variables(request, args)
            rendered = _render(request.body, variables)
            try:
                payload = json.loads(rendered)
            except json.JSONDecodeError as exc:
                raise AssertionError(f"{spec.tool} [{label}] body is not valid JSON") from exc
            expected = {
                _BODY_KEY_FOR_ARG.get(name, name): args[name]
                for name in spec.body_args
                if name in args
            }
            assert payload == expected, f"{spec.tool} [{label}] body drifted: {payload!r}"

        gui_rendered = _render(request.body, dict(OFFLINE_ENV))
        assert json.loads(gui_rendered) == {}, f"{spec.tool} GUI render must be '{{}}'"


# ---------------------------------------------------------------------------
# 4. Auth convention
# ---------------------------------------------------------------------------


def test_gitlab_mcp_requests_use_bearer_auth_convention():
    collection = _load_gitlab_collection()
    assert_gitlab_auth_convention(collection.requests)


def test_gitlab_mcp_auth_convention_rejects_private_token_header():
    """Mutation twin (green by design): the auth checker rejects other conventions."""
    request = _synthetic_request(SPECS_BY_TOOL["gitlab_get_project"])
    assert_gitlab_auth_convention([request])

    altered = request.model_copy(deep=True)
    altered.headers["Authorization"] = "Bearer {{ other_token }}"
    with pytest.raises(AssertionError, match=r"gitlab-get-project"):
        assert_gitlab_auth_convention([altered])

    private = request.model_copy(deep=True)
    private.headers["PRIVATE-TOKEN"] = "{{ gitlab_token }}"
    with pytest.raises(AssertionError, match=r"PRIVATE-TOKEN"):
        assert_gitlab_auth_convention([private])

    query_token = request.model_copy(deep=True)
    query_token.params["private_token"] = "{{ gitlab_token }}"
    with pytest.raises(AssertionError, match=r"private_token"):
        assert_gitlab_auth_convention([query_token])


# ---------------------------------------------------------------------------
# 5. Placeholder integrity
# ---------------------------------------------------------------------------


def test_gitlab_mcp_params_declared_and_used():
    collection = _load_gitlab_collection()
    for request in collection.requests:
        assert_gitlab_mcp_params_declared_and_used(request)


def test_gitlab_mcp_params_checker_rejects_dangling_and_dead_arguments():
    """Mutation twin (green by design): both directions of the check can fail."""
    request = _synthetic_request(SPECS_BY_TOOL["gitlab_get_branch"])
    assert_gitlab_mcp_params_declared_and_used(request)

    dangling = request.model_copy(deep=True)
    del dangling.mcp_params["branch"]
    with pytest.raises(AssertionError, match=r"gitlab-get-branch.*undeclared.*branch"):
        assert_gitlab_mcp_params_declared_and_used(dangling)

    dead = request.model_copy(deep=True)
    dead.mcp_params["unused_arg"] = McpToolParam(type="string", description="x", required=False)
    with pytest.raises(AssertionError, match=r"gitlab-get-branch.*unused.*unused_arg"):
        assert_gitlab_mcp_params_declared_and_used(dead)


def test_gitlab_mcp_companion_env_covers_referenced_names(tmp_path, monkeypatch):
    collection = _load_gitlab_collection()
    environment = _load_gitlab_environment(tmp_path, monkeypatch)
    template_service = TemplateService()
    referenced: set[str] = set()
    for request in collection.requests:
        referenced.update(
            McpSecretsPolicy.extract_environment_variable_names(request, template_service)
        )
    assert referenced == set(GITLAB_ENV_KEYS), f"env references drifted: {sorted(referenced)}"
    missing = referenced - set(environment.variables)
    assert not missing, f"Missing companion key(s): {sorted(missing)}"


def test_gitlab_mcp_argument_names_do_not_shadow_dict_attributes():
    collection = _load_gitlab_collection()
    for request in collection.requests:
        shadowing = sorted(set(request.mcp_params) & _DICT_ATTRIBUTE_NAMES)
        assert not shadowing, f"{request.id} argument(s) shadow dict attributes: {shadowing}"


def test_gitlab_mcp_full_render_leaves_no_template_markers():
    collection = _load_gitlab_collection()
    for spec in GITLAB_TOOL_SPECS:
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
            assert kwargs["url"].startswith(OFFLINE_ENV["gitlab_base_url"] + "/api/v4/")
            if spec.project_scoped:
                assert kwargs["url"].startswith(
                    OFFLINE_ENV["gitlab_base_url"] + "/api/v4/projects/" + _OFFLINE_PROJECT_SEGMENT
                ), f"{spec.tool} must start with the encoded default project prefix"
            expected_keys = {name for name in spec.query if name in args or name in _PAGINATION}
            assert set(kwargs["params"]) == expected_keys, (
                f"{spec.tool} [{label}] query keys {sorted(kwargs['params'])}"
            )


# ---------------------------------------------------------------------------
# 6. Encoding (template layer)
# ---------------------------------------------------------------------------

_ENCODING_CASES = (
    pytest.param(
        "gitlab_get_project", {}, {"gitlab_project": "group/subgroup/my-project"},
        "https://gitlab.example.test/api/v4/projects/group%2Fsubgroup%2Fmy-project",
        id="nested-group-project-path",
    ),
    pytest.param(
        "gitlab_get_project", {"gitlab_project": "42"}, {},
        "https://gitlab.example.test/api/v4/projects/42",
        id="numeric-project-id-string-override",
    ),
    pytest.param(
        "gitlab_list_issues", {"gitlab_project": "other/team/repo"}, {},
        "https://gitlab.example.test/api/v4/projects/other%2Fteam%2Frepo/issues",
        id="project-path-override",
    ),
    pytest.param(
        "gitlab_get_file", {"file_path": "src/app/main.py"}, {},
        f"https://gitlab.example.test/api/v4/projects/{_OFFLINE_PROJECT_SEGMENT}"
        "/repository/files/src%2Fapp%2Fmain.py/raw",
        id="file-path-with-slashes",
    ),
    pytest.param(
        "gitlab_get_file", {"file_path": "docs/a b#c?d%e+f.md"}, {},
        f"https://gitlab.example.test/api/v4/projects/{_OFFLINE_PROJECT_SEGMENT}"
        "/repository/files/docs%2Fa%20b%23c%3Fd%25e%2Bf.md/raw",
        id="file-path-reserved-characters",
    ),
    pytest.param(
        "gitlab_get_branch", {"branch": "feature/x"}, {},
        f"https://gitlab.example.test/api/v4/projects/{_OFFLINE_PROJECT_SEGMENT}"
        "/repository/branches/feature%2Fx",
        id="branch-with-slash",
    ),
    pytest.param(
        "gitlab_get_commit", {"sha": "a1b2c3d"}, {},
        f"https://gitlab.example.test/api/v4/projects/{_OFFLINE_PROJECT_SEGMENT}"
        "/repository/commits/a1b2c3d",
        id="commit-sha",
    ),
    pytest.param(
        "gitlab_get_issue", {"issue_iid": 7}, {},
        f"https://gitlab.example.test/api/v4/projects/{_OFFLINE_PROJECT_SEGMENT}/issues/7",
        id="issue-iid-integer",
    ),
    pytest.param(
        "gitlab_get_issue", {"issue_iid": "7"}, {},
        f"https://gitlab.example.test/api/v4/projects/{_OFFLINE_PROJECT_SEGMENT}/issues/7",
        id="issue-iid-decimal-string",
    ),
    pytest.param(
        "gitlab_get_merge_request", {"merge_request_iid": "12"}, {},
        f"https://gitlab.example.test/api/v4/projects/{_OFFLINE_PROJECT_SEGMENT}"
        "/merge_requests/12",
        id="merge-request-iid-decimal-string",
    ),
    pytest.param(
        "gitlab_get_pipeline", {"pipeline_id": 98765}, {},
        f"https://gitlab.example.test/api/v4/projects/{_OFFLINE_PROJECT_SEGMENT}"
        "/pipelines/98765",
        id="pipeline-id-integer",
    ),
    pytest.param(
        "gitlab_get_job", {"job_id": "4321"}, {},
        f"https://gitlab.example.test/api/v4/projects/{_OFFLINE_PROJECT_SEGMENT}/jobs/4321",
        id="job-id-decimal-string",
    ),
    pytest.param(
        "gitlab_get_current_user", {}, {"gitlab_base_url": "https://git.example.com/gitlab"},
        "https://git.example.com/gitlab/api/v4/user",
        id="self-managed-sub-path-base-url",
    ),
)


@pytest.mark.parametrize(("tool", "args", "env_overrides", "expected_url"), _ENCODING_CASES)
def test_gitlab_template_encoding(
    tool: str, args: dict[str, Any], env_overrides: dict[str, str], expected_url: str
):
    collection = _load_gitlab_collection()
    request = _request_for(collection, tool)
    env = {**OFFLINE_ENV, **env_overrides}
    rendered = _render(request.url, _execution_variables(request, args, env))
    assert rendered == expected_url


_INVALID_NUMERIC_CASES = tuple(
    pytest.param(tool, arg, value, id=f"{tool}-{arg}-{value or 'empty'}")
    for tool, arg in sorted(GITLAB_NUMERIC_PATH_IDS)
    for value in ("7a", "1.5", "")
)


@pytest.mark.parametrize(("tool", "arg", "value"), _INVALID_NUMERIC_CASES)
def test_gitlab_numeric_path_ids_reject_non_decimal(tool: str, arg: str, value: str):
    collection = _load_gitlab_collection()
    request = _request_for(collection, tool)
    args = {**_required_args(SPECS_BY_TOOL[tool]), arg: value}
    variables = {**OFFLINE_ENV, "mcp": {"request": args}}
    with pytest.raises(IntegerConversionError):
        _render(request.url, variables)


def test_gitlab_numeric_identifier_paths_accept_decimal_strings_and_integers():
    collection = _load_gitlab_collection()
    union_rows = {
        (normalize_mcp_tool_name(request.name), name)
        for request in collection.requests
        for name, parameter in request.mcp_params.items()
        if parameter.type == "integer_or_string" and f"to_int(mcp.request.{name})" in request.url
    }
    assert union_rows == set(GITLAB_NUMERIC_PATH_IDS)
    for tool, name in GITLAB_NUMERIC_PATH_IDS:
        parameter = _request_for(collection, tool).mcp_params[name]
        description = parameter.description.lower()
        for word in ("decimal", "string", "integer"):
            assert word in description, f"{tool}.{name} description lacks {word!r}"
        scope_word = "global" if name in _GLOBAL_ID_ARGS else "iid"
        assert scope_word in description, f"{tool}.{name} description lacks {scope_word!r}"


def test_gitlab_project_scoped_descriptions_explain_override():
    collection = _load_gitlab_collection()
    for spec in GITLAB_TOOL_SPECS:
        description = _request_for(collection, spec.tool).mcp_description
        if spec.project_scoped:
            assert "gitlab_project" in description, f"{spec.tool} must mention gitlab_project"
            lowered = description.lower()
            assert re.search(r"\bid\b", lowered) and "path" in lowered, (
                f"{spec.tool} must say a project accepts an ID or a path"
            )


# ---------------------------------------------------------------------------
# 7. Wire layer (prepared request 7b, loopback 7a)
# ---------------------------------------------------------------------------

_WIRE_QUERY_CASES = (
    pytest.param(
        "gitlab_get_file",
        {"file_path": "src/app/main.py", "ref": "feature/x&y=1#z"},
        {"ref": ["feature/x&y=1#z"]},
        id="get-file-ref",
    ),
    pytest.param(
        "gitlab_list_projects",
        {"search": "a b&c"},
        {"search": ["a b&c"], "page": ["1"], "per_page": ["20"]},
        id="list-projects-search",
    ),
    pytest.param(
        "gitlab_list_branches",
        {"search": "a b&c"},
        {"search": ["a b&c"], "page": ["1"], "per_page": ["20"]},
        id="list-branches-search",
    ),
)


@pytest.mark.parametrize(("tool", "args", "expected_query"), _WIRE_QUERY_CASES)
def test_gitlab_query_reserved_characters_stay_single_key_on_wire(
    tool: str, args: dict[str, Any], expected_query: dict[str, list[str]]
):
    collection = _load_gitlab_collection()
    request = _request_for(collection, tool)
    kwargs = _prepare(request, _execution_variables(request, args))
    prepared = requests.Request(kwargs["method"], kwargs["url"], params=kwargs["params"]).prepare()
    assert prepared.url is not None
    assert_query_single_keys_on_wire(prepared.url, urlsplit(kwargs["url"]).path, expected_query)


def test_gitlab_query_wire_checker_rejects_prejoined_reserved_value():
    """Mutation twin (green by design): a raw pre-joined value splits the query."""
    url = "https://gitlab.example.test/api/v4/projects/1/repository/files/f/raw"
    prepared = requests.Request("GET", url + "?ref=feature/x&y=1#z").prepare()
    assert prepared.url is not None
    with pytest.raises(AssertionError):
        assert_query_single_keys_on_wire(
            prepared.url, urlsplit(url).path, {"ref": ["feature/x&y=1#z"]}
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
    ("gitlab_get_current_user", {}),
    ("gitlab_get_file", {"file_path": "src/app/main.py", "ref": "feature/x&y=1#z"}),
    ("gitlab_list_projects", {"search": "a b&c"}),
    ("gitlab_create_issue_note", {"issue_iid": "7", "note_body": 'Looks "good" & done'}),
)


_LOOPBACK_CALL_TIMEOUT_SECONDS = 10


async def _run_loopback_calls(mcp_url: str) -> None:
    for tool, arguments in _LOOPBACK_CALLS:
        with anyio.fail_after(_LOOPBACK_CALL_TIMEOUT_SECONDS):
            result = await _mcp_call_tool_result(mcp_url, tool, arguments)
        _successful_envelope(result, tool)


@pytest.mark.timeout(60)
def test_gitlab_mcp_loopback_e2e_wire_contract():
    collection = _load_gitlab_collection()
    token = "offline-only-gitlab-token"
    with stub_gitlab_mcp_collection_http() as stub:
        variables = {
            "gitlab_base_url": stub.base_url,
            "gitlab_project": "group/sub/proj",
            "gitlab_token": token,
        }
        with live_mcp_server(collection.requests) as server:
            server.impl.set_variable_supplier(lambda: dict(variables))
            server.impl.set_hidden_keys_supplier(lambda: set(GITLAB_HIDDEN_KEYS))
            server.impl.set_overridable_keys_supplier(lambda: set(GITLAB_OVERRIDABLE_KEYS))
            anyio.run(_run_loopback_calls, server.mcp_url)

    captured = stub.requests
    assert [(request.method, request.raw_path) for request in captured] == [
        ("GET", "/api/v4/user"),
        ("GET", "/api/v4/projects/group%2Fsub%2Fproj/repository/files/src%2Fapp%2Fmain.py/raw"),
        ("GET", "/api/v4/projects"),
        ("POST", "/api/v4/projects/group%2Fsub%2Fproj/issues/7/notes"),
    ]
    assert [request.query for request in captured] == [
        {},
        {"ref": ["feature/x&y=1#z"]},
        {"search": ["a b&c"], "page": ["1"], "per_page": ["20"]},
        {},
    ]
    assert [request.body for request in captured] == [
        None, None, None, {"body": 'Looks "good" & done'},
    ]
    assert all(request.authorization == f"Bearer {token}" for request in captured)


# ---------------------------------------------------------------------------
# 8. Library manifest and README parity
# ---------------------------------------------------------------------------


def test_gitlab_library_manifest_lists_collection_variables_and_preset():
    manifest = _load_manifest()
    collections = list(manifest.collections)
    assert "collections/gitlab_mcp.json" in collections, (
        "examples/pypost-library.yaml does not list collections/gitlab_mcp.json"
    )
    assert collections == [
        "collections/jira_mcp.json",
        "collections/gitlab_mcp.json",
        "collections/github_mcp.json",  # PYPOST-1334 (shared manifest)
        "collections/mcp.json",
    ]
    assert validate_manifest_collections(manifest, EXAMPLES_DIR) == []
    assert "gitlab" in manifest.description.lower()
    assert manifest.version == "2.0.0"

    variables = {variable.name: variable for variable in manifest.variables}
    missing = sorted(GITLAB_ENV_KEYS - set(variables))
    assert not missing, f"examples/pypost-library.yaml missing GitLab variable(s): {missing}"
    assert variables["gitlab_base_url"].default == PLACEHOLDER_BASE_URL
    assert variables["gitlab_base_url"].secret is False
    assert variables["gitlab_project"].secret is False
    assert variables["gitlab_token"].secret is True
    assert variables["gitlab_token"].default == ""
    for jira_name in ("jira_base_url", "jira_project_key", "jira_credentials"):
        assert jira_name in variables, f"Jira variable {jira_name} must stay in the manifest"
    assert variables["jira_credentials"].secret is True

    assert "gitlab_com" in manifest.presets, "examples/pypost-library.yaml missing gitlab_com"
    assert manifest.presets["gitlab_com"] == {
        "gitlab_base_url": PLACEHOLDER_BASE_URL,
        "gitlab_project": PLACEHOLDER_PROJECT,
    }
    for preset_name, preset in manifest.presets.items():
        assert "gitlab_token" not in preset, f"preset {preset_name} must not carry the token"
    assert manifest.presets["jira_cloud"] == {
        "jira_base_url": "https://your-company.atlassian.net",
        "jira_project_key": "DEMO",
    }

    collection = _load_gitlab_collection()
    collection_secrets = {variable.name: variable.secret for variable in collection.variables}
    manifest_secrets = {name: variables[name].secret for name in GITLAB_ENV_KEYS}
    assert collection_secrets == manifest_secrets


def test_gitlab_library_manifest_project_default_matches_environment_placeholder(
    tmp_path, monkeypatch
):
    manifest = _load_manifest()
    variables = {variable.name: variable for variable in manifest.variables}
    assert "gitlab_project" in variables, (
        "examples/pypost-library.yaml missing variable gitlab_project"
    )
    default = variables["gitlab_project"].default
    assert isinstance(default, str) and default.strip(), "gitlab_project default must be set"

    environment = _load_gitlab_environment(tmp_path, monkeypatch)
    assert default == environment.variables["gitlab_project"] == PLACEHOLDER_PROJECT
    assert "gitlab_com" in manifest.presets, "examples/pypost-library.yaml missing gitlab_com"
    assert manifest.presets["gitlab_com"]["gitlab_project"] == default


_README_GITLAB_SECTIONS = (
    "Recommended import order (GitLab pair)",
    "GitLab authentication",
    "GitLab.com vs self-managed",
    "GitLab default project and identifiers",
    "GitLab coverage vs gaps",
)
_README_REQUIRED_TERMS = (
    "gitlab.json",
    "gitlab_token",
    "hidden",
    "read_api",
    "`api`",
    "self-managed",
    "not a security boundary",
    "IID",
    PLACEHOLDER_TOKEN,
    "make check-gitlab-mcp-path-freshness",
    "gitlab_com",
)


def test_gitlab_readme_documents_inventory_and_tool_parity():
    readme = EXAMPLES_README_PATH.read_text(encoding="utf-8")
    sections = {heading: _readme_section(readme, heading) for heading in _README_GITLAB_SECTIONS}
    missing_terms = [term for term in _README_REQUIRED_TERMS if term not in readme]
    assert not missing_terms, f"examples/README.md missing GitLab term(s): {missing_terms}"

    inventory = _readme_section(readme, "Standalone Inventory")
    assert "collections/gitlab_mcp.json" in inventory
    assert "collections/gitlab_mcp_rest_paths.json" in inventory
    assert "environments/gitlab.json" in inventory
    assert f"({GITLAB_TOOL_COUNT} REST tools)" in inventory

    library = _readme_section(readme, "Git Collection Library")
    assert "collections/gitlab_mcp.json" in library
    assert "gitlab_com" in library

    for tool in sorted(EXPECTED_GITLAB_TOOLS):
        assert tool in readme, f"examples/README.md does not mention {tool}"
    # Only tool-name shapes (all 25 locked tools use get/list/create/update), so prose
    # mentioning gitlab_mcp, gitlab_project or gitlab_token does not break parity.
    coverage_tools = set(
        re.findall(
            r"\bgitlab_(?:get|list|create|update)_[a-z_]+", sections["GitLab coverage vs gaps"]
        )
    )
    coverage_tools = {name.rstrip("_") for name in coverage_tools}
    catalog = _load_gitlab_catalog()
    catalog_tools = {entry["tool"] for entry in catalog["tools"]}
    assert coverage_tools == catalog_tools, (
        f"README coverage tools differ from catalog: "
        f"missing {sorted(catalog_tools - coverage_tools)}, "
        f"extra {sorted(coverage_tools - catalog_tools)}"
    )
    assert len(catalog_tools) == GITLAB_TOOL_COUNT
    collection = _load_gitlab_collection()
    assert len(collection.requests) == len(catalog["tools"]) == GITLAB_TOOL_COUNT


# ---------------------------------------------------------------------------
# 9. Secret hygiene
# ---------------------------------------------------------------------------

_SECRET_SCAN_PATHS = (
    GITLAB_COLLECTION_PATH,
    GITLAB_ENV_PATH,
    GITLAB_CATALOG_PATH,
    LIBRARY_MANIFEST_PATH,
    EXAMPLES_README_PATH,
)


def test_gitlab_fixtures_contain_no_real_tokens():
    missing = [
        str(path.relative_to(REPO_ROOT)) for path in _SECRET_SCAN_PATHS if not path.is_file()
    ]
    assert not missing, f"GitLab artifact(s) missing (PYPOST-1316): {missing}"
    for path in _SECRET_SCAN_PATHS:
        matches = find_gitlab_token_like_values(path.read_text(encoding="utf-8"))
        assert not matches, f"{path.relative_to(REPO_ROOT)} contains token-like value(s)"
    assert PLACEHOLDER_TOKEN in GITLAB_ENV_PATH.read_text(encoding="utf-8")


def test_gitlab_fixtures_secret_scan_rejects_glpat_like_value():
    """Mutation twin (green by design): the scanner flags a realistic token."""
    synthetic = '{"gitlab_token": "glpat-' + "A1b2C3d4E5f6G7h8I9j0" + '"}'
    assert find_gitlab_token_like_values(synthetic)
    assert not find_gitlab_token_like_values(f'{{"gitlab_token": "{PLACEHOLDER_TOKEN}"}}')
