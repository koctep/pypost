# PYPOST-877: Hang-resistant wait for env-presenter async-load check

## Goals

PYPOST-823 and PYPOST-827 restored a finishing, hang-resistant wait for
encrypted-load responsiveness and for sibling environment/collection storage
gateway and worker checks. One related automated check remains exposed to the
same hang class: the environment-presenter check that async load with
encryption enabled refreshes the environment list. That check can still stall
the default quality gate when event-loop timers do not fire, instead of ending
with a clear pass or fail.

This task brings that remaining check onto the same hang-resistant wait
behavior already proven for PYPOST-823/827, so maintainers keep a finishing,
trustworthy quality gate for encrypted async environment load in the
presenter path—not only in gateway/worker and responsiveness modules.

## Programming Language

Python 3.10+

## User Stories

- As a **maintainer**, when I run the default test suite, I want the
  environment-presenter async-load-with-encryption refresh check to finish
  within a reasonable bound even if event-loop timers stall, so I am not left
  waiting indefinitely.
- As a **maintainer**, I want that check to use the same hang-resistant wait
  contract already used by PYPOST-823/827 consumers so wait behavior does not
  drift and the same hang class is not left half-fixed.
- As a **contributor**, I want the default quality gate to complete for this
  presenter async-load check so unrelated work is not blocked by a suite hang.
- As a **desktop user** (indirect), I want encrypted async environment load
  that refreshes the environment list to stay covered by automation that
  actually finishes, so regressions are not masked by stalled waits.

## Definition of Done

- The environment-presenter check that async load with encryption enabled
  refreshes the environment list finishes with a definite pass or fail and no
  longer hangs on a timer-only wait for async completion.
- Hang-resistant wait behavior for that check is equivalent to the
  PYPOST-823/827 wait: the wait ends by success or by deadline even when
  event-loop timers stall.
- That wait behavior comes from the shared hang-resistant wait definition
  already used by PYPOST-827 consumers (not a new independently maintained
  copy), or an equivalent hang-resistant wait with the same contract.
- Existing business meaning of the check is preserved: it still verifies that
  after async environment load with encryption enabled, the presenter reports
  load completion and the environment list reflects the loaded environments.
- No intentional change to product environment presentation, encryption, or
  user-visible load behavior (test-harness reliability only unless a real
  product defect is uncovered while restoring the wait).

## Task Description

