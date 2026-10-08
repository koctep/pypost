# Roadmap: PYPOST-1267

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - Created `10-requirements.md` from the assigned issue and PYPOST-1229 debt item 2.
  - Reviewed current import loading and the accepted PYPOST-1266 reader contract.
  - Documented loading/decoding cancellation outcomes and a one-second regression target.
  - `make verify-ai-tasks` passed: 392 completed tasks; 2 grandfathered legacy gaps.
  - Acceptance remains with the autonomous orchestrator after independent review.
- [x] **STEP 2: High-Level Architecture Design**
  - Created `20-architecture.md` with bounded read/decode checkpoints and compatibility coverage.
  - Defined deterministic real-file loading and active-scalar cancellation repros for Step 3.
  - Documented native-operation limits and differential JSON/PyYAML validation requirements.
  - Review fix: moved cancellation requests after a completed checkpoint; tests must observe
    actual read/scan work before the next checkpoint detects interruption.
  - Review fix: distinguished callback exceptions with a private carrier while preserving broad
    YAML fallback handling, constructor errors, and original JSON error precedence.
  - Added invalid timestamp/safe-tag and callback-exception compatibility checks to the plan.
  - Independent re-review passed; the orchestrator accepted Step 2.
  - `make verify-ai-tasks` passed: 392 completed tasks; 2 grandfathered legacy gaps.
  - Acceptance remains with the autonomous orchestrator after independent review.
- [x] **STEP 3: Failing Repro Test**
  - Independent review reproduced all 11 intended checkpoint failures; orchestrator accepted.
  - Creating `tests/test_collection_import_decode_cancellation.py` with real 16 MiB files.
  - Added 11 real-file cases: loading JSON/YAML/fallback and active lexical scanning of
    bundles and retained large description values, including plain and quoted YAML.
  - Observers delegate actual reads and inspect active scanner frames without supplying
    checkpoints; gate release precedes a real read/scan batch and its next checkpoint.
  - `make test PYTEST_ARGS='tests/test_collection_import_decode_cancellation.py'
    WORKERS=1 WORKER_TIMEOUT=180` returned exit 2: 11 failed in 31.05 seconds.
  - Every case failed the intended missing active-loading/active-decoding checkpoint
    assertion; no fixture/import/cleanup failures occurred. Runner duration: 32.43 seconds.
  - Production files were not modified. Step remains in progress for independent review.
- [x] **STEP 4: Development**
  - Independent re-review passed after nesting/merge fixes; orchestrator accepted Step 4.
  - [x] Review fix reproduced four 600-level JSON failures through Make before replacing
    recursive array/object descent with an instance-local container stack. This refinement
    preserves C-decoder accepted nesting without changing the process recursion limit;
    updated `20-architecture.md` to explain the change from Python `JSONArray` reuse.
  - [x] Review fix reproduced missing cancellation during 20,000-alias YAML merge assembly.
    Retained PyYAML node mutations, precedence, and recursive aliases; added checkpoints
    between sequence members and each 4096-entry assembly batch. Retained PyYAML MIT notice.
  - [x] Added differential 600/900-level array/object/mixed nesting and valid ignored fields,
    deep malformed-input positions/messages, 10,000-level cancellation/termination, merge
    precedence, recursive alias identity, merge errors, and assembly-only cancellation tests.
  - [x] Review-fix validation: decoder and all 11 unchanged 16 MiB cancellation regressions
    passed together in 16.90 seconds; core/reader/progress modules passed (4 files, 7.44 s).
    `make lint` passed; `make typecheck` retained the unchanged 181-error baseline.
  - [x] Added SafeLoader checkpoints and callback-origin carrier with original error precedence.
  - [x] Suppressed preparation sentinel from worker signals, preserving record emit/check order.
  - [x] Reduced YAML forward checks to bounded counters; disposed loaders on init interruption.
  - [x] Wired YAML observer gates to bounded peek while retaining all actual-work assertions.
  - [x] Final real-file latency run passed all 11 cases: loading 1.197-1.985 ms;
    JSON scanning 0.412-0.636 ms; YAML/fallback scanning 0.295-0.832 ms (limit 1000 ms).
    Fixtures were 16,777,242-17,351,716 bytes; properties exported through Make to JUnit XML.
  - [x] Differential compatibility and core/reader/progress modules passed (4 files, 4.39 s).
    Responsiveness, cancellation, async gaps, teardown, wait, apply, and presenter modules passed.
  - [x] `make lint` passed; `make typecheck` passed with the unchanged 181-error baseline.
  - [x] Retained CPython attribution, adaptation summary, and PSF license in the helper.
  - [x] All 11 accepted real-file cancellation regressions passed in 12.92 seconds.
  - [x] Added differential JSON/YAML, callback identity, concurrency, and progress coverage.
  - [x] Added bounded UTF-8 reads and instance-local JSON lexical/container checkpoints.
