# Roadmap: PYPOST-1153

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - Requirements documented for the seven parallel test runner maintainability
    follow-ups.
- [x] **STEP 2: High-Level Architecture Design**
  - High-level architecture documented in `ai-tasks/PYPOST-1153/20-architecture.md`.
  - Preserves subprocess-per-file isolation and defines CLI, Make, timeout, and coverage
    boundaries for the seven accepted follow-ups.
- [x] **STEP 3: Failing Repro Test**
  - [ ] *[Red test path or N/A — no behavioral change]*
  - `tests/test_parallel_runner_followups_repro.py` covers lossless argv/node-id
    preservation, invalid and empty discovery, strict worker/timeout validation,
    executable Make fail-closed and coverage branches, plan/dispatch coverage
    ownership, adequate versus below-threshold aggregates, report modes, and
    bounded versus unbounded workers.
  - `make test PYTEST_ARGS='tests/test_parallel_runner_followups_repro.py -q'` is
    intentionally red against current code: 27 contract cases failed and 1
    partial Make coverage contract passed; failures are in the pre-fix runner
    behavior, not fixture collection or test discovery by pytest.
  - `make lint` and `make verify-ai-tasks` passed. No production code was changed.
- [x] **STEP 4: Development**
  - [x] Added typed runner configuration, lossless pytest argv replay, node-id-aware discovery,
    and first-class validation results with fail-closed empty/missing-target handling.
  - [x] Added dispatch-unit execution with strict worker/timeout validation, optional unbounded
    communication, timeout process-group cleanup, and preserved test/JSON result reporting.
  - [x] Consolidated coverage into executor-owned worker fragments and aggregate-only combination,
    threshold enforcement, source/report precedence, and project-owned coverage configuration.
  - [x] Updated `make test` and `make test-cov` to fail closed when the parallel runner is missing;
    aligned existing runner tests with the new contracts.
  - [x] Corrected coverage-flag insertion around retained `--` sentinels, fail-closed ambiguous
    opaque passthrough validation, attached short-option tracing, and narrow worker report
    suppression that preserves project pytest `addopts`; added focused regressions.
  - Focused validation: `make test PYTEST_ARGS='tests/test_parallel_runner_followups_repro.py
    tests/test_run_parallel_tests.py -q'` — 76 tests passed.
  - Full validation through `make check WORKERS=1`: lint passed; tests ran 339 files with
    330 passed and 6 skipped. The only failures were five pre-existing baseline nodes in
    `tests/test_function_expression_resolver.py`, `tests/test_solid_audit_baseline.py`, and
    `tests/test_template_service.py`; no PYPOST-1153-focused test failed.
  - Real coverage recipe validation: `make test-cov WORKERS=1` with the focused repro and an
    explicit outer threshold of 0 passed; the repro's genuine 95% below/above-threshold cases
    both retained their expected outcomes.
  - Step 4 remediation validation: focused runner/repro suites passed, including an actual
    `make test-cov` run with `--` and a post-sentinel target; lint, typecheck, and artifact
    verification passed.
  - `make typecheck`, `make verify-ai-tasks`, and the focused Make-budget/runner suites passed.
  - Corrected aggregate report-mode handling so `coverage report -m` is emitted only for
    `term-missing`/`term-m`; added deterministic regressions for terminal/custom report modes
    and confirmed the threshold-bearing report remains present for every mode.
  - Aligned the CI coverage summary with the runner's project-policy reader and added real
    aggregate regressions for project-threshold changes and explicit threshold precedence.
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Technical Debt Analysis**
- [x] **STEP 8: Dev Docs**
- [/] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1153/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1153/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1153/40-code-cleanup.md`
- Cleanup is limited to typing, imports, formatting, readability, and dead-local removal;
  accepted parser, dispatch, coverage, Make, and CI contracts are preserved.
- Updated `scripts/run_parallel_tests.py`, `tests/test_run_parallel_tests.py`, and the CI
  coverage summary shell block; the Make recipes required no additional cleanup.
- `make lint`, `make typecheck`, focused Make tests (4 files), and `make verify-ai-tasks` passed.
- `make analyze` is unavailable because no such Make target exists.

### STEP 6: Observability

- `ai-tasks/PYPOST-1153/50-observability.md`
- Added correlated runner lifecycle, validation, timeout, and coverage aggregate events with
  scalar key/value fields; no captured test output or environment contents are logged.
- Added focused `caplog` contracts for lifecycle correlation, validation redaction, timeout
  context, and coverage lifecycle/threshold outcomes.
- Redacted raw startup targets and parameterized node IDs to aggregate selection/count fields;
  coverage report classification now reserves threshold failures for explicit shortfall output and
  separates collection, configuration, command, report, and artifact failures while preserving
  nonzero exits.
- Added terminal completion events for pre-dispatch validation/discovery rejection with scalar
  zero-work counts and failure phase/code, correlated `run_id` fields on process-group cleanup,
  and root coverage-fragment cleanup before and after aggregate coverage.
- Final independent acceptance review passed: focused Make tests, lint, typecheck, and AI-task
  verification passed; CLI parse and coverage-prepare rejection completion events are covered;
  root `.coverage.*` artifact count was zero before and after review.
- No new Prometheus/OpenTelemetry exporter or Make/CI shell logging was justified for this
  short-lived CLI; existing `RunSummary` timings/counts and non-zero gates remain the metrics
  surface.

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1153/60-tech-debt.md`
- Final independent blocker audit passed: the artifact classifies all residual debt and verification
  gaps with explicit ownership and status, and preserves PYPOST-1261/PYPOST-1262 as pre-existing
  non-blocking issues without duplicate follow-ups.

### STEP 8: Dev Docs

- `doc/dev/parallel_test_runner.md`
- `ai-tasks/PYPOST-1153/70-dev-docs.md`
- Documents the supported Make/direct workflow, lossless pytest argument and node-id
  passthrough, fail-closed validation, coverage ownership, diagnostics, and baseline issue
  handling for PYPOST-1153.
- Final independent documentation review passed: the guide and Step 8 artifact match the final
  runner and Makefile, including missing-runner handling and timeout implementation semantics.

### COMMIT

- Full gate evidence: `make check WORKERS=1` completed with 330 passed, 6 skipped, and 3
  pre-existing baseline failures in `tests/test_function_expression_resolver.py`,
  `tests/test_solid_audit_baseline.py`, and `tests/test_template_service.py`; the focused
  PYPOST-1153 files passed. `make lint`, `make typecheck`, and `make verify-ai-tasks` passed.
- Root `.coverage.*` artifact count was zero after validation. The commit will include only the
  PYPOST-1153 implementation, tests, documentation, and task artifacts; the transient sprint
  registry and user-provided `AGENTS.md` remain untracked.
- Branch name and commit hash are reported in chat only, never written to this file.
