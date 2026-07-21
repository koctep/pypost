# PYPOST-829: Confirm or clear stranded storage-worker completion risk (H3)

## Goals

After background environment or collection storage work finishes, maintainers
need confidence that completion outcomes still reach listeners under heavy
automated Qt suite churn. PYPOST-823 recorded an optional hypothesis (H3):
finished storage workers may be released without orderly teardown, which
*might* strand load/save completion outcomes in later checks. That risk was
**not confirmed** while fixing the hang; this task exists to settle it.

The business outcome is a clear decision with evidence: either prove that
stranded load/save completions do **not** appear under representative suite
churn (and close without product change, or safely defer), or—if they
do—restore reliable completion delivery for both environment and collection
storage gateways without breaking queued follow-on load/save work, with
regression coverage so the defect cannot return unnoticed.

This is investigation-first debt. Most effort may be reproduction and
documentation; a product fix is conditional on confirmation.

## Programming Language

Python 3.10+

## User Stories

- As a **maintainer**, I want a documented answer—confirmed or not—to whether
  finished storage workers leave stranded load/save completions under heavy
  suite churn, so optional lifecycle work is not left as an unverified open
  risk.
- As a **maintainer**, if stranded completions are confirmed, I want both
  environment and collection storage gateways to finish worker teardown in a
  way that completion outcomes still arrive and pending load/save restarts are
  not raced or dropped.
- As a **contributor**, when a fix is required, I want a regression check so
  future changes cannot reintroduce stranded completions without failing the
  quality gate.
- As a **desktop user** (indirect), I want async environment and collection
  load/save to keep delivering completion outcomes reliably so the UI does not
  stall waiting for results that never arrive.

## Definition of Done

- Investigation has attempted to reproduce stranded load/save completion
  outcomes under representative heavy Qt suite churn (or an equivalent
  stress scenario agreed in architecture), with findings recorded in task
  artifacts.
- **If not reproduced:** evidence that H3 is not needed (or may be safely
  deferred) is documented; no mandatory product change; Steps 1–7 artifacts
  still complete; ticket may close with that evidence.
- **If reproduced:** environment and collection storage gateways both ensure
  orderly teardown of a finished worker such that subsequent load/save
  completion outcomes are delivered reliably, without racing or dropping a
  pending queued load/save restart after finish.
- When a product fix is applied, a regression check covers the stranded-
  completion failure mode (or an agreed proxy that would fail if teardown
  again strands outcomes).
- No intentional change to encryption policy, on-disk formats, or
  user-visible persistence UX beyond what is required to keep completion
  delivery correct.
- Task artifacts for Steps 1–7 exist regardless of confirm/fix vs
  not-confirmed path.

## Task Description

