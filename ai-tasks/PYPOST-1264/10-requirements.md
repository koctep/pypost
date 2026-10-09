# PYPOST-1264: Consolidate collection import teardown policy

## Goals

Make the way collection import work is stopped and released at shutdown or panel teardown a
single, named, documented policy, so maintainers can reason about how long closing the
application may wait for import work and change those limits in one place.

The business reason is follow-up item 4 of
[PYPOST-1229 technical debt](../PYPOST-1229/60-tech-debt.md), later reaffirmed by
[PYPOST-1266](../PYPOST-1266/60-tech-debt.md) and [PYPOST-1267](../PYPOST-1267/10-requirements.md),
which both deferred teardown wait policy to this issue. Today the time limits that govern import
teardown are inherited literals (a 5000 ms default and a 100 ms worker-finish wait) repeated
across several entry points without a stated rationale. Users experience these limits as how long
closing the application can hang on an import, or whether abandoned import work is cleanly
released. Maintainers cannot tell whether the values are deliberate, how they combine, or whether
they should be adjustable.

The issue also asks to "evaluate configurability after latency measurement". This task must
produce a recorded, evidence-based decision; it does not presuppose that a configuration option
will be added.

## User Stories

- As a user closing the application during a collection import, I want shutdown to finish within
  its stated time limit and to abandon the import without adding or changing collections.
- As a user closing the application when no import is running, I want no added delay.
- As a maintainer, I want every collection import interruption and wait limit to come from one
  named lifecycle policy with documented values and rationale, so I change it in one place.
- As a maintainer, I want measured teardown latency and a recorded decision on configurability,
  so the limits are justified by evidence rather than inheritance.

## Definition of Done

1. **Single named policy.** Every interruption and wait time limit used by collection import
   wait-for-idle and teardown behavior, for both file import and connected-library import work,
   is defined by one named lifecycle policy. No collection import wait or teardown behavior uses
   an unnamed duplicate of the 5000 ms or 100 ms values. The collections presenter's import
   wait and teardown entry points use the same policy defaults as the import actions.
2. **Documented values.** Each limit in the policy has a stated purpose (for example: overall
   teardown budget, final worker join after disconnection, worker-finish join after normal
   completion) and a rationale. Unless measurement justifies a change, the effective values remain
   5000 ms and 100 ms.
3. **Caller budget is honored.** When a caller supplies a teardown time budget, the total time
   collection import teardown spends waiting for its file-import and library-import work does not
   exceed that budget beyond a small documented tolerance. In particular, sequential phases of
   teardown must not each receive the full budget. An exhausted or zero budget results in a prompt
   unclean result rather than further waiting.
4. **Preserved outcomes.** Observable teardown behavior is otherwise unchanged:
   - Idle teardown returns a clean result without measurable waiting.
   - Teardown during an active file import requests cooperative interruption, never forcibly
     terminates work, and returns clean when work stops within budget and unclean when it does not.
   - After teardown, no import results, progress, completion, failure, or cancellation outcome
     reaches the user interface, and no collections are added or modified.
   - Workers are released after teardown, and the existing structured teardown log events and
     their meaning remain available.
   - Repeated teardown calls remain safe.
5. **Latency measurement.** Teardown latency is measured in at least these scenarios: no import
   running; active file import cancelled during teardown; active connected-library operation
   during teardown. Each measurement records the scenario, the observed elapsed time (or
   distribution where repeated), and the environment conditions.
6. **Recorded configurability decision.** Based on those measurements, a decision is recorded
   in developer documentation: either the limits remain fixed policy values, or a specific limit
   becomes configurable. The record states the measured values, the chosen outcome, and why.
   Adding a user- or settings-visible configuration option is required only if the recorded
   decision calls for it; "remain fixed, with rationale" is an acceptable outcome.
7. **Automated checks.** Automated tests cover clean idle teardown, clean teardown of an active
   interruptible import, unclean teardown when import work exceeds the budget, and caller-budget
   adherence across sequential teardown phases. Tests use explicit timeouts and bounded waits.
8. Repository gates run through `make` targets; no new failures are attributable to this task.

## Task Description

Collection import runs file parsing and connected-library operations in background work. When
the collections area is torn down (normally as part of application shutdown, which distributes a
shared deadline across owners), import work must be interrupted, waited for within a limit,
disconnected from the user interface, and released. These limits are currently inherited
literals: a 5000 ms default on several import wait and teardown entry points and a 100 ms join
used both after disconnection and after normal worker completion. How the phases share the
caller's budget is not defined, so a single teardown can wait for longer than the budget given to
it. This task names and documents the policy, makes the import teardown respect the budget as a
whole, and decides on configurability from measured evidence.

The implementation language is Python. How the policy is represented and wired belongs to Step 2;
this document defines required observable behavior and outcomes.

### Non-functional Requirements

- No forcible termination of background work; interruption remains cooperative.
- Application shutdown remains bounded; teardown must not block indefinitely.
- No added delay when no import work is active.
- Diagnostics must not expose imported collection content.

### Constraints and Assumptions

- Scope is limited to collection import wait-for-idle and teardown behavior (file and
  connected-library import work) and the collections presenter entry points that delegate to it.
- Out of scope: the application-wide shutdown budget and its per-owner allocation; identical
  100 ms literals in unrelated components (storage gateways, settings, websocket views); decoding
  responsiveness (PYPOST-1267); the reader cancellation contract (PYPOST-1266); broader
  cancellation lifecycle test coverage (PYPOST-1265); import planning, conflict resolution, and
  collection application. Similar consolidation elsewhere may be recorded as follow-up debt.
- Measurements are taken in the project's normal test environment and are not hard real-time
  guarantees under operating-system stalls or resource exhaustion.
- The budget-adherence requirement (DoD 3) is derived from the issue's goal of one coherent
  policy and from the shared application shutdown deadline; it is an assumption accepted by the
  autonomous requirements review.

## Main Entities

- **Import lifecycle policy**: the single named set of time limits governing interruption and
  waiting for collection import work, with purpose and rationale for each.
- **Teardown budget**: the time a caller grants collection import teardown to finish.
- **Import work**: active background file parsing or connected-library operation.
- **Teardown result**: clean when all import work stopped and was released within budget;
  unclean otherwise.
- **Latency measurement**: recorded elapsed teardown times per scenario and environment.
- **Configurability decision**: the recorded outcome (fixed or configurable) with evidence.

## Q&A

- **Why is this needed?** Unexplained, duplicated limits make shutdown behavior hard to reason
  about and change; the debt item asks for one named policy and an evidence-based view on tuning.
- **Does "evaluate configurability" require a new setting?** No. It requires measurements and a
  recorded decision with rationale. A configuration option is added only if that decision says so.
- **Must the 5000 ms and 100 ms values change?** No. They are preserved unless measurement
  justifies a change, which must then be recorded with the decision.
- **Why include budget adherence?** Teardown is called with a share of a global shutdown
  deadline; a policy that lets sequential phases each use the full budget is not a coherent
  single policy.
- **Who accepts the requirements?** The autonomous sprint orchestrator after independent review.
