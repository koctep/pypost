# Roadmap: PYPOST-1193

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1193/10-requirements.md`
  - Language: Python
  - Business goal: restore reliable delete and rename of collection items
    (including type-based routing and empty-name rejection) so users keep a
    working collections workflow and CI trusts the named regression checks
  - Pre-existing suite reds from PYPOST-1192 triage at base `18a4d9d1`
    (NON-BLOCKER); Sprint: Suite Failures Cleanup
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1193/20-architecture.md`
  - Root cause: `_unpack_context` returns 3-tuple; collection/request
    handlers unpack as 2 → `ValueError` on delete/rename dispatch
  - Fix shape: align collection/request handler unpack to 3-tuple; keep
    Strategy + Dispatch Context; no API redesign
  - Step 3 plan: confirm existing five named tests red before production fix
- [x] **STEP 3: Failing Repro Test**
  - N/A — no new test; architecture: confirm five existing named tests red
  - Repro command: `make test PYTEST_ARGS="tests/test_collection_item_strategies.py tests/test_request_manager_delete.py"` (exit 1)
  - Confirmed red (5/5), failure mode `ValueError: too many values to unpack (expected 2)` in `collection_item_strategies.py` handlers:
    - `tests/test_collection_item_strategies.py::CollectionItemStrategiesTests::test_builtin_strategies_delegate_to_request_manager_methods` (`_request_delete`)
    - `tests/test_request_manager_delete.py::RequestManagerDeleteTests::test_delete_collection_item_routes_by_type` (`_request_delete`)
    - `tests/test_request_manager_delete.py::RequestManagerDeleteTests::test_delete_collection_item_routes_collection_type` (`_collection_delete`)
    - `tests/test_request_manager_delete.py::RequestManagerDeleteTests::test_rename_collection_item_rejects_empty_name` (`_request_rename`)
    - `tests/test_request_manager_delete.py::RequestManagerDeleteTests::test_rename_collection_item_routes_collection_type` (`_collection_rename`)
  - No production code changed; no new test file (coverage gap: none)
- [x] **STEP 4: Development**
  - [x] Aligned collection/request handler unpack to 3-tuple (`manager, _, _`) in `pypost/core/collection_item_strategies.py` (`_collection_delete` / `_collection_rename` / `_request_delete` / `_request_rename`)
  - [x] Repro green: `make test PYTEST_ARGS="tests/test_collection_item_strategies.py tests/test_request_manager_delete.py"` (5/5 named regressions pass)
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1193/40-code-cleanup.md`
  - Scope: 4-line unpack fix in `pypost/core/collection_item_strategies.py`
  - `make lint` clean; scoped regression tests green; no unused imports/dead code
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1193/50-observability.md`
  - N/A — no new logging/metrics; 4-line unpack arity fix only; existing
    dispatch telemetry in `collection_item_dispatch.py` unchanged
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1193/60-tech-debt.md`
  - Minimal 4-line unpack fix; no AC-breaking debt; optional attribute-only
    hardening noted; sibling suite reds remain out of scope (already ticketed)
- [x] **STEP 8: Dev Docs**
  - Added `doc/dev/collection_item_strategies.md` — ItemDispatchContext /
    `_unpack_context` **3-tuple** contract for collection/request (and
    websocket/MCP) strategy handlers
  - Cross-links + troubleshooting in `collection_item_delete.md`,
    `collection_item_rename.md`; TOC entry in `doc/dev/README.md`
  - Updated stale 2-field context snippet in
    `websocket_persistence_and_interchange.md` (add `mcp_client_registry` +
    unpack note)
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1193/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1193/20-architecture.md`

### STEP 3: Failing Repro

- Existing red suite confirmed (no new test):
  - `tests/test_collection_item_strategies.py::CollectionItemStrategiesTests::test_builtin_strategies_delegate_to_request_manager_methods`
  - `tests/test_request_manager_delete.py::RequestManagerDeleteTests::test_delete_collection_item_routes_by_type`
  - `tests/test_request_manager_delete.py::RequestManagerDeleteTests::test_delete_collection_item_routes_collection_type`
  - `tests/test_request_manager_delete.py::RequestManagerDeleteTests::test_rename_collection_item_rejects_empty_name`
  - `tests/test_request_manager_delete.py::RequestManagerDeleteTests::test_rename_collection_item_routes_collection_type`

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1193/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1193/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1193/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/collection_item_strategies.md` (new — 3-tuple unpack contract)
- `doc/dev/collection_item_delete.md` / `collection_item_rename.md` (cross-links)
- `doc/dev/README.md` (TOC)
- `doc/dev/websocket_persistence_and_interchange.md` (context fields + unpack note)

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
