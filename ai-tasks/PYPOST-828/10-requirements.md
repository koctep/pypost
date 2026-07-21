# PYPOST-828: Richer timeout diagnostics for Qt wait failures

## Goals

When a hang-resistant Qt wait in automated storage async checks times out,
maintainers today see only a generic “condition not met within Nms” message.
That tells them the wait failed, but not *why* the system still looked busy or
incomplete—so triage requires re-running, adding temporary logging, or guessing
whether load/save was still in flight, pending work remained, or a worker was
stuck.

This task makes timeout failures self-explanatory: the failure report must
carry actionable diagnostic context (busy/pending status and, when relevant,
worker state) so developers can triage wait failures quickly from a single
failed run. It is the diagnostics follow-up deferred from PYPOST-823 /
PYPOST-827; it does not re-do the sibling wait port.

## Programming Language

Python 3.10+

## User Stories

- As a **maintainer**, when a hang-resistant Qt wait times out in storage async
  checks, I want the failure message to include busy/pending context so I can
  tell whether work was still in progress when the deadline hit.
- As a **maintainer**, when the waited scenario involves a worker, I want
  optional worker-state context in the timeout report so I can distinguish a
  stalled worker from a predicate that simply never became true.
- As a **contributor**, I want timeout diagnostics rich enough that I do not
  need a second local debug pass just to learn what was still pending.
- As a **desktop user** (indirect), I want storage async regressions to be
  diagnosable quickly in CI so maintainers fix real defects instead of spending
  time decoding opaque wait failures.

## Definition of Done

- When the shared hang-resistant wait used by storage async checks times out,
  the failure report includes actionable diagnostic context beyond the generic
  “condition not met within Nms” wording (at least timeout duration and why
  the wait ended as a timeout).
- For waits that observe storage async load state (the primary use case),
  timeout diagnostics MUST include busy/pending status for that load state.
- Busy/pending may be omitted only when those flags are not part of that
  wait’s business context; the report must still be actionable via timeout
  duration and reason.
- When a worker is part of the waited scenario, optional worker-state context
  is available in the timeout report (or clearly omitted when not applicable).
  Worker state remains optional and is never required for every wait.
- Timeout failures remain definite test failures within the existing deadline;
  diagnostics enrich the failure, they do not change hang-resistant wait
  timing or pass/fail semantics of the waited condition.
- Existing hang-resistant wait behavior from PYPOST-823 / PYPOST-827 is
  preserved (waits still end by success or deadline under timer stall).
- No intentional change to product environment or collection storage behavior,
  encryption, or user-visible persistence (test-harness diagnostics only unless
  a real product defect is uncovered while improving reports).

## Task Description

