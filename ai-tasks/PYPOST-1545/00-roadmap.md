# Roadmap: PYPOST-1545

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1545/10-requirements.md`
  - Isolated catalog for insert dedupe and size, an empty index,
    shorthand-only walks, and path-and-key agreement with the public
    mask check. Removed match helpers stay removed. The catalog locks
    today's yes-or-no for a wildcard-heavy set of rules. A new index
    shape stays out of scope. Mask results stay the same.
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1545/20-architecture.md`
  - Isolated catalog in `tests/test_pypost_1545_failing_repro.py`.
    It calls existing `PathSelectorTrie` and `JsonSelectorEngine` in
    `pypost/core/json_selector_engine.py`. No production change, no new
    public API, and the removed match helpers stay removed.
  - Step 3 is planned as N/A — no behavioral change. The catalog locks
    today's insert count and today's yes-or-no.
- [x] **STEP 3: Failing Repro Test**
  - N/A — no behavioral change. Current insert, size, empty index,
    shorthand-only, bare-name, and wildcard-heavy yes-or-no outcomes
    already match the accepted requirements, so a red test would not
    fail for a missing behavior.
- [x] **STEP 4: Development**
  - [x] Added the characterization catalog in
    `tests/test_pypost_1545_failing_repro.py`: insert dedupe and
    size, empty index, shorthand-only walks, bare-name rules,
    path-and-key agreement, and the wildcard-heavy yes-or-no.
    Production code is unchanged.
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1545/40-code-cleanup.md`
  - Lint and line-length review of `tests/test_pypost_1545_failing_repro.py`
    only. Production code stays unchanged.
  - `make lint` passed. The scoped test file passed. No test edits were
    required.
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1545/50-observability.md`
  - No new logs or metrics. The characterization catalog does not change
    production matching. Existing count-only DEBUG events
    `json_selector_engine_compiled` and
    `json_selector_engine_redact_tree_completed` stay unchanged. Path
    segments and selector strings stay out of logs.
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1545/60-tech-debt.md`
  - No new debt. The catalog is tests only. Production matching stays
    unchanged. Follow-ups: none. `CompiledPathSelector.raw` stays unread
    and is already classified.
- [x] **STEP 8: Dev Docs**
  - `doc/dev/json_selector_engine.md`
  - PathSelectorTrie section names the isolated catalog in
    `tests/test_pypost_1545_failing_repro.py`. Production code is unchanged.
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1545/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1545/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1545/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1545/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1545/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/json_selector_engine.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
