# Roadmap: PYPOST-1159

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1159/10-requirements.md`
  - Implementation language recorded: Python
  - Scope: empty-workspace replacement after closing the last tab uses the
    same protocol picker as `Ctrl+N` / **+**; restore of saved HTTP and
    WebSocket profiles is unchanged; mixed saved workspaces must not
    regress
  - Depends on WS-TM-1
    ([PYPOST-1157](https://pypost.atlassian.net/browse/PYPOST-1157)) and
    WS-TM-2
    ([PYPOST-1158](https://pypost.atlassian.net/browse/PYPOST-1158)), both
    shipped
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1159/20-architecture.md`
  - Last-tab empty strip calls `handle_new_tab("last_tab")` (picker), not
    `add_new_tab`; restore of saved HTTP/WS unchanged
  - Extract `close_tab` first (`tabs_presenter.py` 785/785; PYPOST-1184)
  - Step 3: reds for picker on last-tab close; restore mixed workspace as
    locks (green on HEAD)
- [x] **STEP 3: Failing Repro Test**
  - Red: `tests/test_tabs_presenter.py::TestCloseLastTabProtocolPicker`
    (last-tab close must use picker / `handle_new_tab("last_tab")`, not
    silent `add_new_tab` HTTP)
  - Red: `tests/test_metrics_manager.py` —
    `TestMetricsManagerGuiTracking::test_track_gui_new_tab_action_last_tab_source`
  - Locks in the same class (green on HEAD): non-last close and dirty-WS
    Keep skip the picker
  - Restore locks not added (already green; not the Step 3 repro)
- [x] **STEP 4: Development**
  - [x] Extracted `close_tab` body to `pypost/ui/presenters/tabs_presenter_close.py` (TYPE_CHECKING import of `TabsPresenter`; presenter method is a thin delegate). `tabs_presenter.py` is 770 / 785.
  - [x] Empty-workspace fallback after last close calls `handle_new_tab("last_tab")` instead of `add_new_tab(save_state=False)`. Dirty WS keep/discard still runs first; restore unchanged.
  - [x] Registered `last_tab` in `_NEW_TAB_ACTION_SOURCES` and `doc/prometheus_monitoring.md`.
  - [x] Step 3 reds green: `TestCloseLastTabProtocolPicker` and `test_track_gui_new_tab_action_last_tab_source`. SOLID snapshot baseline LOC updated 779 → 770.
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1159/40-code-cleanup.md`
  - `make lint` exit 0; no flake8 fixes required in scoped files
  - Scoped pytest: `TestCloseLastTabProtocolPicker` (7) +
    `test_track_gui_new_tab_action_last_tab_source` — 8 passed
  - No code edits during cleanup (already conformant)
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1159/50-observability.md`
  - Verified: `close_workspace_tab` → `handle_new_tab("last_tab")` reuses
    existing INFO logs (`new_tab_action_triggered` / `_cancelled` /
    `_completed`) and `gui_new_tab_actions_total{source="last_tab",protocol}`
  - No new log/metric code — Step 4 wiring sufficient; gaps none
  - Validation: `TestCloseLastTabProtocolPicker` metric/cancel tests +
    `test_track_gui_new_tab_action_last_tab_source`
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1159/60-tech-debt.md`
  - No AC-breaking debt; last-tab picker + metrics shipped as designed
  - [PYPOST-1184](https://pypost.atlassian.net/browse/PYPOST-1184) still
    To Do (insert-before-plus extract; **not** closed by close-tab extract)
  - Gaps: mixed-restore lock test not added; no last-tab MCP metric test;
    `doc/dev/` drift → Step 8; bulk-delete empty strip still silent HTTP
    (out of scope)
  - Timeout markers: no BLOCKER (`test_tabs_presenter` / metrics module
    `pytestmark`)
- [x] **STEP 8: Dev Docs**
  - `doc/dev/last_tab_protocol_picker.md` — last-tab empty-workspace
    picker: `close_workspace_tab` → `handle_new_tab("last_tab")`, cancel
    empty strip, restore unchanged, metrics `source=last_tab`
  - Updated `doc/dev/new_tab_protocol_picker.md` — table row, diagram,
    `handle_new_tab` sources, troubleshooting cross-link
  - `doc/dev/README.md` — TOC entry for PYPOST-1159
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1159/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1159/20-architecture.md`

### STEP 3: Failing Repro

- Red: `tests/test_tabs_presenter.py::TestCloseLastTabProtocolPicker`
- Red: `tests/test_metrics_manager.py` —
  `TestMetricsManagerGuiTracking::test_track_gui_new_tab_action_last_tab_source`

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1159/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1159/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1159/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/last_tab_protocol_picker.md`
- `doc/dev/new_tab_protocol_picker.md` (cross-links)
- `doc/dev/README.md` (TOC)

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and
  commit hash are reported in chat only, never written to this file.
