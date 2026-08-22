# Roadmap: PYPOST-1128

## Task Metadata

- **Implementation language**: Python
- **Branch name**: feature/PYPOST-1128-websocket-connection-profile-persistence

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] `ai-tasks/PYPOST-1128/00-roadmap.md` — task progress journal and implementation language recorded.
  - [x] `ai-tasks/PYPOST-1128/10-requirements.md` — business and functional requirements for WebSocket connection profile model, persistence, and collection interchange.
- [x] **STEP 2: High-Level Architecture Design**
  - [x] `ai-tasks/PYPOST-1128/20-architecture.md` — system module diagram, domain models, registry index, item dispatch, export/import interchange, and failing repro plan.
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_websocket_models_and_persistence.py` — automated red test suite asserting WebSocket domain models, Collection.websockets persistence, WebSocketRegistry, item dispatch, export/import interchange, and storage invariance.
- [x] **STEP 4: Development**
  - [x] Implemented WebSocket domain models in `pypost/models/websocket.py` with validation and 6 MCP tool metadata fields (`expose_as_mcp`, `mcp_description`, `mcp_params`, `mcp_probe_preset_id`, `mcp_probe_max_messages`, `mcp_probe_max_duration_ms`).
  - [x] Extended `Collection` model with `websockets: List[WebSocketConnection] = Field(default_factory=list)` in `pypost/models/models.py`.
  - [x] Implemented `WebSocketRegistry` in `pypost/core/websocket_registry.py` with in-memory cross-collection indexing, CRUD operations, and O(1) kind-aware `find_item`.
  - [x] Extracted item-type dispatch to `pypost/core/collection_item_dispatch.py` and updated `pypost/core/request_manager.py` to keep it strictly under its LOC cap (240 LOC vs 264 cap).
  - [x] Registered `"websocket"` strategy in `pypost/core/collection_item_strategies.py`.
  - [x] Added export and import support for WebSocket profiles in `pypost/core/collection_export.py`, `pypost/core/collection_import.py`, and `pypost/core/collection_messages.py` with ID reservation/re-keying, separate summary counts, and template preservation.
  - [x] Verified `pypost/core/storage.py` is unchanged and verified collection persistence invariance.
  - [x] Registered file caps in `scripts/audit_baseline_metrics.py` and updated `ai-tasks/PYPOST-376/baseline-metrics.md`.
  - [x] All 20 tests in `tests/test_websocket_models_and_persistence.py` green, flake8 0 errors, baseline metrics audit clean.
- [x] **STEP 5: Code Cleanup**
  - [x] `ai-tasks/PYPOST-1128/40-code-cleanup.md` — static analysis, timeout markers, formatting, and test validation.
- [x] **STEP 6: Observability**
  - [x] `ai-tasks/PYPOST-1128/50-observability.md` — structured logging, metrics, and health observability documentation.
- [x] **STEP 7: Technical Debt Analysis**
  - [x] `ai-tasks/PYPOST-1128/60-tech-debt.md` — technical debt evaluation, trade-off analysis, performance limits, and follow-up workstreams.
- [x] **STEP 8: Dev Docs**
  - [x] `doc/dev/websocket_persistence_and_interchange.md` — developer guide covering domain models, Collection.websockets, WebSocketRegistry, item dispatch, export/import interchange, and troubleshooting.
  - [x] `doc/dev/README.md` — indexed new developer documentation.
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1128/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1128/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_websocket_models_and_persistence.py`

### STEP 4: Development

- `pypost/models/websocket.py`
- `pypost/models/models.py`
- `pypost/core/websocket_registry.py`
- `pypost/core/collection_item_dispatch.py`
- `pypost/core/collection_item_strategies.py`
- `pypost/core/collection_export.py`
- `pypost/core/collection_import.py`
- `pypost/core/collection_messages.py`
- `scripts/audit_baseline_metrics.py`
- `ai-tasks/PYPOST-376/baseline-metrics.md`

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1128/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1128/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1128/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/websocket_persistence_and_interchange.md`
- `doc/dev/README.md`

### COMMIT

- `feat(websocket): PYPOST-1128 implement connection profile model and persistence`
