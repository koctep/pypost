# PYPOST-883: Investigate intermittent hang on save-async completion check

## Goals

Maintainers need confidence that the automated environment-storage gateway
suite finishes reliably under full-suite pressure. During PYPOST-830 Step 3,
one full `make test` run stalled on the check that verifies async environment
save emits a save-completed outcome. A one-off sample pointed at conflicting
cleanup between Qt widget teardown and a background environment-storage worker
across threads. The stall did not recur on retry or on focused presenter /
gateway clusters, and it was not caused by shared Qt-application fixture
alignment (focused gateway runs stayed green).

The business outcome is a settled risk: either reproduce the hang under suite
pressure and harden lifecycle ordering so the suite no longer stalls, or
document that the hang is unreproducible with enough evidence that maintainers
can close the open flake without speculative product change.

This is investigation-first debt. A product or harness fix is conditional on
reproduction (or a clear, evidence-backed root cause).

## Programming Language

Python 3.10+

## User Stories

- As a **maintainer**, I want a documented answer—reproduced and hardened, or
  unreproducible with evidence—for the intermittent full-suite stall on the
  async environment save-completed check, so CI and local full-suite runs are
  not left with an open hang risk from PYPOST-830 TD-1.
- As a **maintainer**, if the hang is reproduced, I want teardown / wait /
  cleanup ordering hardened so the suite completes instead of stalling when
  background environment-storage work and Qt cleanup interact under pressure.
- As a **contributor**, I want focused relevant suite clusters (environment
  storage gateway and closely related presenter / gateway surfaces called out
  for this investigation) to stay green after any hardening, so the fix does
  not trade one flake for another.
- As a **desktop user** (indirect), I want async environment save completion to
  remain reliable so the UI does not hang waiting for a save outcome that never
  arrives, if the investigation shows a real product lifecycle defect.

## Definition of Done

- Investigation has attempted to reproduce the intermittent hang on the async
  environment save-completed check under full-suite (or equivalent suite-
  prefix) pressure, with findings recorded in task artifacts.
- **If reproduced:** root cause is identified at a business level (lifecycle /
  cleanup conflict under suite pressure), and teardown / wait / cleanup
  ordering is hardened so the hang no longer occurs under the agreed stress
  approach; focused relevant suite clusters stay green.
- **If not reproduced:** unreproducible status is documented with evidence
  (attempts, clusters exercised, relation to prior green focused runs); no
  mandatory speculative product change; ticket may close with that evidence.
- Focused relevant suite clusters (at minimum environment storage gateway and
  any closely related presenter / gateway clusters used in the investigation)
  remain green under the default quality gate for those modules.
- No intentional change to encryption policy, on-disk formats, or
  user-visible environment persistence UX beyond what is required if a real
  hang-causing lifecycle defect is confirmed.
- Task artifacts for Steps 1–8 exist regardless of reproduce/harden vs
  unreproducible path.

## Task Description

