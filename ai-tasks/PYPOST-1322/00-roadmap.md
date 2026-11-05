# Roadmap: PYPOST-1322

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1322/10-requirements.md`
  - Language: Python (test-only characterization of existing teardown behavior)
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1322/20-architecture.md`
  - Characterization-only: extend
    `tests/test_collection_import_teardown_policy.py` (FakeClock / `_SpyWorker`);
    nest `_on_worker_finished` via single-shot `processEvents` monkeypatch; no
    production changes
  - Failing-repro plan: Step 3 adds Risk 3 assertions without nesting hook (red =
    missing coverage); Step 4 wires nesting until same asserts go green
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_collection_import_teardown_policy.py` —
        `test_nested_worker_finish_join_overrun_during_wait_idle` (red: assertions
        without processEvents nesting hook)
- [x] **STEP 4: Development**
  - [x] Wired single-shot `processEvents` nesting hook in
        `test_nested_worker_finish_join_overrun_during_wait_idle` (exhaust budget →
        `_on_worker_finished` → IDLE); no production changes; `_SpyWorker` unchanged
  - [x] Green:
        `make test PYTEST_ARGS="tests/test_collection_import_teardown_policy.py::test_nested_worker_finish_join_overrun_during_wait_idle"`
  - [x] Green: full module
        `make test PYTEST_ARGS="tests/test_collection_import_teardown_policy.py"`
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1322/40-code-cleanup.md`
  - `make lint` PASS (no `make analyze`; flake8 / test-lint / docs OK; no fixes)
  - `make test PYTEST_ARGS="tests/test_collection_import_teardown_policy.py"` PASS
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1322/50-observability.md`
  - N/A — no new production logging/metrics; existing WARNING
    `collection_import_worker_finish_wait_timeout` covered by characterization test
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1322/60-tech-debt.md`
  - Timeout markers: no blocker (module `pytestmark = pytest.mark.timeout(30)`)
  - Follow-ups to file: none (accepted seams / out-of-scope facets only)
  - Phase C blocker review: SAFE TO CLOSE
- [x] **STEP 8: Dev Docs**
  - Updated `doc/dev/collection_import.md`: Risk 3 nested-join bullet, teardown-policy
    tests blurb, troubleshooting WARNING, and PYPOST-1264 follow-ups all point to
    `test_nested_worker_finish_join_overrun_during_wait_idle`
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1322/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1322/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_collection_import_teardown_policy.py::test_nested_worker_finish_join_overrun_during_wait_idle`
  (red: Risk 3 asserts without `processEvents` nesting hook)

### STEP 4: Development

- `tests/test_collection_import_teardown_policy.py` — completed nesting harness for
  `test_nested_worker_finish_join_overrun_during_wait_idle` (characterization green)

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1322/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1322/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1322/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/collection_import.md` — Risk 3 characterization test discoverability
  (`test_nested_worker_finish_join_overrun_during_wait_idle`)

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
