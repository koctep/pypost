# Roadmap: PYPOST-1185

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1185/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1185/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - `tests/test_mcp_client_tab.py` — `_click_disconnect`; `test_click_connect_updates_badge_to_connected_hermetic`; `test_click_disconnect_returns_badge_to_disconnected`
  - **Green on first run** (verification debt): product Connect/Disconnect button→badge wiring already correct; no production defect. Step 4 is harness-only (land/polish), not a chrome fix.
- [x] **STEP 4: Development**
  - [x] Verification debt confirmed: hermetic Connect/Disconnect badge proofs already green; **production no-op** (no `pypost/` changes)
  - [x] `make test PYTEST_ARGS="tests/test_mcp_client_tab.py -k 'click_connect_updates_badge_to_connected_hermetic or click_disconnect_returns_badge_to_disconnected' -v"` — **PASSED** (file 1.17s)
  - [x] Landed harness from Step 3 stays the permanent regression signal: `_click_disconnect`, `_is_disconnected_badge`, `test_click_connect_updates_badge_to_connected_hermetic`, `test_click_disconnect_returns_badge_to_disconnected`
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1185/40-code-cleanup.md`
  - [x] `make lint` PASSED; no cleanup edits required (test-only delta already clean)
  - [x] Full-file `make test PYTEST_ARGS="tests/test_mcp_client_tab.py -v"` PASSED
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1185/50-observability.md` — **N/A** (verification debt; production no-op; no new logs/metrics)
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1185/60-tech-debt.md` — no AC-breaking debt; no new follow-up tickets
- [x] **STEP 8: Dev Docs**
  - `doc/dev/mcp_client_draft_tab.md` — hermetic Connect/Disconnect badge
    button-path tests (PYPOST-1185)
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1185/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1185/20-architecture.md` — hermetic Connect/Disconnect button→badge proofs in `tests/test_mcp_client_tab.py`; inject mock `mcp_client`; FR-2.3 (isolation, not “never call run”)

### STEP 3: Failing Repro

- `tests/test_mcp_client_tab.py` — hermetic Connect→Connected and Disconnect→Disconnected button-path proofs (`_click_disconnect` + two focused tests)
- Outcome: **green first-run** (coverage gap closed; no production fix required for Step 4 unless polish)

### STEP 4: Development

- Production **no-op** (verification debt; chrome already correct)
- Tests: `tests/test_mcp_client_tab.py` hermetic Connect/Disconnect badge proofs (landed in Step 3; confirmed green)

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1185/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1185/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1185/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/mcp_client_draft_tab.md` — hermetic Connect/Disconnect badge
  button-path tests (PYPOST-1185)

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
