# PYPOST-827: Reliable waits for sibling gateway/worker checks

## Goals

PYPOST-823 restored a time-bounded outcome for the encrypted-load responsiveness
check so the default quality gate no longer hangs when event-loop timers stall.
Three related automated checks for environment and collection storage
gateways/workers still wait with the older timer-only pattern. Those checks
remain exposed to the same hang class mid-suite: the run can stall until the
process is killed instead of finishing with a clear pass or fail.

This task brings those sibling checks onto the same hang-resistant wait
behavior already proven for PYPOST-823, defined once and reused, so maintainers
keep a finishing, trustworthy quality gate for this whole family of storage
async checks—not only the responsiveness module.

## Programming Language

Python 3.10+

## User Stories

- As a **maintainer**, when I run the default test suite, I want environment and
  collection storage gateway/worker checks to finish within a reasonable bound
  even if event-loop timers stall, so I am not left waiting indefinitely.
- As a **maintainer**, I want those checks to share one hang-resistant wait
  definition so wait behavior does not drift across modules and the same hang
  class does not recur in one place while fixed in another.
- As a **contributor**, I want the default quality gate to complete for this
  family of storage async checks so unrelated work is not blocked by a suite
  hang.
- As a **desktop user** (indirect), I want gateway/worker async behavior for
  environments and collections to stay covered by automation that actually
  finishes, so regressions are not masked by stalled waits.

## Definition of Done

- The three sibling check modules listed below finish with a definite pass or
  fail and no longer hang on timer-only waits for async completion:
  - environment storage gateway checks
  - collection storage gateway checks
  - collection storage worker checks
- Hang-resistant wait behavior for those modules is equivalent to the
  PYPOST-823 wait: the wait ends by success or by deadline even when
  event-loop timers stall.
- That wait behavior comes from a single shared definition used by all three
  modules (not three independently maintained copies).
- Existing business meaning of those checks is preserved: they still verify the
  intended async gateway/worker outcomes (signals / completion), now with
  reliable, time-bounded waits.
- No intentional change to product environment or collection storage behavior,
  encryption, or user-visible persistence (test-harness reliability only unless
  a real product defect is uncovered while restoring the waits).

## Task Description

