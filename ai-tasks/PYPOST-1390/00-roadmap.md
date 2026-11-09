# Roadmap: PYPOST-1390

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1390/10-requirements.md`
  - Sourced from Jira PYPOST-1390 / summary link to PYPOST-1379 debt: linear hit-testing under high-frequency viewport mouse moves with many masked spans
  - Business goal clarified: keep hover / click-to-reveal responsive when masked token counts grow large, without changing interaction semantics
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1390/20-architecture.md`
  - Decision: `span_at` via stdlib `bisect_right` on ordered `_spans` by `start_pos` + inclusive `end_pos` check; toggle shift / formatter / visuals unchanged
  - Step 3 repro design: `tests/test_pypost_1390_failing_repro.py` (parity vs linear oracle + high-N logarithmic instrumentation)
- [x] **STEP 3: Failing Repro Test**
  - `tests/test_pypost_1390_failing_repro.py` — oracle parity (green) + high-N logarithmic visit budget (red on linear `span_at`; 82368 visits > budget 19608 at N=512)
  - Confirmed red via `make test PYTEST_ARGS="tests/test_pypost_1390_failing_repro.py -v"` — `test_span_at_high_n_queries_do_logarithmic_work_not_full_scans` fails for intended reason; no production fix
- [x] **STEP 4: Development**
  - [x] Rewrote `ResponseMaskController.span_at` to use `bisect_right` on `start_pos` + inclusive `end_pos` check (`pypost/ui/widgets/response_mask_controller.py`)
  - [x] Step 3 repro green: `make test PYTEST_ARGS="tests/test_pypost_1390_failing_repro.py -v"`
  - [x] Full `make test` triage vs baseline `5aadedc8`: pre-existing/flaky only (PYPOST-1474, 1534, 1397, 1535, 1475, 1492; new flaky PYPOST-1546); recorded in `60-tech-debt.md`
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1390/40-code-cleanup.md`
  - Focus: `response_mask_controller.py` + `test_pypost_1390_failing_repro.py`; lint/typecheck green; stale red-state docstrings updated
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1390/50-observability.md`
  - N/A new logs/metrics on hot-path `span_at` (justified); existing DEBUG at span-set / toggle retained
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1390/60-tech-debt.md` — full template; new Debt [PYPOST-1547](https://pypost.atlassian.net/browse/PYPOST-1547), [PYPOST-1548](https://pypost.atlassian.net/browse/PYPOST-1548); pre-existing already linked (skipped)
- [x] **STEP 8: Dev Docs**
  - `doc/dev/hidden_response_fields.md` — `span_at` bisect hit-test section + PYPOST-1390 verification step
  - `doc/dev/README.md` — index entry includes PYPOST-1390
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1390/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1390/20-architecture.md` — bisect hit-test plan for `ResponseMaskController.span_at`; failing-repro design included

### STEP 3: Failing Repro

- `tests/test_pypost_1390_failing_repro.py`

### STEP 4: Development

- `pypost/ui/widgets/response_mask_controller.py` — `span_at` via `bisect_right`
- `tests/test_pypost_1390_failing_repro.py` — green after fix
- `ai-tasks/PYPOST-1390/60-tech-debt.md` — Step 4 triage follow-ups (pre-existing/flaky)

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1390/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1390/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1390/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
