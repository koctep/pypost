# Roadmap: PYPOST-1540

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1540/10-requirements.md`
  - Language: Python
  - Business goal: a person who writes an unsupported field selector is told
    which kind of problem it is when the draft uses a JSONPath dollar, a
    numeric index, or a filter, instead of one generic warning for every
    bad draft
  - Done when `$.token`, `users[0].email`, and `users[?(@.active)].email`
    each carry their own explanation, and a valid selector such as `token`
    gets no warning
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1540/20-architecture.md`
  - Chosen design: when a draft is already invalid, pick one of three
    explanations from the stripped draft's shape; accept and reject stay
  - Failing-repro plan: `tests/test_pypost_1540_failing_repro.py`
    (module timeout 30; Step 3 writes the red test)
- [x] **STEP 3: Failing Repro Test**
  - `tests/test_pypost_1540_failing_repro.py`
- [x] **STEP 4: Development**
  - [x] Added `_message_for_draft` so one JSONPath dollar, numeric index, or
    filter shape names itself. Mixed drafts and the written `..` reject
    keep the generic warning.
- [x] **STEP 5: Code Cleanup**
  - Static gate: `make lint` (`make analyze` is not a Makefile target)
  - Scope: `pypost/core/field_selector_syntax.py`,
    `tests/test_pypost_1540_failing_repro.py`,
    `ai-tasks/PYPOST-1540/40-code-cleanup.md`
  - `make lint` exit 0; scoped `make test` exit 0 (3 files)
  - No source edits; written `..` reject still uses the generic message
- [x] **STEP 6: Observability**
  - N/A: `ai-tasks/PYPOST-1540/50-observability.md` — no logs or metrics;
    `validate_field_selector` only picks a warning string, and a log of
    the draft would record the selector the person typed, including
    header names
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1540/60-tech-debt.md`
  - Follow-up tasks: none
  - `tests/test_pypost_1540_failing_repro.py` declares
    `pytestmark = pytest.mark.timeout(30)`
- [x] **STEP 8: Dev Docs**
  - `doc/dev/hidden_fields_table.md` Supported vocabulary: one dollar, index, or filter sentence
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1540/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1540/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_pypost_1540_failing_repro.py`

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1540/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1540/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1540/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
