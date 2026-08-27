# Roadmap: PYPOST-1180

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1180/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1180/20-architecture.md`
  - Hermetic `prompt()` outcome proofs via instance `menu.exec` mock (reuse MCP pattern); production unchanged unless mapping defect
  - Step 3 failing-repro: N/A for intentional product breakage (verification debt); author HTTP / WebSocket / dismiss tests in `tests/test_new_tab_protocol_picker.py`
- [x] **STEP 3: Failing Repro Test**
  - Verification debt: no intentional product breakage; hermetic HTTP / WebSocket / dismiss `prompt()` proofs authored
  - `tests/test_new_tab_protocol_picker.py` — `test_prompt_maps_http_request_action`, `test_prompt_maps_websocket_action`, `test_prompt_dismiss_returns_none` (+ shared `_install_fake_exec`; MCP mapping kept)
  - First `make test PYTEST_ARGS="tests/test_new_tab_protocol_picker.py -v"`: **green** (expected — production mapping already correct; Step 4 production no-op unless regress)
- [x] **STEP 4: Development**
  - [x] Confirmed FR-1..3 / FR-4 / FR-5: Step 3 hermetic `prompt()` proofs already green against current `NewTabProtocolPicker.prompt` (HTTP `actions()[0]`, WebSocket `actions()[1]`, dismiss `None`); construction + MCP mapping intact
  - [x] Production **no-op** — inspected `pypost/ui/widgets/new_tab_protocol_picker.py`; mapping already matches PYPOST-1157 contract; no production edit
  - [x] `make test PYTEST_ARGS="tests/test_new_tab_protocol_picker.py -v"` — PASSED
  - [x] Regression smoke: `make test PYTEST_ARGS="tests/test_tabs_presenter.py -k 'HandleNewTabProtocolPicker or plus_tab' -v"` — PASSED
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1180/40-code-cleanup.md`
  - `make lint` PASS; flake8 on `tests/test_new_tab_protocol_picker.py` clean
  - No code edits required (already formatted; no unused imports/vars/debug/dead code)
  - `make test PYTEST_ARGS="tests/test_new_tab_protocol_picker.py -v"` PASS; module timeout(60)
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1180/50-observability.md`
  - N/A — verification-debt unit tests only; no production code change; no new logging/metrics
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1180/60-tech-debt.md`
  - No AC-breaking debt; production no-op; module `timeout(60)` OK (no BLOCKER)
  - Closes PYPOST-1157 follow-up 7; remaining: live `exec()` intentional gap, optional defensive-path / construction-overlap notes
- [x] **STEP 8: Dev Docs**
  - `doc/dev/new_tab_protocol_picker.md` — documented PYPOST-1180 hermetic HTTP / WebSocket / dismiss `prompt()` mapping via mocked `menu.exec`; corrected stale “build_menu only” / “never call prompt()” guidance
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1180/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1180/20-architecture.md` — hermetic picker outcome-test architecture (HTTP / WebSocket / dismiss); no new production API

### STEP 3: Failing Repro

- `tests/test_new_tab_protocol_picker.py` — HTTP / WebSocket / dismiss `prompt()` proofs (instance `menu.exec` mock)
- Expected first run **green** (verification debt; mapping already correct) — not an intentional red→green product cycle

### STEP 4: Development

- Production: **no-op** (`new_tab_protocol_picker.py` mapping already correct)
- Tests: Step 3 proofs remain green; presenter / plus-tab injected-picker smoke green

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1180/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1180/50-observability.md` — N/A (verification-debt tests only; no new telemetry)

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1180/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/new_tab_protocol_picker.md` — hermetic `prompt()` HTTP / WebSocket / dismiss coverage (PYPOST-1180)

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
