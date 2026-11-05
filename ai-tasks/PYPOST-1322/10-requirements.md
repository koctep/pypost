# PYPOST-1322: Test nested worker-finish join during collection import teardown

## Goals

Lock in the accepted collection-import teardown contract for the nested worker-finish wait:
when worker-finish handling runs during teardown's wait-for-idle event pumping, any budget
overrun stays within the documented worker-finish join allowance, and the existing
worker-finish wait-timeout warning is emitted when that join stalls.

The business reason is follow-up 7 of
[PYPOST-1264 technical debt](../PYPOST-1264/60-tech-debt.md) (design Risk 3). PYPOST-1264
documented that this nested join is intentionally not capped by the remaining teardown
deadline, and that the pathological stall case is bounded by the worker-finish join limit and
made visible by a warning. That guarantee is not yet covered by an automated check, so a
regression could silently change how long teardown may overrun or drop the diagnostic signal
operators and maintainers rely on.

Production already behaves this way. This task is characterization only: prove and protect the
documented overrun bound and warning, without changing product behavior.

## User Stories

- As a maintainer, I want an automated check that when worker-finish handling runs nested
  inside collection import teardown's wait-for-idle pumping and its join exceeds what remains
  of the caller budget, the extra wait is no larger than the worker-finish join allowance.
- As a maintainer, I want that same check to show the worker-finish wait-timeout warning is
  emitted when the nested join stalls, so the accepted Risk 3 diagnostic remains part of the
  contract.
- As a maintainer, I want this proof to sit with the existing collection import teardown policy
  tests, so future budget or join changes cannot drop the Risk 3 characterization unnoticed.

## Definition of Done

1. **Nested join scenario covered.** An automated test exercises collection import teardown
   such that worker-finish handling runs during the wait-for-idle phase of teardown, and that
   handling's worker-finish join exceeds the remaining caller budget.
2. **Overrun bound asserted.** The test asserts that any teardown time beyond the caller
   budget attributable to that nested join is bounded by the worker-finish join allowance from
   the collection import lifecycle policy (not unbounded and not larger than that allowance).
3. **Warning asserted.** The test asserts that the existing worker-finish wait-timeout warning
   for collection import is emitted when that nested join stalls.
4. **Characterization only.** No intentional change to production teardown, policy values, or
   warning meaning. Observable product behavior remains as documented after PYPOST-1264.
5. **Test quality.** The new coverage uses explicit timeouts and bounded waits consistent with
   the repository's testing rules, and lives with the existing collection import teardown
   policy test module (or an equally appropriate sibling under `tests/` if that module cannot
   host it without harming clarity).
6. Repository gates run through `make` targets; no new failures are attributable to this task.

## Task Description

### Problem

Collection import teardown shares a caller time budget across its phases. During wait-for-idle,
event pumping can deliver a queued worker-finish handler. That handler may still wait up to the
full worker-finish join allowance even when little or no budget remains. PYPOST-1264 accepted
this as design Risk 3: the overrun is intentionally uncapped by the remaining deadline, is
normally negligible, and in the stall case is bounded by the join allowance and surfaced by a
warning. No automated test currently demonstrates that bound or the warning under the nested
path.

### Business reason

Maintainers and operators need the documented Risk 3 contract to stay true: teardown must not
grow an unbounded nested wait, and the stall case must remain diagnosable. Without a
characterization test, a future change could quietly lengthen shutdown hangs or remove the
warning while green suites still pass.

### Implementation language

Python.

### Scope

- Add automated characterization coverage for the nested worker-finish join during collection
  import teardown wait-for-idle, including overrun bound and warning emission.
- Reuse the existing teardown policy test fixtures and helpers where they already support
  deterministic timing and worker observation.

### Out of scope

- Changing production teardown, lifecycle policy defaults, or warning text/meaning.
- Capping the nested join by the remaining teardown deadline (accepted Risk 3 decision from
  PYPOST-1264; changing that would be a separate product decision).
- Long GUI-slot overrun during APPLYING (other Risk 3 facet; deferred / covered elsewhere).
- Broader cancellation lifecycle matrices (PYPOST-1265).
- Registering collections with main-window shutdown (PYPOST-1321) or other PYPOST-1264
  follow-ups.

### Non-functional Requirements

- Deterministic enough for CI: prefer controlled timing over wall-clock flakiness.
- No unbounded waits in the new test.
- No new production logging or metrics required beyond asserting the existing warning.

### Constraints and Assumptions

- Production already implements the accepted Risk 3 behavior; the red-to-green path is adding
  the missing characterization test, not fixing a product defect.
- The collection import lifecycle policy already defines the worker-finish join allowance and
  the worker-finish wait-timeout warning already exists.
- Existing helpers in `tests/test_collection_import_teardown_policy.py` are assumed sufficient
  or extendable for this scenario; inventing a new harness is optional only if those helpers
  cannot express the nested join case.

## Main Entities

- **Teardown budget**: the time a caller grants collection import teardown to finish.
- **Wait-for-idle phase**: the teardown phase that pumps events until import work is idle or
  the shared budget is exhausted.
- **Worker-finish handling**: the normal completion path that joins a finished import worker
  using the worker-finish join allowance.
- **Nested join overrun**: extra wait from worker-finish handling that runs inside
  wait-for-idle pumping after the remaining budget is too small for that join.
- **Worker-finish join allowance**: the policy limit that caps how long the nested join may
  wait in the stall case.
- **Worker-finish wait-timeout warning**: the existing diagnostic emitted when that join does
  not complete within its allowance.

## Q&A

- **Why is this a debt/test ticket rather than a product fix?** PYPOST-1264 deliberately kept
  the nested join uncapped by the remaining deadline (Risk 3). The gap is missing automated
  proof of the documented overrun bound and warning, not incorrect production behavior.
  Source: [PYPOST-1264 follow-up 7](../PYPOST-1264/60-tech-debt.md).
- **What is the business value of a characterization test?** It protects shutdown hang bounds
  and diagnosability: maintainers can change teardown or join policy later without silently
  losing the Risk 3 contract.
- **Why not also cover long GUI slots during APPLYING?** That is a separate Risk 3 facet,
  out of scope for this ticket and already deferred relative to APPLYING rollback /
  PYPOST-1265 lifecycle coverage.
- **Is production behavior expected to change?** No. Estimate and issue text state
  production already behaves this way; work is test-only.