**Problem:** After PYPOST-827, three gateway/worker sibling modules and the
responsiveness module use a hang-resistant wait. The environment-presenter
check for async load with encryption still waits with the older timer-only
pattern. If event-loop timers stall mid-suite, that check can hang the same
way pre-PYPOST-823/827 siblings did. Source:
[PYPOST-877](https://pypost.atlassian.net/browse/PYPOST-877), follow-up from
[PYPOST-827](https://pypost.atlassian.net/browse/PYPOST-827)
(`ai-tasks/PYPOST-827/60-tech-debt.md`).

**Business need:** Maintainers and CI need every related encrypted async
environment-load check to finish with a definite pass or fail. Closing
gateway/worker hang defense is incomplete if one presenter async-load check
can still stall the quality gate.

### In Scope

- Adopting PYPOST-823/827–equivalent hang-resistant wait behavior in the
  environment-presenter async-load-with-encryption refresh check.
- Preferring the existing shared hang-resistant wait definition already used
  by PYPOST-827 consumers so hang defense stays consistent.
- Preserving the existing assertions and business intent of that check.
- Leaving product environment-presenter and encryption runtime behavior
  unchanged unless a genuine defect is found that must be fixed for honest
  verification.

### Out of Scope

- Re-working encryption policy, on-disk formats, or user-facing environment UI.
- Broader suite redesign, marker policy changes, or unrelated flaky tests.
- Re-doing PYPOST-827 sibling gateway/worker modules (already done).
- Richer timeout diagnostics (busy/pending / worker state in failure text)—
  that remains [PYPOST-828](https://pypost.atlassian.net/browse/PYPOST-828).
- Aligning modules onto a shared Qt application fixture
  ([PYPOST-830](https://pypost.atlassian.net/browse/PYPOST-830)).
- Production worker lifecycle hygiene
  ([PYPOST-829](https://pypost.atlassian.net/browse/PYPOST-829)).
- Fixing unrelated presenter or suite failures tracked elsewhere.

## Functional Requirements

- The environment-presenter async-load-with-encryption refresh check must wait
  for async completion in a hang-resistant way: the wait always ends by a
  deadline, including when event-loop timers do not fire.
- Hang-resistant wait behavior must be equivalent to the PYPOST-823/827 wait
  for the same hang class (timer stall mid-suite).
- The check must obtain that wait behavior from the shared hang-resistant wait
  definition used by PYPOST-827 consumers, or an equivalent hang-resistant wait
  with the same contract (no new independently drifting copy of hang defense).
- The check must continue to assert the same business outcomes it does today:
  async load with encryption completes, and the environment list reflects the
  loaded environments.
- Failures of the waited condition must surface as clear test failures within
  the deadline, not as incomplete or indefinitely stalled runs.

## Non-functional Requirements

- **Reliability:** The check must not hang or require external kill when
  event-loop timers stall mid-suite.
- **Consistency:** Wait hang defense must match PYPOST-823/827 behavior so the
  suite does not leave one unsafe wait next to hardened siblings.
- **Maintainability:** Prefer the existing shared wait definition so future
  hang-defense fixes apply once.
- **Time-boundedness:** Stuck waits must fail within the configured timeout
  window rather than multi-minute stalls.
- **Scope discipline:** Prefer test-harness-only change; no product behavior
  change unless required for correct verification.

## Constraints and Assumptions

- Programming language: Python 3.10+.
- Prior work: PYPOST-823 hardened the responsiveness wait; PYPOST-827 shared
  that hang-resistant wait with three gateway/worker siblings and documented
  this presenter nested wait as Medium debt; this task closes that debt item.
- Target check (current name, for locating scope—not a design mandate):
  `tests/test_env_presenter.py::test_async_load_refreshes_combo_when_encryption_enabled`.
- Reference outcome: hang-resistant wait already used by PYPOST-827 consumers
  and the responsiveness module. Mechanism details belong in
  architecture/implementation, not here.
- “Shared definition” means reuse of the existing hang-resistant wait consumed
  by PYPOST-827 modules when practical; inventing a second hang-defense copy
  is not the acceptance goal.
- Approval for Step 1 artifacts is treated as granted under sprint-task-runner
  autonomy.

## Main Entities and Interactions

| Entity | Attributes (business) | Role |
| --- | --- | --- |
| Maintainer / contributor | Role, need for timely gate results | Runs the default quality gate |
| Default quality gate | Pass/fail outcome, finishing run | Automated suite that must finish |
| Env-presenter async-load check | Encryption-enabled load, list refresh outcome | Verifies presenter refreshes environments after encrypted async load |
| Hang-resistant wait | Deadline, completion condition, hang-class coverage (timer stall), pass/fail outcome | Time-bounded wait that ends even when event-loop timers stall |
| Shared wait definition | Single source, PYPOST-827 consumer set, equivalence to PYPOST-823 | One hang-resistant wait reused by this check |
| PYPOST-823/827 wait behavior | Proven hang-resistant outcome for the same hang class | Reference contract for equivalence |
| Encrypted async environment load | Load completion, environment list contents | Product capability under test (unchanged by intent) |

Interaction overview:

1. Maintainer runs the default quality gate.
2. The environment-presenter check exercises async environment load with
   encryption enabled.
3. The check waits for completion using the hang-resistant wait.
4. The wait ends by success or by deadline (including when event-loop timers
   stall).
5. The check reports pass or fail for list refresh; the suite continues
   without an indefinite hang.

## Q&A

- Q: Why is this more than “fix one wait call”?
  A: The business goal is a finishing quality gate for encrypted async
  environment-load coverage in the presenter path, with hang defense that does
  not drift from the PYPOST-823/827 contract.
- Q: Why ask “why” when the Jira text is already technical?
  A: The technical ask (port hang-resistant wait into the nested wait) serves
  the business need: stop suite hangs of the PYPOST-823/827 class in this
  remaining presenter async-load check and keep wait behavior consistent.
- Q: How does this relate to PYPOST-827?
  A: PYPOST-827 fixed hang-resistant waits for three gateway/worker siblings
  and left this presenter nested wait as out-of-DoD Medium debt. This task
  closes that follow-up.
- Q: Must product environment-presenter code change?
  A: No, by default. Only if current product behavior is wrong and the check
  cannot honestly finish otherwise.
- Q: Are richer timeout messages or a shared application fixture part of this
  task?
  A: No; those remain separate follow-ups (PYPOST-828, PYPOST-830).
- Q: Why omit wall-clock / posted-quit mechanism details here?
  A: Step 1 states outcomes only. Equivalence to PYPOST-823/827 and hang
  resistance under timer stall are the requirements; how that is achieved is
  architecture.
