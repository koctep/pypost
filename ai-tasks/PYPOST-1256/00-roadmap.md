# Roadmap: PYPOST-1256

## Task Metadata

- **Implementation language**: Python 3.11+

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1256/10-requirements.md`
  - Documents business goals, user stories, scope, non-goals, lifecycle safety constraints,
    measurable acceptance criteria, and current Jira-to-repository terminology.
  - Validation: `make lint` and `make verify-ai-tasks` pass.
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - `tests/test_presenter_teardown_contract_repro.py`
  - Repros use public owner methods, public Qt signals/widgets, injected storage fakes, and the
    public RequestWorker construction seam; no private production worker, presenter-handler,
    gateway-queue, or manager-thread state is inspected.
  - Coverage includes two-tab completion/failure/cancellation emissions concurrent with teardown,
    concurrent teardown against an active gated worker, real append/delete/clear persistence
    performed by teardown itself, gated public load/save APIs, panel-local/shared-history
    ownership, the product-facing queued `TabsPresenter.env_update_requested` handoff with
    pre-cutoff acceptance/post-cutoff rejection and product-reported dispositions, late
    environment load/save success/failure signals whose incomplete result and UI state cannot be
    retroactively mutated, and public MainWindow composition-root ordering, shared-deadline
    propagation, and aggregate failure.
  - The history panel refresh assertion follows the asynchronous load completion callback through
    a controlled queued signal. Controlled Events/signals replace sleeps and `qWait`.
  - Accepted history saves release their storage gate only after the teardown-owned public
    `HistoryManager.flush()` drain path is entered, so a no-op or early-return teardown cannot
    satisfy the persistence assertions. Request/environment race doubles expose public
    `stop_entered` and `release_stop` gates; the worker settles only after the test-controlled
    release follows the stop request, and neither `stop()` nor `wait()` performs settlement.
  - Step 3 was intentionally red before implementation because the current owners did not expose
    the approved uniform teardown API; the repro is now green under Step 4.
  - Validation: `make test WORKERS=1 WORKER_TIMEOUT=60
    PYTEST_ARGS='tests/test_presenter_teardown_contract_repro.py'` collected 23 tests and
    failed 23 expected red repros (0 passed, 0 skipped), with no collection errors; all failures
    are due to absent approved teardown APIs on the current base revision. `make lint` passed and
    `make verify-ai-tasks` passed.
- [x] **STEP 4: Development**
  - [x] Added shared `TeardownResult` values and bounded, idempotent teardown entry points for
    request tabs, history panel/manager, environment gateway/presenter, and MainWindow.
  - [x] Added lifecycle admission fences, late-delivery suppression, request cancellation across
    all open request tabs, accepted history persistence draining, and environment queue retention.
  - [x] Focused repro gate: 27 collected (the original 23 plus four review-regression cases),
    all passed via `make test WORKERS=1 WORKER_TIMEOUT=60
    PYTEST_ARGS='tests/test_presenter_teardown_contract_repro.py'`; `make lint` passed.
  - [x] Closed Step 4 review gaps with atomic request/history/storage admission, propagated
    persistence outcomes for environment-update sequences, root-wide shutdown fencing, and
    close-event rejection for incomplete aggregate cleanup; the 23-case repro and affected
    suites remain passing.
  - [x] Repaired the latest compatibility regressions: deferred history writes are replayed after
    bounded loads, accepted save failures remain observable, extracted saves use the established
    tabs logger, MainWindow preserves AlertManager and legacy environment seams, and environment
    update admission shares the teardown cutoff lock. Added focused regression coverage.
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Technical Debt Analysis**
- [x] **STEP 8: Dev Docs**
  - `doc/dev/presenter_teardown.md`
  - `ai-tasks/PYPOST-1256/70-dev-docs.md`
  - Documents public teardown APIs, result/outcome semantics, bounded deadlines, root ordering,
    environment-update cutoff, late-signal fencing, ownership, compatibility, telemetry, and test
    guidance. Validation: focused lifecycle/observability Make tests passed (2 files), `make lint`
    passed, and `make verify-ai-tasks` passed. Independent acceptance review passed.
- [/] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1256/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1256/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1256/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1256/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1256/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
