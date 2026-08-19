# Roadmap: PYPOST-1085

## Task Metadata

- **Implementation language**: Python
- **Branch name**: `refactoring/PYPOST-1085-drop-window-backref-and-aliases`

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1085/00-roadmap.md`
  - `ai-tasks/PYPOST-1085/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1085/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - Added assertions in `tests/test_main_window.py` verifying no `mcp_manager` or `mcp_registry` attributes on `MainWindow` and no `for_window` on `McpServerSettingsController`.
- [x] **STEP 4: Development**
  - Inlined `McpServerSettingsController` instantiation in `MainWindow.__init__` and removed `for_window` classmethod and `MainWindow` type-checking import from `pypost/ui/mcp_server_controller.py`.
  - Dropped `self.mcp_manager` and `self.mcp_registry` attribute aliases from `MainWindow`.
  - Updated `pypost/main.py` and `tests/test_main_window.py`.
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1085/40-code-cleanup.md`
  - `make lint` clean.
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1085/50-observability.md`
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1085/60-tech-debt.md`
- [x] **STEP 8: Dev Docs**
  - Updated `doc/dev/mcp_integration.md` and `doc/dev/testability.md`.
- [x] **COMMIT: Commit Changes**
  - Commit hash: `b81e645b` on `dev` — "refactoring(ui): PYPOST-1085 drop MainWindow back-reference and mcp aliases"
  - Branch name (reference only, not switched): `refactoring/PYPOST-1085-drop-window-backref-and-aliases`

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1085/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1085/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_main_window.py::TestMainWindow::test_constructor_stores_injected_dependencies`

### STEP 4: Development

- `pypost/ui/mcp_server_controller.py`
- `pypost/ui/main_window.py`
- `pypost/main.py`
- `tests/test_main_window.py`

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1085/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1085/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1085/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/mcp_integration.md`
- `doc/dev/testability.md`

### COMMIT

- Commit hash and message
