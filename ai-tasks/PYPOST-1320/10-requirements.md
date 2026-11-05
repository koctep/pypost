# PYPOST-1320: Flaky hang when hang-resistant wait arms while import worker logs errors

## Goals

Maintainers and contributors rely on Make quality gates (`make test` / `make check`) to
finish with a clear pass or fail. An intermittent hang appears when automated checks wait
through the shared hang-resistant wait helper while a collection-import background worker
is logging an error with full exception context. The main thread never returns to Python,
so ordinary per-test timeouts do not fire; the worker process only dies after the much
longer parallel-runner timeout. The flake was found during PYPOST-1264 Step 4 triage and
already reproduces at base commit `c3f8e183` (pre-existing, not introduced by that task).

**Business goal**: restore a trustworthy, finishing quality signal for every suite that
uses the shared hang-resistant wait—especially collection-import teardown and import-UI
checks—by eliminating this deadlock class, keeping the hang-regression mode that still
fails when event-loop timer slots never run, and proving the fix under stress so a ~1/7
to ~2/12 intermittent hang does not return unnoticed.

**Implementation language**: Python.

## User Stories

- **US1 (maintainer, quality gate)**: As a maintainer running parallel or full-suite
  `make test`, I want waits that use the shared hang-resistant helper to finish with a
  definite pass or fail within normal suite bounds, so a green or red result is not
  replaced by a silent hang until the parallel-runner worker timeout.
- **US2 (contributor, collection import checks)**: As a contributor running collection
  import teardown and import-UI checks through Make, I want those checks to complete
  reliably even when a background import worker logs an unexpected error with exception
  context, so local and CI results agree and I am not chasing environment-only hangs.
- **US3 (maintainer, hang-regression mode)**: As a maintainer, I want the shared wait’s
  hang-regression mode—used when event-loop timer slots must not be the only progress
  path—to still trip when those timers never run, so prior hang defenses
  (PYPOST-823 / PYPOST-827 / PYPOST-877 / PYPOST-1148 lineage) are not weakened.
- **US4 (maintainer, shared consumers)**: As a maintainer, I want every automated module
  that already depends on the shared hang-resistant wait to keep finishing, bounded
  wait behavior after this fix, so stability for one flake does not regress ~21 other
  consumers.
- **US5 (maintainer, evidence)**: As a maintainer, I want bounded, repeatable stress
  evidence for this intermittent hang class before and/or after the fix, so acceptance
  is not a single lucky green run.

## Definition of Done

1. **Hang class eliminated.** Automated runs no longer hang indefinitely (or until the
   parallel-runner worker timeout alone) because the shared hang-resistant wait arms
   while a collection-import background worker is logging an error with exception
   context. Affected scenarios include at least:
   - `tests/test_collection_import_teardown_repro.py` —
     `test_unexpected_reader_exception_requires_teardown_and_reaps_worker`
   - `tests/test_collections_import_ui.py` —
     `test_zero_candidates_treated_as_invalid_file`
2. **Definite outcome within suite bounds.** Waits that use the shared helper end with a
   clear pass or fail. Ordinary suite timeout mechanisms remain meaningful: the main
   thread must not remain permanently blocked so that per-test timeout enforcement never
   gets a chance to run.
3. **Hang-regression mode preserved.** The shared wait’s mode that detects stalls when
   event-loop timer slots never run (`use_poll_timer=False` hang-regression contract)
   still reports failure within its deadline in that situation. This capability remains
   available to all current consumers of the helper.
4. **Consumer behavior preserved.** All existing automated modules that use the shared
   hang-resistant wait continue to get hang-resistant, time-bounded waits with the same
   business meaning of their assertions. Stability is not achieved by removing those
   waits, skipping the tests, or disabling hang-regression coverage.
5. **Product behavior unchanged.** Collection import product outcomes (including how
   unexpected reader errors surface and how workers are torn down) are not intentionally
   weakened or rewritten away to hide the hang. Product changes are in scope only if a
   genuine product defect must be fixed for honest verification.
6. **Stress-backed validation.** Acceptance includes bounded stress or repeated parallel
   Make runs sufficient to address the historically observed intermittent rates (on the
   order of roughly 1-in-7 to 2-in-12 processes under documented stress / targeted
   parallel recipes), not only a single focused green run.
7. **Repository gates.** Quality gates are exercised only through `make` targets; no new
   failures attributable to this task remain in the accepted validation runs.

## Task Description

### Problem

Under intermittent load, the quality gate hangs when a test uses the shared hang-resistant
wait while a collection-import parse worker is emitting an error log with exception
context. Observed stacks (via faulthandler under Make with a faulthandler timeout) show
the main thread blocked while arming the wait’s watchdog, the parse worker inside
exception-aware error logging, and the watchdog path itself stuck—so pytest’s usual
per-test timeout never fires and only the longer parallel-runner timeout (~120 s) ends
the worker.

Documented reproduction avenues (for later verification, not for this requirements
step to execute):

- Targeted parallel Make: collection-import / collections test selection with
  faulthandler timeout enabled, default workers, repeated.
- Stress: many repetitions of the scenario per process with elevated workers and a
  longer worker timeout.