**Problem:** PYPOST-823’s architecture named H3: after a storage worker
finishes, the gateway clears its worker reference without orderly teardown
hygiene. Under heavy Qt suite churn, that *might* disturb later signal
delivery so load/save completion outcomes never arrive (stranded), causing
flaky or hanging async checks. PYPOST-823 did not confirm H3; product
lifecycle was left unchanged. Source:
[PYPOST-829](https://pypost.atlassian.net/browse/PYPOST-829), follow-up from
[PYPOST-823](https://pypost.atlassian.net/browse/PYPOST-823).

**Business need:** Close the open “maybe” with evidence. Maintainers should
not carry an untested lifecycle risk indefinitely, nor apply speculative
product changes. If the risk is real, both storage gateways must behave
safely for users and for the quality gate; if not, document and stop.

### In Scope

- Investigating whether stranded load/save completion outcomes appear under
  heavy Qt suite churn (or equivalent stress) for environment and/or
  collection storage async paths.
- Documenting investigation findings and the confirm/not-confirm decision.
- If confirmed: restoring reliable completion delivery after worker finish for
  **both** environment and collection storage gateways, without racing pending
  load/save restart after finish.
- If confirmed: adding regression coverage for the stranded-completion mode.
- Completing Steps 1–7 workflow artifacts either with a fix or with
  not-needed/deferred evidence.

### Out of Scope

- Re-doing hang-resistant wait work (PYPOST-823 / PYPOST-827).
- Richer wait timeout diagnostics (PYPOST-828).
- Aligning modules onto a shared Qt application fixture (PYPOST-830).
- Redesigning encryption, key handling, or on-disk storage formats.
- Broader suite redesign, marker policy, or unrelated flaky tests
  (e.g. tabs-presenter close-focus failures).
- Speculative product lifecycle changes when investigation does not show
  stranded completions.

## Functional Requirements

- The task must produce a recorded investigation outcome: H3 reproduced, or
  not reproduced under the agreed stress approach.
- If not reproduced, the task may complete without product code change,
  provided findings justify “not needed” or “safely deferred.”
- If reproduced, after a storage worker finishes, both environment and
  collection gateways must leave the system able to deliver the next load/save
  completion outcomes to listeners (no stranded completions attributable to
  post-finish worker release).
- If reproduced, tearing down a finished worker must not prevent a pending
  queued load or save from starting correctly after finish (no race that drops
  or corrupts the restart of pending work).
- If a product fix is applied, automated regression coverage must detect
  recurrence of stranded completions (or an agreed equivalent failure signal).
- Product encryption and persistence safety baselines remain unchanged unless
  a genuine defect must be fixed for correct completion delivery.

## Non-functional Requirements

- **Evidence-first:** Prefer documented reproduction (or failed reproduction)
  over speculative product change.
- **Reliability:** When a fix is required, load/save completion delivery under
  suite churn must be stable enough for the default quality gate.
- **Safety of pending work:** Worker finish handling must preserve correct
  restart of queued load/save (single-flight / pending semantics unchanged in
  business terms).
- **Scope discipline:** Environment and collection gateways stay aligned if
  either needs a fix; do not leave one gateway with the known defect.
- **Clarity:** Investigation notes and DoD path (fix vs close-with-evidence)
  must be understandable from task artifacts alone.

## Constraints and Assumptions

- Programming language: Python 3.10+.
- Prior work: PYPOST-823 restored hang-resistant encrypted-load checks and
  deferred H3 as optional Low follow-up; PYPOST-827/828 addressed wait sharing
  and timeout diagnostics without confirming H3.
- Parent / related: [PYPOST-823](https://pypost.atlassian.net/browse/PYPOST-823);
  see also `ai-tasks/PYPOST-823/` and `doc/dev/environment_storage_async.md`.
- H3 remains a hypothesis until this task’s investigation says otherwise.
- “Stranded load/save signals” means completion (or failure) outcomes that
  listeners expect after background storage work never arrive, despite the
  worker having finished its work.
- “Heavy Qt churn” means representative multi-module / full-suite pressure
  where Qt event delivery has historically been flaky; exact stress method is
  architecture/implementation.
- Approval for Step 1 artifacts is treated as granted under sprint-task-runner
  autonomy.

## Main Entities and Interactions

| Entity | Attributes (business) | Role |
| --- | --- | --- |
| Maintainer / contributor | Need for evidence-based risk closure | Runs suite; decides from findings |
| Default quality gate | Pass/fail, suite churn | Context where stranded outcomes may appear |
| Environment storage gateway | Async load/save, pending restart after finish | One of two gateways in scope if fix needed |
| Collection storage gateway | Async load (and pending restart), analogue risk | Must stay consistent if env gateway is fixed |
| Storage worker | Background load/save unit of work; finished state | Source of completion outcomes |
| Load/save completion outcome | Success or failure delivered to listeners | Must not strand after worker finish |
| Pending load/save | Queued work waiting for current worker to finish | Must still start correctly after teardown |
| H3 investigation | Reproduce / not-reproduce evidence | Gate for whether product change is required |

Interaction overview:

1. Maintainer (or agent) stresses async storage paths under heavy Qt suite churn.
2. Investigation records whether load/save completion outcomes strand after
   workers finish.
3. If not: document evidence; complete remaining workflow artifacts; close or
   defer without mandatory product change.
4. If yes: both gateways ensure orderly post-finish teardown so completions
   still arrive and pending work still restarts; add regression coverage;
   complete remaining artifacts.

## Q&A

- Q: Why investigate instead of always applying the suggested lifecycle change?
  A: H3 was never confirmed. Speculative product changes risk racing pending
  load/save restart. Business value is a settled risk, not an unforced edit.
- Q: What is the business “why” behind orderly worker teardown?
  A: Listeners (UI and tests) must receive load/save completion outcomes after
  background work ends. If teardown strands those outcomes, the app or suite
  waits forever or flakes—undermining trust in async storage.
- Q: Why both environment and collection gateways?
  A: PYPOST-823 named the collection analogue explicitly. Leaving one gateway
  with the same defect would leave half the async storage surface unreliable.
- Q: Is a product fix required for Done?
  A: Only if stranded completions are reproduced. Not-confirmed with documented
  evidence also satisfies Done, provided Steps 1–7 artifacts exist.
- Q: How does this relate to PYPOST-823 / 827 / 828?
  A: 823 fixed hang-resistant waits and deferred H3; 827 shared the wait; 828
  enriched timeout text. This ticket only settles the optional worker-teardown
  hypothesis.
- Q: May we change pending load/save queue behavior?
  A: Not as a goal. Any fix must preserve correct restart of pending work after
  finish; redesign of single-flight/coalescing is out of scope.
- Q: Why omit naming specific Qt teardown APIs in requirements?
  A: Step 1 states outcomes (reliable completions; no race on pending restart).
  How teardown is implemented belongs in architecture if a fix is warranted.
