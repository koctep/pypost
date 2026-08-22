# Roadmap: PYPOST-1132

## Task Metadata

- **Implementation language**: Python
- **Branch name**: feature/PYPOST-1132-websocket-client-ui-inspector

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_websocket_client_ui_repro.py`
- [x] **STEP 4: Development**
  - [x] Defined all `WS_*` stable UI identity constants in `pypost/ui/widget_ids.py` and exported in `KEY_WIDGET_IDS`
  - [x] Implemented `WebSocketStateBadge` with multi-modal glyphs, text status, metric counts, and tooltips
  - [x] Implemented `WebSocketConnectionEditor` with URL input, tabs for params/headers (`WebSocketKeyValueTable`), subprotocols input, dynamic read-only locking, and `WS_LOCK_NOTICE` banner
  - [x] Implemented `WebSocketPresenter` with 33ms batch queue ingestion, secret masking, state machine synchronization, and send validation
  - [x] Implemented `WebSocketTab` integrating header status bar, connection editor, stream `QListView`, and composer
  - [x] Integrated `WebSocketTab` lifecycle in `TabsPresenter` (open, focus duplicate, close with teardown, idle-safe startup restore, secret propagation) under LOC cap
  - [x] Integrated collection-tree profile rendering and opening in `CollectionsPresenter` and `CollectionTreeIncremental`
  - [x] Extended `tests/test_ui_identity_spotcheck.py` to verify `WS_*` objectNames
  - [x] Implemented loopback end-to-end integration test in `tests/test_agent_e2e_websocket.py`
  - [x] Verified all unit repro tests, e2e tests, and full test suite pass (`make test-agent-e2e`, `make lint`, `audit_baseline_metrics`)
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Technical Debt Analysis**
- [x] **STEP 8: Dev Docs**
  - [x] Documented WebSocket UI Client and Live Stream Inspector in `doc/dev/websocket_ui_client.md`
  - [x] Updated `doc/dev/README.md` index
  - [x] Synchronized `doc/dev/agent_e2e.md` harness table with `tests/test_agent_e2e_websocket.py`
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1132/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1132/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1132/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1132/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1132/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/websocket_ui_client.md`
- `doc/dev/README.md`
- `doc/dev/agent_e2e.md`

### COMMIT

- Commit hash: `233e6f75`
- Message: `feat(websocket): PYPOST-1132 interactive WebSocket UI client and live stream inspector`
- Branch: `feature/PYPOST-1132-websocket-client-ui-inspector`
