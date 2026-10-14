# Roadmap: PYPOST-1379

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] `ai-tasks/PYPOST-1379/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - [x] `ai-tasks/PYPOST-1379/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_gui_response_view_click_to_reveal.py`
- [x] **STEP 4: Development**
  - [x] Iteration 1: Created `pypost/ui/widgets/response_mask_controller.py` with `MaskedTokenSpan`, `JsonMaskFormatter`, and `ResponseMaskController`.
  - [x] Iteration 2: Enhanced `pypost/core/sensitive_text_sanitizer.py` to publicly expose `format_path_variants`.
  - [x] Iteration 3: Enhanced `pypost/ui/widgets/foldable_code_view.py` with mask controller reference, viewport mouse event filtering, pointing hand cursor, and hover tooltips.
  - [x] Iteration 4: Enhanced `pypost/ui/widgets/response_view.py` with `display_response(..., hidden_fields=...)`, large-document fallback, streaming compatibility, search update synchronization, and re-indent preservation.
  - [x] Iteration 5: Wired `tabs_presenter_worker.py` to forward `request_data.hidden_response_fields` to `display_response`.
  - [x] Iteration 6: Verified all 8 repro test scenarios in `tests/test_gui_response_view_click_to_reveal.py` pass; verified full quality gate (`make check`, `make typecheck`).
- [x] **STEP 5: Code Cleanup**
  - [x] Static analysis and linting (`make lint` passed cleanly)
  - [x] Type checking verification (`make typecheck` passed baseline gate)
  - [x] Fast test suite execution (`make test PYTEST_ARGS="tests/test_gui_response_view_click_to_reveal.py"` passed in 1.30s)
  - [x] AI task artifacts verification (`make verify-ai-tasks` passed)
  - [x] Removed unused imports/variables and confirmed line lengths <= 100
  - [x] `ai-tasks/PYPOST-1379/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - [x] `ai-tasks/PYPOST-1379/50-observability.md`
  - [x] Documented logging, metrics, UI interaction telemetry, and security audit log boundaries for GUI click-to-reveal response masking.
- [x] **STEP 7: Technical Debt Analysis**
  - [x] `ai-tasks/PYPOST-1379/60-tech-debt.md`
  - [x] Evaluated shortcuts (in-memory AST formatting vs lazy span tokenizer, linear list scan for hit-testing, full text replacement on indent change, linear span shifting).
  - [x] Verified zero tests missing timeout markers across all test suites, including `tests/test_gui_response_view_click_to_reveal.py`.
  - [x] Analyzed performance concerns (latency on 50KB-100KB payloads, span tracking memory footprint).
  - [x] Classified follow-up tasks (0 Blockers, 5 Non-Blockers; downstream story PYPOST-1380 ticketed under parent epic PYPOST-1312).
- [x] **STEP 8: Dev Docs**
  - [x] Expanded `doc/dev/hidden_response_fields.md` Section 3 with MASK-3 click-to-reveal architecture, token span model, controller lifecycle, styling, downstream offset shifting, subsystem coexistence, large-doc fallback, and telemetry.
  - [x] Updated `doc/user/requests.md` with user guide for interacting with masked fields (click-to-reveal, re-mask, tooltips, drag selection, and context menu actions).
  - [x] Created `ai-tasks/PYPOST-1379/70-dev-docs.md` developer documentation record with architecture summary and verification instructions.
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1379/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1379/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_gui_response_view_click_to_reveal.py`

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1379/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1379/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1379/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/hidden_response_fields.md`
- `doc/user/requests.md`
- `ai-tasks/PYPOST-1379/70-dev-docs.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
