# Roadmap: PYPOST-1158

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1158/10-requirements.md`
  - Implementation language recorded: Python
  - Scope: unsaved WebSocket draft workspace tab (full editor, no collection item)
  - Depends on WS-TM-1 ([PYPOST-1157](https://pypost.atlassian.net/browse/PYPOST-1157))
  - ACs: title New WebSocket, empty URL (no host/path, no pre-filled scheme),
    live editor on draft, no session restore, no merge with other open tabs,
    dirty-close uses HTTP discard-vs-keep-tab prompt until PYPOST-1161 Save
  - Review-gap fix: language is Python only (no toolkit name); URL empty
    with no pre-filled scheme; FR-1.4 handshake start (URL blank vs factory
    defaults for Params/Headers/Subprotocols); dirty-close lifecycle (FR-8)
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1158/20-architecture.md`
  - Reuses PYPOST-1156 blank-tab model; peer MCP draft omission (1166)
  - Core gaps: `save_tabs_state` writes draft WS ids; no dirty-close prompt (FR-8)
  - Plan: registry-gated restore, `websocket_persisted_fields`, shared discard/keep prompt
  - Step 3 red tests: restore omit (FR-5), dirty-close prompt (FR-8)
  - Rewrite vs draft: verified FR-1..FR-8 / DoD against current code. HTTP
    `close_tab` has no unsaved prompt (`is_tab_dirty` is sibling-reload only;
    PYPOST-647). Dirty-close is WS-draft-only (factory-compare, no
    `persisted_baseline`). Factory / no-merge already on HEAD (WS-TM-1).
    Must-red Step 3: FR-5 omit + FR-8 dirty prompt. Step 4 locks:
    no-merge, saved dedup, saved id still persisted, clean-close
    (already green on HEAD — not a Step 3 red).
  - Review-gap fix: moved `test_close_clean_websocket_draft_does_not_prompt`
    from Step 3 reds to Step 4 locks (already green on HEAD).
- [x] **STEP 3: Failing Repro Test**
  - `tests/test_tabs_presenter.py` :: `TestTabsPresenter`
    - `test_save_tabs_state_omits_unsaved_websocket_draft`
    - `test_close_dirty_websocket_draft_prompts_discard_or_keep`
- [x] **STEP 4: Development**
  - [x] Iteration 1: `pypost/core/websocket_persisted_fields.py` factory-compare (Qt-free)
  - [x] Iteration 2: `prompt_unsaved_draft_tab_close` Discard / Keep dialog
  - [x] Iteration 3: `tab_dirty.is_websocket_draft_dirty` + `tabs_presenter_draft` helpers; wired `save_tabs_state` (registry gate) and `close_tab` (dirty unsaved WS draft prompt). `tabs_presenter.py` stays at 785 LOC.
  - [x] Iteration 4: Step 3 reds green; Step 4 locks (no-merge, saved dedup, persist saved id, clean-close); `make lint` clean on touched Python
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1158/40-code-cleanup.md`
  - `make lint` passed; `make analyze` is not a Makefile target
  - Targeted `make test` passed (5 files, 0 failed)
  - `tabs_presenter.py` remains 785 / 785 LOC
  - `make typecheck` failed in unrelated files (baseline-out-of-scope)
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1158/50-observability.md`
  - INFO logs in `tabs_presenter_draft.py` (omit, persist, dirty Keep/Discard,
    clean close); `tabs_presenter.py` unchanged at 785 LOC
  - No new Prometheus instruments (N/A for persist/close; existing GUI
    new-tab / WS session counters unchanged)
  - Caplog tests in `tests/test_tabs_presenter.py` (`timeout(60)`)
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1158/60-tech-debt.md`
  - No AC-breaking debt; factory-compare and WS-only dirty-close are
    intentional (PYPOST-1161 / HTTP close still unprompted)
  - `tabs_presenter.py` at 785 / 785 (PYPOST-1184 still To Do)
  - New follow-ups left unticketed (saved-tab skip-prompt test; HTTP
    discard-on-close — PYPOST-647 is Done and does not own that gap)
  - STEP 7 left `[/]` for the acceptance-gate owner
- [x] **STEP 8: Dev Docs**
  - Canonical: `doc/dev/websocket_draft_tab.md` (Overview, Architecture,
    API/Usage, Configuration, Troubleshooting)
  - Updated: `doc/dev/websocket_ui_client.md` (lifecycle, WS-TM-2 shipped)
  - Updated: `doc/dev/mcp_client_draft_tab.md` (WS draft omit table)
  - Updated: `doc/dev/new_tab_protocol_picker.md` (1158 shipped)
  - Updated: `doc/dev/state_manager.md` (`open_tabs` registry gate)
  - Updated: `doc/dev/logging.md` (draft persist/close INFO events)
  - Updated: `doc/dev/presenter_architecture.md` (TabsPresenter pointer)
  - Updated: `doc/dev/README.md` (TOC entry)
  - STEP 8 left `[/]` for the acceptance-gate owner
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1158/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1158/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1158/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1158/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1158/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/websocket_draft_tab.md`
- `doc/dev/websocket_ui_client.md`
- `doc/dev/mcp_client_draft_tab.md`
- `doc/dev/new_tab_protocol_picker.md`
- `doc/dev/state_manager.md`
- `doc/dev/logging.md`
- `doc/dev/presenter_architecture.md`
- `doc/dev/README.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