**Problem:** PYPOST-830 recorded TD-1: during one full-suite run, the check
that async environment save emits save-completed stalled. Sampling suggested a
cross-thread cleanup conflict between Qt widget teardown and an environment
storage worker. Retry and focused presenter / gateway clusters did not
reproduce it; shared Qt-application fixture alignment was ruled out as the
cause. Source:
[PYPOST-883](https://pypost.atlassian.net/browse/PYPOST-883), follow-up from
[PYPOST-830](https://pypost.atlassian.net/browse/PYPOST-830) TD-1
(`ai-tasks/PYPOST-830/60-tech-debt.md`).

**Business need:** Close the open intermittent hang risk so maintainers trust
full-suite runs and do not carry an unexplained stall. Prefer evidence over
speculative lifecycle edits. If the hang is real under suite pressure, harden
cleanup ordering; if not, document and stop.

### In Scope

- Attempting reproduction under full-suite or suite-prefix pressure (or an
  equivalent stress approach agreed in architecture).
- Documenting investigation findings and the reproduce / unreproducible
  decision.
- If reproduced: hardening teardown / wait / cleanup ordering so the hang no
  longer stalls the suite under the agreed stress approach.
- Verifying focused relevant suite clusters stay green after any change (or
  after investigation-only closure).
- Completing Steps 1–8 workflow artifacts either with a harden path or with
  unreproducible evidence.

### Out of Scope

- Re-doing hang-resistant wait sharing (PYPOST-827), timeout diagnostics
  (PYPOST-828), or H3 worker-finish teardown confirmation (PYPOST-829), except
  where they are directly implicated by a confirmed root cause for this hang.
- Suite-wide Qt-application fixture migration (PYPOST-886 / PYPOST-830 TD-4).
- Aligning the collection storage worker module onto shared fixture
  (PYPOST-884 / PYPOST-830 TD-2).
- Style-only conversion of gateway TestCase modules to free functions
  (PYPOST-885 / PYPOST-830 TD-3).
- Clearing unrelated SOLID LOC baseline noise (PYPOST-882 / PYPOST-830 TD-5).
- Redesigning encryption, key handling, or on-disk storage formats.
- Broader suite redesign, marker policy, or unrelated flaky tests.

## Functional Requirements

- The task must produce a recorded investigation outcome: hang reproduced under
  suite pressure (or equivalent), or not reproduced with documented evidence.
- If not reproduced, the task may complete without product or harness code
  change, provided findings justify “unreproducible” with enough evidence for
  maintainers.
- If reproduced, lifecycle ordering for cleanup after async environment save
  (and any confirmed related path) must be hardened so the suite completes
  instead of stalling under the agreed stress approach.
- After any hardening, focused relevant suite clusters must remain green
  (environment storage gateway and closely related clusters used to validate
  the fix).
- Product encryption and persistence safety baselines remain unchanged unless
  a genuine hang-causing defect must be fixed for correct completion delivery.

## Non-functional Requirements

- **Evidence-first:** Prefer documented reproduction (or failed reproduction)
  over speculative lifecycle change.
- **Reliability:** When a harden path is taken, full-suite / suite-prefix runs
  must no longer stall on the async environment save-completed check under the
  conditions that reproduced the hang.
- **Scope discipline:** Do not expand into unrelated Qt test modules or
  deferred PYPOST-830 consistency items (TD-2–TD-5).
- **Clarity:** Investigation notes and DoD path (harden vs close-with-evidence)
  must be understandable from task artifacts alone.
- **Quality gate stability:** Focused relevant clusters stay green; any change
  must not introduce known new flakes on those surfaces.

## Constraints and Assumptions

- Programming language: Python 3.10+.
- Prior work: PYPOST-830 aligned gateway tests onto shared Qt-application
  fixture; TD-1 explicitly deferred this hang as out of fixture-alignment
  scope. Related hang/wait/teardown work lives in PYPOST-827–829.
- Parent / related: [PYPOST-830](https://pypost.atlassian.net/browse/PYPOST-830);
  debt item TD-1 in `ai-tasks/PYPOST-830/60-tech-debt.md`.
- The stall was observed once during full `make test`, did not reproduce on
  retry or focused presenter / gateway clusters, and is not attributed to
  `usefixtures("qapp")` alignment.
- “Suite pressure” means full-suite or substantial suite-prefix runs where
  Qt cleanup and background storage work interact; exact stress method is
  architecture / implementation.
- “Harden teardown / wait / cleanup ordering” is an outcome statement (suite
  no longer stalls); how ordering is achieved belongs in architecture if a
  fix is warranted.
- Story points: 5; issue type: Debt; priority: Medium; sprint: Gateway test
  stability.
- Approval for Step 1 artifacts is treated as granted under sprint-task-runner
  autonomy.

## Main Entities and Interactions

| Entity | Attributes (business) | Role |
| --- | --- | --- |
| Maintainer / contributor | Need settled hang risk | Runs suite; decides from findings |
| Default quality gate / full suite | Pass/fail under suite pressure | Context where the stall appeared once |
| Async environment save-completed check | Asserts save completion arrives | Observed stall target |
| Environment storage gateway | Async save path under test | Primary investigation surface |
| Background environment storage worker | Cross-thread storage unit of work | Implicated in sample as cleanup peer |
| Qt widget teardown / cleanup | Suite pressure side effects | Implicated in sample as cleanup peer |
| Focused relevant suite clusters | Gateway + related presenter/gateway | Must stay green after investigation |
| TD-1 investigation | Reproduce / unreproducible evidence | Gate for whether harden path is required |

Interaction overview:

1. Maintainer (or agent) attempts to reproduce the stall under suite pressure.
2. Investigation records whether the hang recurs and what cleanup conflict (if
   any) is confirmed.
3. If not: document unreproducible evidence; complete remaining workflow
   artifacts; close without mandatory speculative change.
4. If yes: harden teardown / wait / cleanup ordering so the suite completes;
   keep focused relevant clusters green; complete remaining artifacts.

## Q&A

- Q: Why investigate instead of immediately changing teardown / wait ordering?
  A: The hang appeared once and did not reproduce on retry or focused clusters.
  Speculative lifecycle edits risk new flakes. Business value is a settled
  risk with evidence, not an unforced edit.
- Q: What is the business “why” behind hardening if reproduced?
  A: Full-suite and CI runs must finish. A stall on save-completed undermines
  trust in the quality gate and may signal a real async-save completion risk
  for users.
- Q: Was this caused by PYPOST-830 fixture alignment?
  A: No. Focused gateway runs stayed green; TD-1 and the Jira description rule
  out `usefixtures("qapp")` as the cause.
- Q: Is a product or harness fix required for Done?
  A: Only if the hang is reproduced (or a clear root cause warrants hardening).
  Unreproducible with documented evidence also satisfies Done, provided
  Steps 1–8 artifacts exist and focused clusters stay green.
- Q: How does this relate to PYPOST-827 / 828 / 829 / 830?
  A: 827–829 owned wait sharing, timeout diagnostics, and H3 teardown. 830
  aligned gateway fixtures and deferred this intermittent hang as TD-1. This
  ticket only settles that hang risk.
- Q: Which clusters must stay green?
  A: At minimum the environment storage gateway module and the closely related
  presenter / gateway clusters used during investigation validation. Exact
  list is refined in architecture; requirements require “focused relevant”
  clusters, not a full-suite green mandate as sole DoD.
- Q: Why omit naming specific Qt teardown or GC APIs in requirements?
  A: Step 1 states outcomes (reproduce or document; harden ordering if found;
  clusters green). How cleanup is ordered belongs in architecture if a fix is
  warranted.
