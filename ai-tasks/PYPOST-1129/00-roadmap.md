# Roadmap: PYPOST-1129

## Task Metadata

- **Implementation language**: Python
- **Branch name**: *[recorded by the commit procedure — reference only, do not switch]*

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] Gather requirements and document business scope in `ai-tasks/PYPOST-1129/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - [x] Research QtWebSockets test server architecture and requirements
  - [x] Design ScriptedWebSocketServer with configurable ServerBehavior enum
  - [x] Design pytest fixture ws_test_server with bounded lifecycle management
  - [x] Design ui_wait integration and deterministic polling helpers
  - [x] Design responsiveness/flood test and offscreen test suite
  - [x] Document failing repro design for Step 3 and complete `ai-tasks/PYPOST-1129/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - [x] Failing repro test suite: `tests/test_websocket_echo_server.py`
- [x] **STEP 4: Development**
  - [x] Implement ServerBehavior enum and ServerBehaviorConfig dataclass in tests/websocket_echo_server.py
  - [x] Implement ScriptedWebSocketServer in tests/websocket_echo_server.py
  - [x] Register ws_test_server fixture in tests/conftest.py
  - [x] Run and verify test suite and static analysis
- [x] **STEP 5: Code Cleanup**
  - [x] Run static analysis and formatting checks (flake8, mypy, line length <= 100)
  - [x] Verify explicit timeout markers and bounded waits across all test files
  - [x] Create cleanup report in `ai-tasks/PYPOST-1129/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - [x] Implement structured debug logging in `tests/websocket_echo_server.py`
  - [x] Expose real-time diagnostic properties and tracking counters
  - [x] Add verification tests in `tests/test_websocket_echo_server.py`
  - [x] Create observability report in `ai-tasks/PYPOST-1129/50-observability.md`
- [x] **STEP 7: Technical Debt Analysis**
  - [x] Analyze shortcuts, missing tests, and performance considerations
  - [x] Document non-blocking follow-up tasks and dependencies
  - [x] Create technical debt report in `ai-tasks/PYPOST-1129/60-tech-debt.md`
- [x] **STEP 8: Dev Docs**
  - [x] Create developer documentation `doc/dev/websocket_test_harness.md` covering offline test server, scripted behaviors, fixture usage, bounded synchronization, observability, and troubleshooting
  - [x] Update `doc/dev/README.md` table of contents with link to `websocket_test_harness.md`
- [x] **COMMIT: Commit Changes**
  - [x] Commit hash: `deae72bd`
  - [x] Suggested branch: `task/PYPOST-1129-websocket-test-harness`

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1129/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1129/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1129/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1129/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1129/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/websocket_test_harness.md`
- `doc/dev/README.md`

### COMMIT

- Commit hash and message (Conventional Commits + JIRA ID)
