# Roadmap: PYPOST-1544

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1544/10-requirements.md`
  - Decision: wildcard presence is known from push and pop of the breadcrumb,
    and which fields are masked stays the same.
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1544/20-architecture.md`
  - Decision: breadcrumb wildcard count updated on push and pop; the
    shorthand gate reads that flag. Mask results stay the same.
- [x] **STEP 3: Failing Repro Test**
  - `tests/test_pypost_1544_failing_repro.py`
  - Source checks fail: `matches` still scans the path for `*`, and the
    redact and formatter walks still call `append`. Live mask checks pass.
- [x] **STEP 4: Development**
  - [x] Implemented `MaskBreadcrumb` wildcard count on push and pop.
    Hierarchical miss reads `has_wildcard`. One-shot lists and tuples still
    check segments. Redact and formatter walks call `push`. Mask results
    stay the same.
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1544/40-code-cleanup.md`
  - `MaskBreadcrumb.pop` index type is `SupportsIndex`. The 1544 test
    module docstring no longer says the source checks fail.
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1544/50-observability.md`
  - No new logs or metrics. Wildcard presence stays on the breadcrumb.
    Existing compile and redact debug events stay count-only. Path
    segments are not logged.
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1544/60-tech-debt.md`
  - No new follow-up. One-shot lists still scan their own segments; that
    is the accepted design. The 1544 test module timeout is 30 seconds.
- [x] **STEP 8: Dev Docs**
  - `doc/dev/json_selector_engine.md` — changed one sentence: "A one-shot
    list or tuple still uses `_sequence_has_wildcard`." `has_wildcard` is
    the wildcard count above zero. A hierarchical miss on a breadcrumb
    reads that flag and does not scan the location.
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1544/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1544/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_pypost_1544_failing_repro.py`

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1544/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1544/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1544/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
