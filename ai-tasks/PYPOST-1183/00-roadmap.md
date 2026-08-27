# Roadmap: PYPOST-1183

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1183/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1183/20-architecture.md`
  - Verification-debt architecture: presenter proofs for title / widget id /
    last-HTTP-close-with-MCP; widen suite `_request_tab_count` to match
    production; no product change expected unless restore
- [x] **STEP 3: Failing Repro Test**
  - Verification debt: no intentional product breakage; hermetic proofs authored
  - `tests/test_tabs_presenter.py`:
    - `_request_tab_count` helper aligned to `(RequestTab, WebSocketTab, McpClientTab)`
    - `TestHandleNewTabProtocolPicker::test_open_blank_tab_mcp_client_sets_title_new_mcp_client`
    - `TestHandleNewTabProtocolPicker::test_open_blank_tab_mcp_client_sets_widget_id`
    - `TestHandleNewTabProtocolPicker::test_request_tab_count_helper_counts_mcp_client`
    - `TestCloseLastTabProtocolPicker::test_close_last_http_with_mcp_remaining_does_not_auto_open_http`
  - Optional FR-5 construction-only: skipped (existing `tests/test_mcp_client_tab.py` identity coverage adequate)
  - First `make test PYTEST_ARGS="tests/test_tabs_presenter.py -k 'open_blank_tab_mcp_client_sets or request_tab_count_helper_counts_mcp or close_last_http_with_mcp_remaining' -v"`: **green** (expected — production title / id / count already correct; helper widen is test-only)
  - Full file regression `make test PYTEST_ARGS="tests/test_tabs_presenter.py -v"`: **PASSED**
  - No production edits
- [x] **STEP 4: Development**
  - [x] Confirmed FR-1..FR-4 met by Step 3 proofs in `tests/test_tabs_presenter.py`
    (title, widget id, last-HTTP-close-with-MCP, helper aligned to production)
  - [x] Production no-op: no restore needed — PYPOST-1165 title / id / count
    already correct; no production module edits
  - [x] Focused proofs `make test PYTEST_ARGS="tests/test_tabs_presenter.py -k 'open_blank_tab_mcp_client_sets or request_tab_count_helper_counts_mcp or close_last_http_with_mcp_remaining' -v"`: **PASSED**
  - [x] Full file `make test PYTEST_ARGS="tests/test_tabs_presenter.py -v"`: **PASSED**
  - Optional FR-5: still skipped (existing `tests/test_mcp_client_tab.py` adequate)
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1183/40-code-cleanup.md`
  - `make lint` PASSED (no `pypost/` findings; no production edits)
  - Focused + full `tests/test_tabs_presenter.py` via `make test`: PASSED
  - Module `pytestmark` timeout(60) covers new proofs; no unused imports / dead
    code / debug prints in the PYPOST-1183 delta
  - No code edits required beyond this cleanup report
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1183/50-observability.md`
  - Verification-debt / production no-op: no new production logging or
    metrics; observability N/A for this ticket
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1183/60-tech-debt.md`
  - Verification-debt / production no-op: no AC-breaking debt; remaining
    items are intentional hermetic gaps, out-of-scope sibling helpers, and
    epic context (none block Step 8)
- [/] **STEP 8: Dev Docs**
  - `doc/dev/new_tab_protocol_picker.md` — PYPOST-1183 blank MCP title /
    widget id / suite `_request_tab_count` proofs + troubleshooting
  - `doc/dev/last_tab_protocol_picker.md` — last-HTTP-close-with-MCP
    remaining path, troubleshooting, close-path test
  - `doc/dev/mcp_client_draft_tab.md` — teardown count note + Tests
    cross-links to PYPOST-1183 proofs
  - `doc/dev/README.md` — index titles include PYPOST-1183
- [ ] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1183/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1183/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_tabs_presenter.py` — title / widget id after `open_blank_tab(MCP_CLIENT)`;
  last-HTTP-close-with-MCP-remaining; suite `_request_tab_count` aligned
- Expected / observed first run **green** (verification debt; product already
  matches PYPOST-1165 contract; helper widen is test-only) — not an intentional
  red→green product cycle
- Optional FR-5 construction tests: not added (existing coverage sufficient)

### STEP 4: Development

- Verification debt: **production no-op** (no `pypost/` edits)
- Proofs already green from Step 3 (`tests/test_tabs_presenter.py`)
- FR-1..FR-4 satisfied; FR-5 optional coverage not added

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1183/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1183/50-observability.md`
- Verdict: **N/A** — verification debt / production no-op; no new logs or
  metrics; existing PYPOST-1165 blank-tab / MCP Client observability unchanged

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1183/60-tech-debt.md`
- No AC-breaking debt; verification-debt / production no-op; timeout
  markers OK (module `timeout(60)`); remaining items NON-BLOCKER
  (hermetic gaps, optional hardening, sibling helpers, epic context)

### STEP 8: Dev Docs

- `doc/dev/new_tab_protocol_picker.md`
- `doc/dev/last_tab_protocol_picker.md`
- `doc/dev/mcp_client_draft_tab.md`
- `doc/dev/README.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