Observed rough rates: current-tree stress ~2/12 processes; targeted parallel ~1/7;
base stress ~1/18; base full `make test` ~1/2. Classification is flaky by unchanged-tree
and base-commit evidence (`c3f8e183`), not a claim of a deterministic single-run failure.

### Business reason

A quality gate that hangs until an outer worker kill is not a usable signal. It burns CI
time, blocks delivery, and hides whether collection-import teardown and import-UI
coverage still hold. The hang-resistant wait was introduced so suites finish; a deadlock
inside that wait undermines that investment across every consumer. The business need is
stable, honest completion of those checks—not workarounds that drop hang defense or skip
tests.

### Implementation language

Python.

### Scope

**In scope:**

- Eliminating the intermittent hang where shared hang-resistant waiting and concurrent
  collection-import worker error logging with exception context leave the suite stuck.
- Preserving hang-regression behavior when event-loop timer slots never run, for all
  current consumers of the shared wait helper (~21 test modules plus helper diagnostics).
- Keeping existing assertion intent for the named affected collection-import /
  collections-import UI checks and for other shared-wait consumers.
- Bounded stress or repeated parallel evidence appropriate to the intermittent rate.
- Validation exclusively through repository `make` targets.

**Out of scope:**

- Redesigning collection import product features, file formats, conflict handling, or
  user-visible import UX beyond what is required for honest, finishing verification.
- Changing parallel-runner infrastructure, pytest binary behavior, or CI host policy
  except as needed to demonstrate this hang class is gone.
- Unrelated flakes or native crashes outside this wait/worker-logging deadlock class
  (for example export-UI post-PASS segfaults tracked elsewhere).
- Broad rewrite of all test waits that do not use the shared hang-resistant helper.

### Functional requirements

1. Shared hang-resistant waits used by collection-import and related suites must complete
   with pass or fail under concurrent background worker error logging with exception
   context.
2. When hang-regression mode is selected, a stall in which event-loop timer slots never
   run must still produce a timed failure, not an indefinite hang and not a false pass.
3. Existing consumers of the shared helper retain hang-resistant, deadline-bounded waits
   and their current assertion meaning.
4. Acceptance evidence must address intermittency (stress or repeated parallel Make), not
   only one-shot focused success.

### Non-functional requirements

- **Reliability**: No intermittent indefinite hang of the documented class under normal
  parallel Make load or the documented stress recipe.
- **Boundedness**: Failures surface within suite-normal timeout expectations; the suite
  must not depend on the parallel-runner outer kill as the only recovery path for this
  class.
- **Maintainability**: Hang defense remains a single shared contract for consumers
  rather than one-off per-test workarounds that drift.
- **Tooling**: All install, test, and lint operations go through `make` targets per
  repository policy.

### Constraints and assumptions

- Implementation language is Python.
- The defect is pre-existing at `c3f8e183`; triage during PYPOST-1264 discovered it but
  did not introduce it.
- Related hang-resistant wait history (PYPOST-823, PYPOST-827, PYPOST-877, PYPOST-1148)
  establishes the hang-regression contract that must be preserved; this task does not
  reopen those product features.
- Intermittency means a single green focused run is insufficient acceptance evidence.
- Suggested implementation directions in the Jira ticket are hints for later design
  steps; this document specifies required outcomes only, not how the wait is implemented.
- Autonomous sprint-task-runner acceptance: the orchestrator marks Step 1 complete after
  independent review PASS; no interactive user approval gate in this run mode.

## Main Entities

- **Quality gate**: Make-driven automated suite that must finish with a clear outcome.
- **Shared hang-resistant wait**: Cross-suite wait contract that ends by success or
  deadline even when progress would otherwise depend only on event-loop timers.
- **Hang-regression mode**: Wait configuration that must still fail when event-loop
  timer slots never run (existing `use_poll_timer=False` contract).
- **Collection import background work**: Parse / import worker activity that may log
  unexpected errors with exception context while a test is waiting.
- **Affected automated checks**: Named teardown-repro and collections-import UI tests
  that have hung, plus the broader set of modules using the shared wait.
- **Stress evidence**: Bounded repeated / parallel Make runs sized to the observed flake
  rate, used to confirm the hang class before and/or after the fix.

## Q&A

- **Why is this needed?** Intermittent hangs until the parallel-runner timeout destroy
  trust in Make gates and waste CI capacity; hang-resistant waits must themselves finish.
- **Is this a product feature change?** No. Primary goal is reliable finishing
  verification. Product code changes only if required for honest coverage.
- **Must hang-regression mode stay?** Yes. Mode that trips when event-loop timer slots
  never run remains mandatory for all current shared-wait consumers.
- **Why stress evidence?** Historical rates are roughly 1/7–2/12 under stress/parallel;
  a single focused pass can miss the flake.
- **Does “suggested direction” in Jira bind Step 1?** No. It informs later architecture;
  requirements state outcomes (no hang; preserve hang-regression; keep consumers;
  stress proof), not a concrete design.
- **Who accepts the requirements?** The autonomous sprint orchestrator after independent
  review PASS.
