# Roadmap: PYPOST-1137

## Task Metadata

- **Implementation language**: Python
- **Branch name**: `feature/PYPOST-1137-bounded-mcp-websocket-probe-tool`

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] `ai-tasks/PYPOST-1137/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - [x] `ai-tasks/PYPOST-1137/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_websocket_mcp_probe_repro.py`
- [x] **STEP 4: Development**
  - [x] Iteration 1: `pypost/core/websocket_probe.py` — Qt-free domain models, stopping condition evaluator, limit clamping, transcript formatter
  - [x] Iteration 2: `pypost/core/qt/websocket_probe_runner.py` — QThread with QEventLoop, hard deadline QTimer, SessionSlots, guaranteed termination
  - [x] Iteration 3: `pypost/core/websocket_mcp_tools.py` — Schema generation, secret isolation, contract preview, execution bridge
  - [x] Iteration 4: `pypost/core/mcp_server_impl.py` — Delegating seam, AppSettings injection, within 325 LOC cap
  - [x] Iteration 5: `pypost/core/websocket_session_policy.py` — Added `is_full` property to `SessionSlots`
  - [x] Iteration 6: `pypost/core/daemon_storage.py` — Collection.websockets already loaded by model_validate (no code change needed)
  - [x] Iteration 7: `pypost/ui/widgets/websocket/connection_editor.py` — MCP preview sub-tab wired
  - [x] Iteration 8: Run test suite, audit baseline metrics, and static checks (19/19 repro tests passed, flake8 clean)
- [x] **STEP 5: Code Cleanup**
  - [x] `ai-tasks/PYPOST-1137/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - [x] `ai-tasks/PYPOST-1137/50-observability.md`
- [x] **STEP 7: Technical Debt Analysis**
  - [x] `ai-tasks/PYPOST-1137/60-tech-debt.md`
- [x] **STEP 8: Dev Docs**
  - [x] `doc/dev/websocket_mcp_probe_tool.md`
- [x] **COMMIT: Commit Changes**
  - Commit: `7868a54c` (`feat(websocket): PYPOST-1137 bounded MCP WebSocket probe tool`)

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1137/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1137/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1137/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1137/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1137/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- Commit hash and message (Conventional Commits + JIRA ID)