- [x] **STEP 5: Code Cleanup**
  - Independent re-review passed after decorator wrapping; orchestrator accepted Step 5.
  - Running full `make check` and `make typecheck`; results go in `40-code-cleanup.md`.
  - Created `40-code-cleanup.md`; corrected a stale decoder-observer comment only.
  - Review correction: wrapped an overlong decoder-test decorator; cases remain unchanged.
    `make lint` and the focused decoder module passed (4.30 seconds); whitespace check clean.
  - `make check`: lint passed; suite 363 passed, 5 failed, 6 skipped across 374 modules.
    All collection-import modules passed, including differential and real-file cancellation.
  - `make typecheck`: unchanged 181-error baseline; separate `make verify-ai-tasks` passed.
  - Unchanged reruns passed environment export, recipes, install stamps, and target filtering.
    Exit-policy rerun also passed (103.56 seconds). Existing follow-ups: PYPOST-1315,
    PYPOST-1298, PYPOST-1299. All five failed modules passed unchanged reruns.
- [x] **STEP 6: Observability**
  - Independent review passed; orchestrator accepted Step 6.
  - Reviewing existing worker/read lifecycle diagnostics and cancellation/error coverage.
  - Created `50-observability.md`; reused existing cancellation, success, and failure events.
  - Existing bounded file-import lifecycle metrics cover preparation cancellation as rejected.
    No new checkpoint logs, imported-content diagnostics, or production metric were necessary.
  - Focused cancellation, async-gap, and progress logging coverage passed (3 modules, 4.25 s).
  - `make lint` passed; existing document selection and production code remain unchanged.
  - Execution complete; independent review remains pending. No production/test code changed.
- [x] **STEP 7: Technical Debt Analysis**
  - Independent review passed; orchestrator accepted Step 7.
  - Created `60-tech-debt.md`; no new task-specific blocker or actionable follow-up identified.
  - Recorded parser maintenance, deeper JSON acceptance, native-operation and memory limits.
  - Preserved exact flaky node evidence and PYPOST-1298/PYPOST-1299/PYPOST-1315 ownership.
  - `make verify-ai-tasks` passed: 392 completed tasks; 2 grandfathered legacy gaps.
  - Execution complete; independent review remains pending. No production/test code changed.
- [x] **STEP 8: Dev Docs**
  - Independent review passed; orchestrator accepted Step 8.
  - Updating `doc/dev/collection_import.md` for cooperative loading/decoding checkpoints.
  - Documented `(0, 0)` callback sentinel, unchanged required worker reader keyword, optional
    helper checkpoint, bounded read/scanning/merge work, fallback and exception-origin cleanup.
  - Recorded all 11 active-phase real-file regressions, 1000 ms bound, final 0.295-1.985 ms
    measurements, environment/native-operation limits, deep JSON acceptance, and memory costs.
  - Updated usage, configuration, and troubleshooting; removed the obsolete task follow-up.
  - `make lint` passed (Markdown and relative links); `make verify-ai-tasks` passed:
    392 completed tasks, 2 grandfathered legacy gaps. No full-suite repeat for documentation.
  - Execution complete; independent review pending. No production/test code changed.
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1267/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1267/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1267/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1267/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1267/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/collection_import.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
