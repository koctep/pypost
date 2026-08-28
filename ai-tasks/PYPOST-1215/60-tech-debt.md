# PYPOST-1215: Technical Debt Analysis

PYPOST-1215 (REPRO-1) established an owned, documented, and repeatable empirical baseline
of the intermittent failure of `tests/test_ui_actions.py::test_live_collection_tree_missing_option_raises`
under parallel test execution (`make test`), contrasting it with reliable passing behavior in
isolated single-node and single-file execution.

There is **no AC-breaking debt** in this story's deliverables. All tasks strictly adhere to the
scope boundaries established in [PYPOST-1205](https://pypost.atlassian.net/browse/PYPOST-1205):
root-cause diagnosis is deferred to DIAG-1 ([PYPOST-1216](https://pypost.atlassian.net/browse/PYPOST-1216))
and stabilization is deferred to FIX-1 ([PYPOST-1217](https://pypost.atlassian.net/browse/PYPOST-1217)).
Zero production code in `pypost/` was modified, and the behavioral assertion locks from
[PYPOST-975](https://pypost.atlassian.net/browse/PYPOST-975) remain completely intact.

Jira keys below that already exist are cited for context. **New follow-up issues are not created
in this step** (Phase D / orchestrator).

## Shortcuts Taken

1. **Reproduction via existing Make orchestrator targets without custom harness script.**
   Differential profiles were executed using standard Make-only commands
   (`make test PYTEST_ARGS="..."`, `make test WORKERS=16`) rather than introducing a temporary
   standalone stress-loop script in `scripts/`. This prevents transient script clutter in the
   codebase and strictly enforces the Make-only tooling standard (`AGENTS.md`).
2. **Empirical sampling matrix.** The differential run matrix (isolated node, isolated file,
   concurrent subset, full parallel suite) was evaluated across controlled sample runs (3 node runs,
   2 file runs, 1 subset run, 1 full suite run) rather than an unbounded multi-hour Monte Carlo
   loop, which is sufficient to establish the duration inflation baseline (+40.3%) without
   prolonging CI turnaround.
3. **Strict deferral of root-cause diagnosis.** In compliance with the decomposition boundaries
   in PYPOST-1205, diagnostic investigation into Qt `apply_theme` stylesheet parsing vs uvicorn
   thread lifecycles was intentionally not executed in this story and is reserved for DIAG-1
   ([PYPOST-1216](https://pypost.atlassian.net/browse/PYPOST-1216)).
4. **No production or test assertion modifications.** No modifications to `pypost/` or
   `tests/test_ui_actions.py` were attempted in this baseline capture slice.

## Code Quality Issues

1. **No production code touched.** Zero lines of production code in `pypost/` were modified.
2. **Artifact formatting and link hygiene.** All markdown deliverables in `ai-tasks/PYPOST-1215/`
   adhere to repository standards (line length <= 100 characters, valid relative links, clean
   document hierarchy).
3. **Strict Make-only compliance.** All test executions and artifact verifications use standard
   `make` entry points (`make test`, `make lint`, `make verify-ai-tasks`).

## Missing Tests

**Timeout markers: NO BLOCKER.**
All relevant test files declare explicit pytest timeout markers per `do-testing` requirements:
- `tests/test_ui_actions.py` declares `pytestmark = [pytest.mark.timeout(60), pytest.mark.agent_e2e]`
  at module scope.
- Subprocess worker timeout is enforced at `WORKER_TIMEOUT = 120s` by `scripts/run_parallel_tests.py`.

In-scope AC coverage is verified:
- Isolated node execution passes deterministically: `tests/test_ui_actions.py::test_live_collection_tree_missing_option_raises`.
- Full file execution passes deterministically: `tests/test_ui_actions.py` (14 tests).
- Behavioral negative assertion invariant verified: `UiTargetNotInteractableError` with
  `"option not found"` substring.

Deferred test enhancements (none are AC breaks for this story):
- **Automated multi-worker stress test suite.** An automated stress-test regression node running
  concurrent UI sessions is deferred to FIX-1 ([PYPOST-1217](https://pypost.atlassian.net/browse/PYPOST-1217))
  as part of the stabilization gate.

## Performance Concerns

1. **Execution Duration Inflation under Parallel Load (+40.3%).**
   Under full parallel suite execution (300 test files across 8 workers), the wall-clock execution
   time for `tests/test_ui_actions.py` inflates from 5.80s (isolated) to 8.14s (parallel load),
   representing substantial CPU scheduling and Qt event-loop dispatch contention.
2. **Worker Process Contention under High Concurrency.**
   When executing under elevated worker pools (`WORKERS=16`), contention for offscreen window
   creation and background loopback server threads increases the risk of worker subprocesses
   approaching the 120s `WORKER_TIMEOUT`.

## Follow-up Tasks

Phase D of the orchestrator creates Jira issues. Step 7 records follow-up context and citations.

1. **NON-BLOCKER — intentional downstream slice: Root-Cause Diagnosis (DIAG-1)**
   - Formulate, investigate, and confirm root-cause hypotheses for the parallel flake:
     1. Qt event loop pumping and `session.window.is_ui_ready` readiness polling delays.
     2. Qt stylesheet parsing contention (`apply_theme`).
     3. Concurrently running uvicorn/HTTP/MCP server thread lifecycles.
   - Anchor all traces against base commit `353370cdbd19c7a3338e2ed05c292b0a404d7b90`.
   - Verdict: **NON-BLOCKER — intentional downstream slice**.
   - Jira: [PYPOST-1216](https://pypost.atlassian.net/browse/PYPOST-1216)

2. **NON-BLOCKER — intentional downstream slice: Stabilization (FIX-1)**
   - Implement production/test fixes to eliminate parallel flake under `make test` and `make check`.
   - Ensure 100% pass rate under parallel load without relaxing timeouts or weakening the
     negative assertion contract (`UiTargetNotInteractableError` with `"option not found"`).
   - Verdict: **NON-BLOCKER — intentional downstream slice**.
   - Jira: [PYPOST-1217](https://pypost.atlassian.net/browse/PYPOST-1217)

3. **NON-BLOCKER — pre-existing flake (parent epic context)**
   - Target node: `tests/test_ui_actions.py::test_live_collection_tree_missing_option_raises`
   - Repro: intermittent failure / timeout under parallel `make test` load vs isolated pass.
   - Verdict: **NON-BLOCKER — pre-existing**.
   - Jira: [PYPOST-1188](https://pypost.atlassian.net/browse/PYPOST-1188)

4. **NON-BLOCKER — Step 8 Dev Docs of this task (not a new ticket)**
   - Document the empirical flake baseline and differential execution recipes in `doc/dev/testing.md`.
   - Owned by PYPOST-1215 Step 8.
   - Verdict: **NON-BLOCKER**.
   - Jira: none
