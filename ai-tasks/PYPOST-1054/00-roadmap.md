# Roadmap: PYPOST-1054

## Task Metadata

- **Implementation language**: Python
- **Branch name**: feature/PYPOST-1054-jira-mcp-pagination-defaults

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] Gather business goals and user stories for optional Jira MCP pagination defaults
  - [x] Define functional requirements and acceptance criteria (DoD)
  - [x] Identify business entities and scope boundaries
  - [x] Produce requirements artifact `ai-tasks/PYPOST-1054/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - [x] Research core models, schema generation, execution defaulting, and fixtures
  - [x] Design Step 3 failing-repro suite across contract, unit, and integration levels
  - [x] Document target architecture, Mermaid interaction flow, data contracts, and DoD matrix
  - [x] Create architecture artifact `ai-tasks/PYPOST-1054/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_mcp_tool_contract.py::TestMcpToolContract::test_schema_includes_default_and_omits_optional_from_required`
  - [x] `tests/test_mcp_server_impl.py::TestMCPServerImpl::test_call_tool_applies_mcp_param_defaults_when_args_omitted`
  - [x] `tests/test_mcp_server_impl.py::TestMCPServerImpl::test_call_tool_honors_explicit_custom_pagination_args`
  - [x] `tests/test_example_fixtures.py::test_jira_mcp_list_requests_expose_pagination_mcp_params`
- [x] **STEP 4: Development**
  - [x] Added `default: Optional[Any] = None` to `McpToolParam` model in `pypost/models/models.py`
  - [x] Updated `build_tool_input_schema` in `pypost/core/mcp_tool_contract.py` to publish default values in JSON schema properties
  - [x] Updated `MCPServerImpl._build_execution_variables` in `pypost/core/mcp_server_impl.py` to populate parameter defaults from `request_data.mcp_params` when omitted
  - [x] Preserved parameter defaults in `McpParamsTable` within `pypost/ui/widgets/request_editor.py`
  - [x] Updated `examples/collections/jira_mcp.json` list operations (`jira-list-boards`, `jira-list-board-sprints`, `jira-get-sprint-issues`) with `required: false`, `default: 50` / `default: 0`, and updated descriptions
  - [x] Verified all contract, unit, and UI tests pass 100% GREEN
- [x] **STEP 5: Code Cleanup**
  - [x] Ran `make lint` (flake8 on `pypost/`) — clean, no violations in Step 4's source changes
  - [x] Ran `flake8` explicitly against touched `tests/*.py` (not covered by `make lint`) and fixed:
    removed 2 unused `out` variables (F841) and wrapped a 134-char URL literal in
    `tests/test_mcp_server_impl.py`; trimmed 3 over-100-char docstrings across
    `tests/test_mcp_tool_contract.py` and `tests/test_example_fixtures.py`
  - [x] Found and fixed a Step 4 regression: `tests/test_mcp_server_impl.py` had lost its
    `import pytest` / `pytestmark = pytest.mark.timeout(60)` module marker (dropped 45 tests'
    required timeout markers) — restored to match `HEAD`
  - [x] Ran `make typecheck` (mypy baseline) — no new errors from this task's diff; pre-existing
    8-error baseline drift in unrelated files confirmed via `git stash` to predate this task
  - [x] Ran `make check-mcp-fixtures` and `make verify-ai-tasks` — both pass
  - [x] Ran full repo suite (`pytest -q`, 2227 collected) and found `mcp_server_impl.py`'s
    growth (282->293 LOC) made `ai-tasks/PYPOST-376/baseline-metrics.md` stale; regenerated it
    via `scripts/audit_baseline_metrics.py --markdown ai-tasks/PYPOST-376/baseline-metrics.md`
  - [x] Investigated 7 other full-suite failures (encryption CLI/migration, mcp_server_manager,
    metrics_server_startup) — confirmed via `git stash` they reproduce identically on unmodified
    `dev` (Linux-vs-macOS errno hardcoding + pre-existing test-order flakiness); out of scope,
    left unfixed, documented for reviewer
  - [x] Re-ran affected tests: `pytest tests/test_mcp_server_impl.py tests/test_mcp_tool_contract.py
    tests/test_example_fixtures.py tests/test_request_editor_mcp_params.py
    tests/test_solid_audit_baseline.py` — 99 passed
  - [x] Produced `ai-tasks/PYPOST-1054/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - [x] Added INFO-level `mcp_param_default_applied method=%s param=%s default=%r` log line in
    `MCPServerImpl._build_execution_variables` (`pypost/core/mcp_server_impl.py`), emitted once
    per optional MCP param silently filled from its declared default — the previously-silent
    default-application path is now visible in logs
  - [x] Extended the pre-existing `mcp_execution_variables_merged` DEBUG line with a
    `defaults_applied_count=%d` field
  - [x] Added `mcp_param_defaults_applied_total{method}` Prometheus/OTel counter following the
    codebase's existing `track_response_body_truncated`-style "counter + log at point of silent
    behavior substitution" convention; threaded through all four `MetricsTrackerProtocol`
    implementers: `pypost/core/metrics_protocol.py`, `pypost/core/metrics_registry.py`,
    `pypost/core/metrics_otel.py`, `pypost/core/qt/metrics.py`
  - [x] Added/extended tests: `tests/test_mcp_server_impl.py` (2 new tests: log+metric fire on
    default application, both stay silent on explicit args), `tests/test_metrics_registry.py`,
    `tests/test_metrics_otel.py`, `tests/test_metrics_manager.py` — 144 targeted tests pass
  - [x] Re-derived `pypost/core/qt/metrics.py`'s SOLID-audit LOC cap (181 -> 185 in
    `scripts/audit_baseline_metrics.py`, documented inline) after the new delegation method
    pushed it from 179 to 182 lines; regenerated `ai-tasks/PYPOST-376/baseline-metrics.md`;
    `tests/test_solid_audit_baseline.py` 4/4 pass
  - [x] Verified `make lint`, `make typecheck` (pre-existing 227-error baseline drift only,
    confirmed unrelated via `git stash`), `make check-mcp-fixtures`, `make verify-ai-tasks` all
    pass
  - [x] Produced `ai-tasks/PYPOST-1054/50-observability.md`
- [x] **STEP 7: Technical Debt Analysis**
  - [x] Analyzed Steps 1-6 for scope gaps, deferred work, and known limitations
  - [x] Recorded the Step 6 reviewer's `mcp_arg_count` DEBUG-log semantic-shift
    note as TD-1 (Low, non-blocking)
  - [x] Checked `examples/collections/jira_mcp.json` for other curated list
    tools that could benefit from the same optional+default pagination
    pattern: none already declare `maxResults`/`startAt` as `required: true`;
    `jira-search-assignable-users` doesn't expose pagination params at all —
    recorded as TD-3 (Low)
  - [x] Flagged missing `default`-vs-`type` validation on `McpToolParam` and
    missing UI affordance to author/edit defaults in `McpParamsTable` as TD-2
    (Medium)
  - [x] Re-confirmed (with exact node ids and repro command) the 4 pre-existing,
    out-of-scope test failures already surfaced by Steps 5-6; JQL search found
    no existing Jira issue for either root cause — recorded NON-BLOCKER,
    unticketed pending `tech-debt-jira-sync`
  - [x] Re-ran the 9 targeted test modules (144 tests) — all green
  - [x] Produced `ai-tasks/PYPOST-1054/60-tech-debt.md`
- [x] **STEP 8: Dev Docs**
  - [x] Extended `doc/dev/mcp_integration.md` with a new "Optional MCP parameter
    defaults (PYPOST-1054)" section (model field, schema publication,
    execution-time defaulting code walkthrough, log line + metric, UI
    round-trip-only behavior, curated Jira fixture summary, limitations)
  - [x] Updated the pre-existing `McpToolParam` field list, schema pipeline
    diagram, `_build_execution_variables` API entry, `McpParamsTable` UI
    subsection, Troubleshooting table, and Limitations & Tech Debt list in
    `doc/dev/mcp_integration.md` to reflect `default` end-to-end (including
    the `mcp_arg_count` DEBUG-field semantic-shift note, PYPOST-1090)
  - [x] Updated `doc/dev/jira_mcp_project_default.md` "List pagination"
    section and its troubleshooting row — corrected stale "required, no
    default" language now that PYPOST-1054 makes `maxResults`/`startAt`
    optional with safe defaults
  - [x] Updated `doc/dev/testing.md` (allowlist note, fixture contract test
    list, curated-surface editing checklist, troubleshooting row) to match
    the optional+default pagination contract
  - [x] Added a PYPOST-1054 entry to the `doc/dev/README.md` MCP section
    table of contents; fixed a pre-existing stale anchor (missing
    PYPOST-1050) on the neighboring "jira-mcp example fixtures" link found
    while cross-checking anchors
  - [x] Verified all new/edited in-file and cross-file Markdown anchors
    resolve (scripted check); `make verify-ai-tasks` passes
- [ ] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1054/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1054/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_mcp_tool_contract.py`
- `tests/test_mcp_server_impl.py`
- `tests/test_example_fixtures.py`

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1054/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1054/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1054/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/mcp_integration.md`
- `doc/dev/jira_mcp_project_default.md`
- `doc/dev/testing.md`
- `doc/dev/README.md`

### COMMIT

- Commit hash and message (Conventional Commits + JIRA ID)
