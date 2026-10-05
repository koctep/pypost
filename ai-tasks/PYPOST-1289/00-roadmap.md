# Roadmap: PYPOST-1289

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1289/10-requirements.md` drafted for review.
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1289/20-architecture.md` documents session-end ownership, metrics
    interfaces, all teardown routes, and the Step 3 failing repro plan; review passed.
- [x] **STEP 3: Failing Repro Test**
  - Added session-end regression tests in `tests/test_mcp_client_presenter.py`.
  - `make test PYTEST_ARGS='tests/test_mcp_client_presenter.py'`: 3 failed, 9 passed.
    User and teardown releases emit no count; terminal-error release lacks the planned
    `reason` argument. Failed/cancelled Connect and nonterminal errors preserve zero counts.
  - Production code is unchanged; Step 3 awaits independent review.
- [x] **STEP 4: Development**
  - Implementing the reviewed session release and metrics-output contract.
  - [x] Added an idempotent, best-effort release counter and all four tracker surfaces.
  - [x] Wired workspace metrics and release on profile deletion and application teardown.
  - [x] Verified Prometheus, Qt, OTel and disabled outputs, tracker failure cleanup,
    stale callbacks, all five user/teardown routes, and declined profile-close behavior.
  - Focused presenter, metrics, tab, hotkey and teardown-contract tests pass through `make test`.
  - [x] Refreshed the measured LOC snapshot for the two changed audited modules; caps unchanged.
    `make test PYTEST_ARGS='tests/test_solid_audit_baseline.py
    tests/test_mcp_client_disconnect_metrics.py'` passes (2 files).
  - `make typecheck` passes against the 181-error baseline; `make verify-ai-tasks` passes.
  - `make check`: lint and documentation checks pass; 337 test files pass, 8 fail and 6 skip.
    The LOC snapshot failure is fixed and rerun green. Remaining failures match malformed
    expressions (PYPOST-1261), dialog inventory (PYPOST-1287), stream export (PYPOST-1286),
    and 120-second worker timeouts in Makefile/exit-policy tests (PYPOST-1262).
    The orchestrator confirmed the exit-policy timeout is included in PYPOST-1262's
    existing baseline-reproduction comment.
    An unchanged-tree rerun of those three files reproduced all three 120-second timeouts.
    Full output: `/tmp/pypost-1289-step4-check.log`. Step 4 awaits independent review.
- [x] **STEP 5: Code Cleanup**
  - `40-code-cleanup.md` records the source review; no code cleanup was necessary.
  - `make lint` and `make verify-ai-tasks` pass. Both affected test modules have explicit
    timeout markers. Prior typecheck and focused-test evidence remains applicable.
  - No production or test changes; the full suite was not repeated. Baseline failures and
    their tracking issues remain as recorded under Step 4. Awaiting independent review.
- [x] **STEP 6: Observability**
  - `50-observability.md` documents the disconnect counter, bounded reason contract,
    tracker-failure warning, privacy, supported outputs, and existing focused-test evidence.
  - No production or test changes were needed. `make lint` and `make verify-ai-tasks` pass.
    Full-suite baseline failures remain recorded under Step 4. Awaiting independent review.
- [x] **STEP 7: Technical Debt Analysis**
  - `60-tech-debt.md` records the contract limits, coverage, timeout-marker audit, and performance
    analysis. No new implementation debt or blocker was identified.
  - Recorded remaining baseline failures with node components, failure evidence, and existing
    PYPOST-1261, PYPOST-1287, PYPOST-1286, and PYPOST-1262 links; no duplicate issues needed.
  - Documentation-only changes; existing focused-test evidence remains applicable. No broad
    tests repeated. Awaiting independent review and the subsequent blocker review.
  - `make lint verify-ai-tasks` passes, including Markdown and relative-link checks.
- [x] **STEP 8: Dev Docs**
  - Updated `doc/dev/mcp_client_draft_tab.md` with session-end ownership, lifecycle/tracker
    APIs, reason semantics, supported outputs, configuration, and troubleshooting.
  - Updated `doc/prometheus_monitoring.md` with the counter and corrected workspace wiring.
    Documented nonterminal errors, idempotent teardown, best-effort loss, and duration limits.
  - `make lint verify-ai-tasks` passes, including Markdown and relative-link checks.
    Documentation-only changes; no full tests repeated. Awaiting independent review.
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1289/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1289/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1289/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1289/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1289/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/mcp_client_draft_tab.md`
- `doc/prometheus_monitoring.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
