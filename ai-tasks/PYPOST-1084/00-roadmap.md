# Roadmap: PYPOST-1084

## Task Metadata

- **Implementation language**: Python
- **Branch name**: `refactoring/PYPOST-1084-inject-collection-lookup`

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1084/00-roadmap.md`
  - `ai-tasks/PYPOST-1084/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1084/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - Added `test_collection_lookup_passed_to_registry` in `tests/test_mcp_server_controller.py`; failed with `TypeError` before implementation.
- [x] **STEP 4: Development**
  - `pypost/ui/mcp_server_controller.py`: Injected `collection_lookup: Callable[[str], Collection | None]`, dropped `collections_provider`, `get_collections`, and `_collection_by_id`.
  - Updated `for_window` factory and test doubles in `tests/test_main_window.py` and `tests/test_mcp_server_controller.py`.
  - All targeted unit tests passing (22 passed).
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1084/40-code-cleanup.md`
  - `make lint` clean.
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1084/50-observability.md`
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1084/60-tech-debt.md`
- [x] **STEP 8: Dev Docs**
  - Verified `doc/dev/` contains no stale references.
- [x] **COMMIT: Commit Changes**
  - Commit hash: `143eebbc` on `dev` — "refactoring(ui): PYPOST-1084 inject collection_lookup into McpServerSettingsController"
  - Branch name (reference only, not switched): `refactoring/PYPOST-1084-inject-collection-lookup`

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1084/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1084/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_mcp_server_controller.py::test_collection_lookup_passed_to_registry`

### STEP 4: Development

- `pypost/ui/mcp_server_controller.py`
- `tests/test_main_window.py`
- `tests/test_mcp_server_controller.py`

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1084/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1084/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1084/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/` (no changes needed)

### COMMIT

- Commit hash and message
