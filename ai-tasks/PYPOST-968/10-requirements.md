# PYPOST-968: Decide direct log coverage for forced dialog-settle timeout

## Goals

Determine whether the forced dialog-settle timeout scenario needs a direct automated
check for its existing DEBUG `ui_wait_timeout` event, and close the low-priority
observability question raised by PYPOST-934.

The business value is earlier detection when timeout logging silently regresses in CI,
so maintainers retain useful evidence when diagnosing an intermittent dialog-settle
failure. Because the timeout exception already carries the primary failure diagnostics
and the comparable golden Send companion does not check this DEBUG event, the additional
coverage must provide distinct, proportionate value rather than duplicate existing
confidence.

Source: [PYPOST-934](https://pypost.atlassian.net/browse/PYPOST-934) TD-3.

## Programming Language

Python, consistent with the existing PyPost application and automated test suite.

## User Stories

- As a **maintainer**, I want confidence that a forced dialog-settle timeout remains
  visible in diagnostic logs, so a logging regression does not become a CI blind spot.
- As a **CI investigator**, I want timeout evidence to identify the forced dialog-settle
  condition, so I can distinguish the expected companion path from unrelated waits.
- As a **test-suite owner**, I want optional diagnostic checks to justify their ongoing
  maintenance cost, so low-value duplication does not make the suite more brittle.

## Definition of Done

- The value of directly checking the existing DEBUG `ui_wait_timeout` event in the forced
  dialog-settle scenario is assessed against current diagnostic coverage and the sibling
  golden Send precedent.
- One of these acceptance outcomes is recorded:
  - an automated check proves that the forced path emits `ui_wait_timeout` and identifies
    the forced dialog-settle condition; or
  - a documented deferral explains why the check still lacks distinct value and states
    what future evidence would justify revisiting it.
- If the automated check is adopted, it remains bounded, deterministic, and suitable for
  the existing CI selection.
- Existing dialog-settle behavior, timeout exception diagnostics, and sibling golden Send
  coverage retain their acceptance meaning.
- No user-visible application behavior changes as part of this debt item.

## Task Description

PYPOST-934 added a forced-timeout companion that verifies the primary dialog-settle
failure diagnostics. Its review intentionally left direct verification of the DEBUG
`ui_wait_timeout` event as optional low-priority debt because the exception is the primary
regression signal and the golden Send companion follows the same posture.

PYPOST-968 resolves that open decision. The task covers the observability contract for the
existing forced dialog-settle timeout only. It does not broaden dialog behavior, alter the
wait contract, or require parity work on unrelated timeout companions.

### Functional Requirements

- FR1: The forced dialog-settle timeout continues to expose its existing primary exception
  diagnostics regardless of the decision on direct log coverage.
- FR2: If direct log coverage is adopted, the automated proof confirms the timeout event is
  observable at DEBUG level during the forced scenario.
- FR3: If direct log coverage is adopted, the observed event identifies the forced
  dialog-settle condition without relying on incidental timing.
- FR4: If direct log coverage is deferred, the decision records both the current reason and
  a concrete revisit trigger, such as repeated CI failures where exception diagnostics do
  not reveal whether the expected timeout event was emitted.
- FR5: The selected outcome does not weaken or replace the existing forced-timeout
  exception assertions.

### Non-Functional Requirements

- **Reliability:** Any adopted proof must be deterministic and must not introduce timing
  sensitivity into the dialog-settle scenario.
- **Boundedness:** Automated execution must remain protected from hangs and complete within
  the established test budget.
- **Maintainability:** The outcome should add a distinct regression signal or explicitly
  avoid redundant coverage.
- **Compatibility:** Existing offscreen CI execution and user-visible behavior remain
  unchanged.
- **Security and privacy:** Diagnostic verification must not require or expose user data.

### Scope Boundaries

In scope:

- The existing forced dialog-settle timeout scenario introduced by PYPOST-934.
- The existing DEBUG timeout event for that scenario.
- An evidence-based adoption or deferral decision.

Out of scope:

- Changes to product dialog behavior or timeout semantics.
- New logging events, metrics, or broad observability redesign.
- Retrofitting direct log checks across every wait or timeout companion.
- Changes to the golden Send companion.
- Broader Settings functionality or dialog-matrix coverage.

### Main Entities and Interactions

- **Forced dialog-settle scenario:** Reproduces a known timeout deterministically and
  produces the primary failure diagnostics and existing DEBUG timeout event.
- **Timeout event:** Provides supplemental evidence and identifies the timed-out condition
  for maintainers and CI investigators.
- **Exception diagnostics:** Remain the primary regression signal whether direct log
  coverage is adopted or deferred.
- **CI maintainer:** Uses exception and log context to diagnose a failing settle step.
- **Deferral decision:** Records why supplemental proof is not yet worth its maintenance
  cost and when that conclusion should be revisited.

## Q&A

- **Q: Why is this task needed when PYPOST-934 already checks the forced timeout?**
  **A:** PYPOST-934 checks the primary exception diagnostics but not the supplemental DEBUG
  timeout event. This task decides whether that omission is a meaningful CI blind spot.

- **Q: Is adding a direct log assertion mandatory?**
  **A:** No. Jira explicitly accepts a documented deferral if current evidence still shows
  that the check would duplicate existing confidence without proportionate value.

- **Q: What would justify deferral?**
  **A:** The exception remains the primary diagnostic contract, no recurring CI blind spot
  has been established, and the comparable golden Send companion also omits direct DEBUG
  verification.

- **Q: What would justify adding the proof?**
  **A:** Evidence that maintainers need an independent regression signal for timeout-event
  emission, especially repeated CI failures where the exception alone cannot establish
  whether the event was recorded.

- **Q: Does this task change application behavior?**
  **A:** No. It is limited to test confidence or a documented observability decision.
