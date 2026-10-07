# Roadmap: PYPOST-1266

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - Created `10-requirements.md` from the assigned issue and PYPOST-1229 debt item 1.
  - Defined consistent reader cancellation behavior and retained existing import outcomes.
  - Acceptance review pending with the autonomous orchestrator.
- [x] **STEP 2: High-Level Architecture Design**
  - Reviewing the collection reader boundary and planning a typed checkpoint contract.
  - Created `20-architecture.md` with the required-keyword protocol and direct worker invocation.
  - Defined red tests for opaque-reader cancellation and explicit single-argument rejection.
  - Production parser keeps its optional callback for synchronous callers; test fakes are scoped
    to the background collection import boundary. Independent review pending.
  - `make lint-docs` and `make verify-ai-tasks` passed; production and tests are unchanged.
- [x] **STEP 3: Failing Repro Test**
  - Creating `tests/test_collection_import_reader_contract.py` for opaque-reader cancellation.
  - Replacing legacy-reader success coverage with rejection coverage in
    `tests/test_collection_import_progress.py`; production code remains unchanged.
  - Red run: `make test PYTEST_ARGS='tests/test_collection_import_reader_contract.py
    tests/test_collection_import_progress.py' WORKERS=1 WORKER_TIMEOUT=60` exited 2:
    four existing tests passed and exactly two intended regressions failed.
  - `test_opaque_reader_observes_cancellation_at_first_checkpoint` processed `[1, 2, 3]`
    instead of `[1]`: signature inspection bypassed the cancellation checkpoint.
  - `test_collection_import_parse_worker_rejects_legacy_single_arg_reader` invoked the reader
    body instead of rejecting its missing keyword: the compatibility fallback silently succeeded.
  - Both tests capture terminal signals directly and use explicit timeout markers plus bounded
    worker waits/cleanup. Independent red-test review pending; Step 3 remains in progress.
- [x] **STEP 4: Development**
  - Applying the reviewed reader protocol and making the cancellation regressions green.
  - [x] Replaced signature inspection and fallback with `ReadImportFile` and direct callback
    invocation; propagated the presenter injection type. The two reviewed regressions and
    existing progress checks pass through Make (two modules).
  - [x] Migrated collection UI, delayed, and responsiveness reader fakes to accept and invoke
    checkpoints; file-error fakes accept the keyword without pretending to process records.
  - [x] Added success/progress and first-checkpoint cancellation coverage for keyword-only and
    positional-or-keyword functions, bound methods, callable objects, keyword forwarding, and
    opaque callable metadata; added real JSON parser success and valid/invalid record cancellation.
  - Targeted Make checks passed for contract, core parser, progress, cancellation, responsiveness,
    collection UI, UI lifecycle repro, teardown repro, and async gaps (nine modules).
    A transient contract-test insertion syntax error was fixed and that module reran green.
  - `make lint` passed; `make typecheck` passed with the unchanged 181-error baseline.
    No new failures or blockers remain; Step 4 awaits independent acceptance.
- [x] **STEP 5: Code Cleanup**
  - Reviewing accepted source/test changes for formatting, imports, and bounded test cleanup.
  - Running the full `make check WORKER_TIMEOUT=120` once without test exclusions.
  - Created `40-code-cleanup.md`; no Python cleanup edits were necessary.
  - Full check exited 2: lint/docs passed; 359 test files passed, seven failed, six skipped.
    Refreshed the task-caused presenter metrics count (522 to 520) via `make baseline-metrics`;
    the focused SOLID module then passed. Six remaining failures require orchestrator triage.
  - Separate `make verify-ai-tasks` passed (391 completed tasks; two legacy gaps).
    Exact failure IDs/excerpts are recorded in the cleanup report; acceptance remains pending.
  - Resumed triage at base `28084091` in fresh `/tmp/baseline-PYPOST-1266-resume`:
    five of six focused modules passed; the exit-policy timeout reproduced (PYPOST-1299).
    Shared dependencies were reused without installing into or modifying the root environment.
  - Export UI passed twice on unchanged current production/tests and once at base; its original
    exit -11 is a confirmed flake, deduplicated and tracked by PYPOST-1315.
  - All four Makefile modules passed at base; collecting two unchanged-tree focused reruns
    before closing their flake classification under existing PYPOST-1298.
  - Added preliminary `60-tech-debt.md` Follow-up Tasks with test IDs and existing Jira links;
    this records Step 5 triage and does not start or accept Step 7.
  - Both unchanged-tree Makefile reruns passed all four modules (72.84 s and 74.29 s).
    Their original failures are confirmed flakes under PYPOST-1298; exact commands and logs
    are in the cleanup report. All six remaining full-check failures are now classified.
  - Removed the fresh baseline worktree; root environment stamp timestamps stayed unchanged.
    No production or test edits were made during triage. Independent acceptance remains pending.
  - Post-triage `make lint-docs verify-ai-tasks` passed; detailed output is in
    `/tmp/p1266-step5-triage-artifacts.log`.
- [x] **STEP 6: Observability**
  - Reviewing retained worker outcome logs, action lifecycle diagnostics, and import metrics
    against the typed cancellation contract; no additional instrumentation is planned.
  - Created `50-observability.md`; existing structured event messages and bounded import
    outcome metrics cover this contract change. No production or test changes were needed.
  - Four focused retained-log regressions passed through `make test` across three modules:
    legacy-reader errors, cancellation/state context, and wait completion/timeout diagnostics.
  - `make lint-docs verify-ai-tasks` passed. No new issues or blockers were found;
    Step 6 remains in progress pending independent acceptance.
- [x] **STEP 7: Technical Debt Analysis**
  - Reviewing accepted requirements, architecture, source/test changes, and failure triage.
  - Expanded `60-tech-debt.md` with shortcuts, quality, coverage, explicit timeouts, performance,
    architecture alignment, and retained failure evidence; no new debt or blocker was found.
  - Remaining latency, lifecycle, and broader coverage limits reuse PYPOST-1267, PYPOST-1264,
    and PYPOST-1265; test lint coverage reuses PYPOST-1303. No duplicate issues are needed.
  - Preserved exact failure IDs and non-blocker classifications under PYPOST-1298, PYPOST-1299,
    and PYPOST-1315. The corrected SOLID snapshot is distinguished from those six failures.
  - `make lint-docs verify-ai-tasks` passed; no production/test edits or passing-test reruns.
    Step 7 remains in progress for independent acceptance by the autonomous orchestrator.
- [x] **STEP 8: Dev Docs**
  - Updating `doc/dev/collection_import.md` for the required typed reader checkpoint contract.
  - Documented structural `ReadImportFile`, required keyword invocation, supported/opaque shapes,
    checkpoint exception propagation, single-argument rejection, and retained synchronous parser API.
  - Updated architecture, injection guidance, focused test command, configuration, migration
    troubleshooting, decoding/record latency limits, residual publication race, and follow-up scope.
  - `make lint-docs verify-ai-tasks` passed: 16 user docs linted, 18 relative-link files checked,
    and 391 completed task artifacts accepted with two grandfathered legacy gaps.
    Those targets do not check this developer guide; its changed passages were reviewed directly
    against accepted source/test evidence and await independent documentation review.
  - No production/test changes, new issues, or repeated full-suite run; Step 8 remains in progress.
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1266/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1266/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_collection_import_reader_contract.py`
- `tests/test_collection_import_progress.py`

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1266/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1266/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1266/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/collection_import.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
