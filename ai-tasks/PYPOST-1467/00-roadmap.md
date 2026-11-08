# Roadmap: PYPOST-1467 — IPC protocol version negotiation / reject mismatch

## Task Metadata

- **Implementation language**: Python

## Implementation Steps

- [x] **STEP 1: Requirements Gathering**
  - Documented business goals, user stories, acceptance criteria, failure containment, and
    scope boundaries in `ai-tasks/PYPOST-1467/10-requirements.md`.
- [x] **STEP 2: Architecture & Design**
  - Designed protocol version contracts (`MSG_V`, `SUPPORTED_MSG_VERSIONS`,
    `McpProtocolVersionError`, `validate_message_version`) in `20-architecture.md`.
  - Designed worker and supervisor ingress validation and deterministic mismatch rejection.
  - Specified automated acceptance tests for Step 3 in
    `tests/test_mcp_ipc_protocol_version_repro.py`.
- [x] **STEP 3: Failing Repro Test**
  - Implemented 5 red repro tests in `tests/test_mcp_ipc_protocol_version_repro.py`.
  - Asserted envelope version contracts, worker start rejection, worker runtime rejection,
    and supervisor ingress mismatch rejection during startup and running phases.
  - Verified 5/5 tests fail red against current codebase (/tmp/PYPOST-1467-step3-red.log).
- [x] **STEP 4: Development**
  - Implemented `SUPPORTED_MSG_VERSIONS`, `McpProtocolVersionError`, `validate_message_version`,
    and `VERSION_MISMATCH` MsgType in `pypost/core/mcp_worker_ipc.py`.
  - Added ingress version validation and lifecycle rejection handling
    (START_FAILED / WORKER_ERROR) in `pypost/core/mcp_worker_process.py`.
  - Added ingress version validation and starting/running phase rejection handling in
    `pypost/core/mcp_process_supervisor.py`.
  - Verified 5/5 repro tests pass green in `tests/test_mcp_ipc_protocol_version_repro.py`.
  - Verified MCP regression suites pass green and quality gates (`lint`, `typecheck`,
    `verify-ai-tasks`) succeed.
- [x] **STEP 5: Code Cleanup**
  - Verified all touched files (`pypost/core/mcp_worker_ipc.py`,
    `pypost/core/mcp_worker_process.py`, `pypost/core/mcp_process_supervisor.py`,
    `tests/test_mcp_ipc_protocol_version_repro.py`) adhere to PEP 8 / `lsr-python` import
    ordering, `<= 100` char line lengths, single trailing newlines, no trailing whitespace,
    and zero debug prints or dead code.
  - Confirmed all 5 acceptance tests in `tests/test_mcp_ipc_protocol_version_repro.py` have
    explicit `@pytest.mark.timeout` markers (20s or 30s) and module-level
    `pytestmark = pytest.mark.timeout(30)` per `do-testing`.
  - Documented cleanup actions and verification results in
    `ai-tasks/PYPOST-1467/40-code-cleanup.md`.
- [x] **STEP 6: Observability**
  - Documented structured logging events for IPC protocol version negotiation in
    `ai-tasks/PYPOST-1467/50-observability.md`.
  - Reviewed `mcp_worker_ipc_version_rejected` (WARNING) in `pypost/core/mcp_worker_process.py`
    and `mcp_supervisor_ipc_version_rejected` (ERROR) in
    `pypost/core/mcp_process_supervisor.py`.
  - Added caplog test coverage for worker startup and runtime mismatch rejection logging in
    `tests/test_mcp_ipc_protocol_version_repro.py`.
  - Validated secret safety, operational guidance, and zero lines exceeding 100 characters.
- [x] **STEP 7: Technical Debt Analysis**
  - Evaluated shortcuts taken, confirming frozenset version gating (`SUPPORTED_MSG_VERSIONS`)
    and fail-fast synchronous error reply handling without dynamic multi-version fallback.
  - Reviewed code quality, verifying boolean exclusion, structured `McpProtocolVersionError`
    typing, and full PEP 8 / `lsr-python` type annotations.
  - Verified all 7 repro tests in `tests/test_mcp_ipc_protocol_version_repro.py` declare explicit
    timeout markers (20s/30s) and bounded waits per `do-testing`.
  - Assessed performance impact, confirming O(1) dictionary and frozenset lookup with
    sub-microsecond overhead.
  - Documented pre-existing test lint finding (`tests/test_mcp_server_registry.py:308`) tracked in
    Jira as `PYPOST-1509` (`NON-BLOCKER — pre-existing`).
  - Confirmed zero blockers preventing closure and documented analysis in
    `ai-tasks/PYPOST-1467/60-tech-debt.md`.
- [x] **STEP 8: Dev Docs**
  - Updated `doc/dev/mcp_process_isolation.md` with dedicated subsection
    `### IPC protocol versioning and mismatch rejection (PYPOST-1467)`.
  - Documented envelope contracts (`MSG_V = 1`, `SUPPORTED_MSG_VERSIONS = frozenset({1})`),
    validation helper `validate_message_version`, and error class `McpProtocolVersionError`.
  - Documented worker pre-START `START_FAILED` and runtime command `WORKER_ERROR` rejection
    semantics.
  - Documented supervisor starting `failed` transition and running message discard semantics.
  - Documented observability events table (`mcp_worker_ipc_version_rejected`,
    `mcp_supervisor_ipc_version_rejected`), secret safety, and troubleshooting guidance.
  - Verified every line added or updated in `doc/dev/mcp_process_isolation.md` is `<= 100`
    characters.
  - Verified documentation links and quality gates (`make -o lint-tests lint`,
    `make verify-ai-tasks`).
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1467/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1467/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_mcp_ipc_protocol_version_repro.py`

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1467/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1467/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1467/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/mcp_process_isolation.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are
  reported in chat only, never written to this file.
