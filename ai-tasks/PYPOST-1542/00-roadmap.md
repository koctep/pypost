# Roadmap: PYPOST-1542

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1542/10-requirements.md`
  - Decision: remove both unused match helpers; point the remaining
    compiled-selector match checks at the live masking outcome.
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1542/20-architecture.md`
  - Delete `PathSelectorTrie.matches_tokens` and
    `CompiledPathSelector.matches` only. No private helper becomes unused.
  - Red test: `tests/test_pypost_1542_failing_repro.py` (timeout 30);
    absence assertion is red while the helpers still exist.
- [x] **STEP 3: Failing Repro Test**
  - `tests/test_pypost_1542_failing_repro.py`
- [x] **STEP 4: Development**
  - [x] Removed `PathSelectorTrie.matches_tokens` and
    `CompiledPathSelector.matches`. Retargeted the five 1394 matcher
    checks to `JsonSelectorEngine.matches` and dropped both helpers from
    `doc/dev/json_selector_engine.md`.
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1542/40-code-cleanup.md`
  - `make lint` passed. Scoped tests passed (2 files, 0 failed).
    No scoped source changes.
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1542/50-observability.md`
  - No new logs or metrics. Existing live-path DEBUG logs
    `json_selector_engine_compiled` and
    `json_selector_engine_redact_tree_completed` stay unchanged.
    Monitoring boxes left unchecked.
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1542/60-tech-debt.md`
  - Follow-up tasks: none
  - `tests/test_pypost_1542_failing_repro.py` declares
    `pytestmark = pytest.mark.timeout(30)`
  - `tests/test_pypost_1394_failing_repro.py` declares
    `pytestmark = pytest.mark.timeout(60)`
  - User docs: N/A. `doc/user/` does not name the removed helpers. The
    engine guide was updated in Step 4.
- [x] **STEP 8: Dev Docs**
  - Artifact: `doc/dev/json_selector_engine.md` from the Step 4 guide
    update. No Step 8 rewrite.
  - The guide does not offer `PathSelectorTrie.matches_tokens` or
    `CompiledPathSelector.matches`. Live matching stays on
    `JsonSelectorEngine.matches`.
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1542/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1542/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_pypost_1542_failing_repro.py`

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1542/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1542/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1542/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/json_selector_engine.md` (Step 4 guide update; no Step 8 rewrite)

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
