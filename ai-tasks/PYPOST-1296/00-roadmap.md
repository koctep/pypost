# Roadmap: PYPOST-1296

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] Determine implementation language (Python)
  - [x] Gather requirements from issue description and parent task PYPOST-1285
  - [x] `ai-tasks/PYPOST-1296/10-requirements.md` drafted and accepted by review
- [x] **STEP 2: High-Level Architecture Design**
  - [x] Research `WebSocketPresenter`, `tabs_presenter_hotkeys.py`, and test patch sites
  - [x] Design public `toggle_connection()`, renamed router functions, and test updates
  - [x] Implementation Plan with failing-repro design for Step 3
  - [x] `ai-tasks/PYPOST-1296/20-architecture.md` accepted by review
- [x] **STEP 3: Failing Repro Test**
  - [x] Write failing repro test asserting `WebSocketPresenter.toggle_connection` and router naming
  - [x] Verify automated failure reproduces the deficiency
  - [x] Step 3 review accepted
- [x] **STEP 4: Development**
  - [x] Add public `toggle_connection()` to `WebSocketPresenter`; alias `_on_connect_clicked`
  - [x] Rename routers to `handle_websocket_connect_toggle` & `handle_mcp_client_connect_toggle`
  - [x] Update `tabs_presenter_hotkeys.py` to call `toggle_connection()`
  - [x] Update tests in `tests/test_main_window_hotkeys.py` to patch `toggle_connection`
  - [x] Verify all tests pass green
  - [x] Step 4 review accepted
- [x] **STEP 5: Code Cleanup**
  - [x] Static analysis and formatting verified (`make lint`, all lines <= 100 chars)
  - [x] Code cleanup verified (0 unused imports, 0 debug prints)
  - [x] Test suite passing and timeout markers verified
  - [x] `ai-tasks/PYPOST-1296/40-code-cleanup.md` created
  - [x] Step 5 review accepted
- [x] **STEP 6: Observability**
  - [x] Analyze observability requirements (structured hotkey routing logs preserved)
  - [x] Create `ai-tasks/PYPOST-1296/50-observability.md`
  - [x] Step 6 review accepted
- [x] **STEP 7: Technical Debt Analysis**
  - [x] Analyze codebase changes for technical debt, shortcuts, and missing tests
  - [x] Create `ai-tasks/PYPOST-1296/60-tech-debt.md`
  - [x] Step 7 review accepted
  - [x] Phase C blocker review accepted (SAFE TO CLOSE)
- [x] **STEP 8: Dev Docs**
  - [x] Update `doc/dev/websocket_hotkeys.md`, `doc/dev/mcp_client_hotkeys.md`,
    and `doc/dev/hotkeys.md`
  - [x] Step 8 review accepted
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1296/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1296/20-architecture.md`

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1296/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1296/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1296/60-tech-debt.md`