**Problem:** After PYPOST-827, storage async checks share a hang-resistant wait
that fails with a generic timeout message when the condition is still false at
the deadline. Maintainers cannot tell from that message alone whether the
system was still busy, had pending work, or (when applicable) what the worker
looked like. Source: [PYPOST-828](https://pypost.atlassian.net/browse/PYPOST-828),
follow-up from [PYPOST-823](https://pypost.atlassian.net/browse/PYPOST-823) /
[PYPOST-827](https://pypost.atlassian.net/browse/PYPOST-827).

**Business need:** Faster, lower-friction triage of wait timeouts. A failed
quality-gate run should answer “what was still going on?” without requiring
extra instrumentation. Richer diagnostics reduce mean time to understand
flakes and genuine regressions in this wait family.

### In Scope

- Enriching timeout failure reports from the shared hang-resistant wait used by
  storage async checks with actionable busy/pending context.
- Including optional worker-state context in those reports when the waited
  scenario involves a worker.
- Keeping hang-resistant wait outcomes and deadlines behaviorally equivalent to
  today’s PYPOST-823 / PYPOST-827 wait contract.
- Leaving product storage/gateway/worker runtime behavior unchanged unless a
  genuine defect is found that must be fixed for honest verification.

### Out of Scope

- Re-doing the sibling gateway/worker wait port (completed under PYPOST-827).
- Changing hang-resistant wait timing, polling strategy, or hang-defense
  semantics beyond what is needed to report richer timeout context.
- Re-working encryption policy, on-disk formats, or user-facing storage UI.
- Broader suite redesign, marker policy changes, or unrelated flaky tests.
- Aligning modules onto a shared Qt application fixture (PYPOST-830).
- Production worker lifecycle hygiene (PYPOST-829).
- Fixing unrelated tabs-presenter failures tracked elsewhere.

## Functional Requirements

- On timeout of the shared hang-resistant wait used by storage async checks,
  the failure report must include diagnostic context that helps triage why the
  condition was still unmet (at least timeout duration and the timeout reason).
- For waits that observe storage async load state, the timeout report MUST
  include busy/pending status for that load state.
- Busy/pending may be omitted only when those flags are not part of that
  wait’s business context; the report must still be actionable (timeout
  duration + reason).
- When the waited scenario involves a worker, the timeout report must be able
  to include worker-state context (or state clearly that none applies).
  Worker state remains optional.
- Successful waits must continue to succeed without requiring new user-facing
  steps; diagnostics apply to timeout failures.
- Hang-resistant wait behavior must remain: the wait ends by success or by
  deadline, including when event-loop timers stall.
- Checks that already use the shared wait must keep asserting the same business
  outcomes; only the timeout failure report becomes more informative.

## Non-functional Requirements

- **Actionability:** Timeout text must be useful for triage without a second
  debug run for the common busy/pending / worker cases.
- **Clarity:** Reports must remain readable in CI logs (concise, structured
  enough to scan).
- **Reliability:** Enriching diagnostics must not reintroduce hangs or extend
  waits beyond the configured deadline.
- **Consistency:** All consumers of the shared hang-resistant wait benefit from
  the richer timeout reporting (no module left with only the generic message
  while others are enriched).
- **Scope discipline:** Prefer test-harness-only change; no product behavior
  change unless required for correct verification.

## Constraints and Assumptions

- Programming language: Python 3.10+.
- Prior work: PYPOST-823 introduced hang-resistant waits; PYPOST-827 shared that
  wait across sibling storage async checks and deferred richer timeout
  diagnostics to this task.
- The shared hang-resistant wait used by storage async checks is the single
  wait whose timeout reports are in scope.
- “Busy/pending” (required for waits that observe storage async load state)
  and “optional worker state” are business-level diagnostic signals about
  in-flight async work; how they are captured or formatted is
  architecture/implementation.
- Call sites may not always have a worker; worker context is optional and must
  not be required for every wait.
- Approval for Step 1 artifacts is treated as granted under sprint-task-runner
  autonomy.

## Main Entities and Interactions

| Entity | Attributes (business) | Role |
| --- | --- | --- |
| Maintainer / contributor | Role, need for fast triage | Reads failed quality-gate output |
| Default quality gate | Pass/fail outcome, CI logs | Automated suite that reports wait timeouts |
| Shared hang-resistant wait | Deadline, completion condition, timeout failure report | Time-bounded wait whose timeout text is enriched |
| Timeout diagnostic context | Timeout duration, reason, busy/pending when part of wait context, optional worker state | Actionable information attached to a wait failure |
| Storage async checks | Modules using the shared wait, asserted outcomes | Consumers that surface timeout failures |
| Worker (when present) | State at timeout (business view) | Optional source of diagnostic context |
| Busy / pending status | Whether storage async load work was still in flight | Required triage signal for waits that observe storage async load state; omit only when not part of that wait’s business context |

Interaction overview:

1. Maintainer runs the default quality gate (or a focused storage async check).
2. A check waits for async completion via the shared hang-resistant wait.
3. If the condition is unmet at the deadline, the wait fails with a report that
   includes timeout duration and reason; for storage async load waits, also
   busy/pending; plus optional worker state when applicable.
4. The maintainer uses that report to triage without adding temporary logging.
5. Successful waits and hang-resistant timing behave as today.

## Q&A

- Q: Why is a richer timeout message a business requirement?
  A: Opaque timeouts force maintainers to re-run and instrument just to learn
  whether work was still busy/pending. Actionable failure text shortens triage
  and keeps the quality gate trustworthy.
- Q: Why ask “why” when Jira already names busy/pending and worker state?
  A: Those signals are the *content* of the diagnostic need. The business goal
  is faster triage of wait failures; listing the signals defines what “enough
  context” means without prescribing how they are collected.
- Q: How does this relate to PYPOST-827?
  A: PYPOST-827 delivered the shared hang-resistant wait and explicitly deferred
  richer timeout diagnostics. This task closes that deferred item only.
- Q: Must every wait include worker state?
  A: No. Worker context is optional and applies when the waited scenario has a
  worker.
- Q: Must every timeout report include busy/pending?
  A: For waits that observe storage async load state, yes—busy/pending is
  required. It may be omitted only when busy/pending is not part of that
  wait’s business context; the report must still be actionable (timeout
  duration + reason).
- Q: Does this change when waits pass or fail?
  A: No. Pass/fail and deadlines stay the same; only the timeout failure report
  becomes more informative.
- Q: Is re-porting sibling modules part of this task?
  A: No; that is complete under PYPOST-827 and out of scope here.
- Q: Why omit how diagnostics are attached to the wait API?
  A: Step 1 states outcomes only (what the failure report must convey). Capture
  and formatting belong in architecture/implementation.
