# Roadmap: PYPOST-1548

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1548/10-requirements.md`
  - Optional limit on how often mask hover feedback runs. The hovered
    value stays the value a click at that place would use. Extra pointer
    moves do not change which value is hovered or revealed. The limit is
    optional, and click results stay the same with or without it. Which
    fields are masked stays the same. Later click targets after a toggle
    stay as delivered by PYPOST-1547.
  - Any wait, interval, or pointer-motion filter is deferred to
    architecture (Step 2). Left `[/]` for the acceptance gate.
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1548/20-architecture.md`
  - Chosen limit: opt-in trailing coalesce of `MouseMove` hover
    feedback to the latest point, one apply per armed turn, default
    off (`limit_hover_moves=False`). Click keeps `span_at` on the
    release position. Fenwick index and masked fields stay.
  - Step 3 red test (not written in this step):
    `tests/test_pypost_1548_failing_repro.py`
    `test_enabled_hover_limit_coalesces_rapid_moves_and_keeps_latest_span`
  - Left `[/]` for the acceptance gate.
- [x] **STEP 3: Failing Repro Test**
  - `tests/test_pypost_1548_failing_repro.py`
  - `test_enabled_hover_limit_coalesces_rapid_moves_and_keeps_latest_span`
  - Red on current code: three synchronous viewport moves still apply
    hover feedback before one `processEvents`. The constructor rejects
    `limit_hover_moves`, so the test sets `_limit_hover_moves` and
    asserts the coalesce. Left `[/]` for the acceptance gate.
- [x] **STEP 4: Development**
  - [x] Implemented optional trailing coalesce of mask `MouseMove` hover
    feedback on `ResponseMaskController`. `limit_hover_moves` defaults
    to false, so `ResponseView` stays synchronous. When enabled, one
    0 ms timer applies cursor and tooltip once for the latest point
    through `span_at`. Click, the Fenwick index, and masked fields stay.
    `tests/test_pypost_1548_failing_repro.py` is green.
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1548/40-code-cleanup.md`
  - Hover coalesce code already met the 100-character limit, had no
    unused names, and needed no formatting edit. Lint passed.
    Typecheck stayed at 175 known baseline errors. The repro test
    stayed green. Left `[/]` for the acceptance gate.
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1548/50-observability.md`
  - Default hover stays synchronous and unlogged. The optional coalesce
    stores points and applies them once, with no coordinate or tooltip
    log. Existing click and span DEBUG records stay. No new log. No
    metrics. Left `[/]` for the acceptance gate.
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1548/60-tech-debt.md`
  - Optional trailing coalesce matches the architecture. The default
    hover path stays synchronous. Follow-up tasks: none. Reveal-memory,
    menu, and editor debt stays on the existing tickets. The developer
    guide still describes immediate `MouseMove` feedback; that update
    is Step 8. Left `[/]` for the acceptance gate.
- [x] **STEP 8: Dev Docs**
  - `doc/dev/hidden_response_fields.md`
  - Guide now describes the optional hover coalesce.
    `limit_hover_moves` defaults to false, so `ResponseView` still
    applies cursor and tooltip inside the move event. When the flag is
    true, rapid moves store the latest point and one 0 ms timer applies
    cursor and tooltip once through `span_at`. A click still uses the
    release position. Left `[/]` for the acceptance gate.
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1548/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1548/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_pypost_1548_failing_repro.py`

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1548/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1548/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1548/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/hidden_response_fields.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
