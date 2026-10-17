# Roadmap: PYPOST-1429

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] Identify business goals and technical debt reduction rationale
  - [x] Formulate user stories, acceptance criteria, definition of done, and Q&A
  - [x] Acceptance gate review PASS
- [x] **STEP 2: High-Level Architecture Design**
  - [x] Design McpStdioHarness module architecture, lifecycle, and thread management
  - [x] Define API contract for process execution, stream draining, and response registry
  - [x] Specify Step 3 automated failing repro test in tests/test_mcp_stdio_harness.py
  - [x] Document architectural decisions, pipe deadlock prevention, and Q&A in 20-architecture.md
  - [x] Acceptance gate review PASS
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_mcp_stdio_harness.py` (fails with ModuleNotFoundError: No module named 'tests.helpers.mcp_stdio_harness')
  - [x] Acceptance gate review PASS
- [x] **STEP 4: Development**
  - [x] Iteration 1: Implement `McpStdioHarness` in `tests/helpers/mcp_stdio_harness.py` with asynchronous stream draining and condition synchronization (Step 3 repro tests pass)
  - [x] Iteration 2: Refactor `test_stdio_subprocess_ipc_large_payload_and_burst` in `tests/test_mcp_standalone_wire_ipc_repro.py` to consume `McpStdioHarness`
  - [x] Acceptance gate review PASS
- [x] **STEP 5: Code Cleanup**
  - [x] Run static analysis and linter checks (`make lint`, `make typecheck`)
  - [x] Verify line lengths (<= 100 chars), formatting, clean imports, absence of unused code/variables/debug prints
  - [x] Verify explicit timeout markers on tests per `do-testing` (`pytestmark = pytest.mark.timeout(30)`)
  - [x] Run tests to confirm all pass (`make test PYTEST_ARGS="tests/test_mcp_stdio_harness.py tests/test_mcp_standalone_wire_ipc_repro.py"`)
  - [x] Verify AI task artifacts integrity (`make verify-ai-tasks`)
  - [x] Created `ai-tasks/PYPOST-1429/40-code-cleanup.md`
  - [x] Acceptance gate review PASS
- [x] **STEP 6: Observability**
  - [x] Perform observability audit for `tests/helpers/mcp_stdio_harness.py`
  - [x] Audit exception design, timeout diagnostics, and stderr context attachment
  - [x] Verify zero leakage of credentials/tokens or oversized raw binary dumps
  - [x] Document logging structure, syslog mapping, metrics applicability in `ai-tasks/PYPOST-1429/50-observability.md`
  - [x] Acceptance gate review PASS
- [x] **STEP 7: Technical Debt Analysis**
  - [x] Analyze shortcuts taken, code quality issues, missing tests, and performance concerns
  - [x] Link sprint follow-up issues (PYPOST-1433, PYPOST-1434, PYPOST-1430, PYPOST-1435) with non-blocker classification
  - [x] Create `ai-tasks/PYPOST-1429/60-tech-debt.md`
  - [x] Acceptance gate review PASS
- [x] **STEP 8: Dev Docs**
  - [x] Update Overview and Mermaid diagram in doc/dev/mcp_standalone_wire_ipc_stress.md
  - [x] Add dedicated McpStdioHarness architectural design and API reference
  - [x] Add test suite usage examples (context manager, burst correlation, timeout handling)
  - [x] Validate doc linting and link integrity (make lint-docs, make verify-ai-tasks)
  - [x] Acceptance gate review PASS
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1429/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1429/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1429/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1429/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1429/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/mcp_standalone_wire_ipc_stress.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