**Problem:** After PYPOST-823, only the encrypted-load responsiveness module uses
a hang-resistant wait. Sibling gateway/worker check modules still use
timer-only waits. If event-loop timers stall mid-suite, those checks can hang
the same way the responsiveness check did before PYPOST-823. Source:
[PYPOST-827](https://pypost.atlassian.net/browse/PYPOST-827), follow-up from
[PYPOST-823](https://pypost.atlassian.net/browse/PYPOST-823).

**Business need:** Maintainers and CI need the whole related set of storage
async checks to finish with a definite pass or fail. One fixed module is not
enough if three siblings can still stall the quality gate. Shared wait behavior
prevents copy-drift so hang defense stays consistent.

### In Scope

- Adopting PYPOST-823–equivalent hang-resistant wait behavior in the three
  sibling environment/collection gateway and worker check modules.
- Providing that behavior via one shared wait definition consumed by those
  modules.
- Preserving the existing assertions and business intent of those checks.
- Leaving product storage/gateway/worker runtime behavior unchanged unless a
  genuine defect is found that must be fixed for honest verification.

### Out of Scope

- Re-working encryption policy, on-disk formats, or user-facing storage UI.
- Broader suite redesign, marker policy changes, or unrelated flaky tests.
- Richer timeout diagnostics (busy/pending / worker state in failure text)—that
  is a separate follow-up (PYPOST-828).
- Aligning modules onto a shared Qt application fixture (PYPOST-830).
- Production worker lifecycle hygiene (PYPOST-829).
- Fixing unrelated tabs-presenter failures tracked elsewhere.

## Functional Requirements

- Sibling environment and collection storage gateway/worker checks must wait for
  async completion in a hang-resistant way: the wait always ends by a deadline,
  including when event-loop timers do not fire.
- Hang-resistant wait behavior must be equivalent to the PYPOST-823 wait for the
  same hang class (timer stall mid-suite).
- All three listed sibling modules must obtain that wait behavior from one
  shared definition rather than maintaining separate copies.
- Checks must continue to assert the same business outcomes they do today
  (async load/save / worker completion as currently specified in those modules).
- Failures of the waited condition must surface as clear test failures within
  the deadline, not as incomplete or indefinitely stalled runs.

## Non-functional Requirements

- **Reliability:** Sibling checks must not hang or require external kill when
  event-loop timers stall mid-suite.
- **Consistency:** Wait hang defense must match PYPOST-823 behavior so the
  suite does not have one “safe” and several “unsafe” variants.
- **Maintainability:** One shared definition so future hang-defense fixes apply
  once.
- **Time-boundedness:** Stuck waits must fail within the configured timeout
  window rather than multi-minute stalls.
- **Scope discipline:** Prefer test-harness-only change; no product behavior
  change unless required for correct verification.

## Constraints and Assumptions

- Programming language: Python 3.10+.
- Prior work: PYPOST-823 hardened the wait in the responsiveness module and
  documented sibling copies as Medium debt; this task closes that debt item.
- Target modules (current names, for locating scope—not a design mandate):
  - `tests/test_environment_storage_gateway.py`
  - `tests/test_collection_storage_gateway.py`
  - `tests/test_collection_storage_worker.py`
- Reference outcome: hang-resistant wait already used by
  `tests/test_env_storage_responsiveness.py` (PYPOST-823). Mechanism details
  belong in architecture/implementation, not here.
- “Shared definition” means a single hang-resistant wait consumed by the three
  siblings; consolidating the responsiveness module onto the same definition is
  allowed if it keeps one definition, but is not required beyond the three
  listed modules.
- Approval for Step 1 artifacts is treated as granted under sprint-task-runner
  autonomy.

## Main Entities and Interactions

| Entity | Attributes (business) | Role |
| --- | --- | --- |
| Maintainer / contributor | Role, need for timely gate results | Runs the default quality gate |
| Default quality gate | Pass/fail outcome, finishing run | Automated suite that must finish |
| Sibling gateway/worker checks | Module family, async completion predicate, asserted outcome | Verify async environment/collection storage gateway and worker behavior |
| Hang-resistant wait | Deadline, completion condition, hang-class coverage (timer stall), pass/fail outcome | Time-bounded wait that ends even when event-loop timers stall |
| Shared wait definition | Single source, consumer set (three siblings), equivalence to PYPOST-823 | One hang-resistant wait used by the three sibling modules |
| PYPOST-823 wait behavior | Proven hang-resistant outcome for the same hang class | Reference contract for equivalence |
| Environment / collection storage async paths | Load/save / worker completion signals | Product capabilities under test (unchanged by intent) |

Interaction overview:

1. Maintainer runs the default quality gate.
2. Sibling gateway/worker checks exercise async storage operations.
3. Each check waits for completion using the shared hang-resistant wait.
4. The wait ends by success or by deadline (including when event-loop timers stall).
5. The check reports pass or fail; the suite continues without an indefinite hang.

## Q&A

- Q: Why is this more than “copy a wait into three files”?
  A: The business goal is a finishing quality gate for this whole family of
  checks, with hang defense that does not drift. One shared definition is the
  acceptance bar so the same hang class is not left half-fixed.
- Q: Why ask “why” when the Jira text is already technical?
  A: The technical ask (port hang-resistant wait / shared definition) serves the
  business need: stop suite hangs of the PYPOST-823 class in sibling storage
  async checks and keep wait behavior consistent.
- Q: How does this relate to PYPOST-823?
  A: PYPOST-823 fixed the hang in the responsiveness module and deferred sibling
  modules. This task applies the same hang-resistant wait contract there.
- Q: Must product gateway/worker code change?
  A: No, by default. Only if current product behavior is wrong and the checks
  cannot honestly finish otherwise.
- Q: Is aligning the responsiveness module onto the shared definition required?
  A: Not strictly; DoD requires the three sibling modules to use one shared
  definition with PYPOST-823–equivalent behavior. Unifying the responsiveness
  module onto that definition is optional if it strengthens the single-definition
  goal.
- Q: Are richer timeout messages or a shared application fixture part of this
  task?
  A: No; those are separate follow-ups (PYPOST-828, PYPOST-830).
- Q: Why omit wall-clock / posted-quit mechanism details here?
  A: Step 1 states outcomes only. Equivalence to PYPOST-823 and hang resistance
  under timer stall are the requirements; how that is achieved is architecture.
