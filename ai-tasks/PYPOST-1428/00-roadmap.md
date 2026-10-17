# Roadmap: PYPOST-1428

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] Determine implementation language (Python) and initialize roadmap
  - [x] Gather business problem context and technical debt reduction rationale
  - [x] Define user stories, acceptance criteria, definition of done, and Q&A
  - [x] Acceptance gate review PASS
- [x] **STEP 2: High-Level Architecture Design**
  - [x] Research existing wire client implementation and test helpers patterns
  - [x] Design module structure, Mermaid architecture diagrams, and API contracts
  - [x] Specify Step 3 failing repro test strategy (tests/test_raw_tcp_client_helper.py)
  - [x] Document high-level implementation plan and design decisions
  - [x] Acceptance gate review PASS
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_raw_tcp_client_helper.py` (fails with ModuleNotFoundError: No module named 'tests.helpers.raw_tcp_client')
  - [x] Acceptance gate review PASS
- [x] **STEP 4: Development**
  - [x] Iteration 1: Create `tests/helpers/raw_tcp_client.py` implementing `RawTcpWireClient` and `parse_jsonrpc_from_response`
  - [x] Iteration 1: Make Step 3 red repro test (`tests/test_raw_tcp_client_helper.py`) go GREEN
  - [x] Iteration 2: Refactor `tests/test_mcp_standalone_wire_ipc_repro.py` to import from `tests.helpers.raw_tcp_client` and remove redundant class/function definitions
  - [x] Iteration 2: Verify both test suites pass (`tests/test_raw_tcp_client_helper.py` and `tests/test_mcp_standalone_wire_ipc_repro.py`)
  - [x] Run static analysis and validation (`make lint`, `make typecheck`, `make verify-ai-tasks`)
  - [x] Acceptance gate review PASS
- [x] **STEP 5: Code Cleanup**
  - [x] Run static analysis and linter checks (`make lint`, `make typecheck`)
  - [x] Verify line lengths (<= 100 chars), formatting, clean imports, absence of unused code/variables/debug prints
  - [x] Verify explicit timeout markers on tests per `do-testing` (`pytestmark = pytest.mark.timeout(30)`)
  - [x] Run tests to confirm all pass (`make test PYTEST_ARGS="tests/test_raw_tcp_client_helper.py tests/test_mcp_standalone_wire_ipc_repro.py"`)
  - [x] Verify AI task artifacts integrity (`make verify-ai-tasks`)
  - [x] Created `ai-tasks/PYPOST-1428/40-code-cleanup.md`
  - [x] Acceptance gate review PASS
- [x] **STEP 6: Observability**
  - [x] Audit observability and diagnostics design for shared test utility `tests/helpers/raw_tcp_client.py`
  - [x] Verify deterministic exception raising (`ConnectionResetError`, `socket.timeout`, graceful `OSError` suppression)
  - [x] Verify zero leakage of credentials, auth tokens, or oversized bodies
  - [x] Document logging structure, syslog severity mapping, and metrics applicability
  - [x] Create `ai-tasks/PYPOST-1428/50-observability.md`
  - [x] Acceptance gate review PASS
- [x] **STEP 7: Technical Debt Analysis**
  - [x] Analyze extracted `RawTcpWireClient` and test harness for shortcuts, code quality, missing tests, and performance
  - [x] Catalog follow-up tasks with links to Jira tickets (PYPOST-1430, PYPOST-1431, PYPOST-1432)
  - [x] Classify all items as NON-BLOCKER (no blocking debt for PYPOST-1428)
  - [x] Create `ai-tasks/PYPOST-1428/60-tech-debt.md`
  - [x] Verify task artifacts with `make verify-ai-tasks`
  - [x] Acceptance gate review PASS
- [x] **STEP 8: Dev Docs**
  - [x] Inspect and update `doc/dev/mcp_standalone_wire_ipc_stress.md` to document the shared helper `tests/helpers/raw_tcp_client.py`
  - [x] Document `RawTcpWireClient` and `parse_jsonrpc_from_response` (overview, methods, parameters, return types, usage patterns in tests)
  - [x] Update references in `doc/dev/mcp_server_registry.md`
  - [x] Validate markdown linting and relative links (`make lint-docs`, `scripts/lint_user_docs.py`, `scripts/check_user_docs_links.py`)
  - [x] Verify task artifacts integrity (`make verify-ai-tasks`)
  - [x] Acceptance gate review PASS
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1428/00-roadmap.md`
- `ai-tasks/PYPOST-1428/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1428/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1428/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1428/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1428/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/mcp_standalone_wire_ipc_stress.md`
- `doc/dev/mcp_server_registry.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
