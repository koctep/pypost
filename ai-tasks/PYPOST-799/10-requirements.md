# PYPOST-799: Close optional-metrics guard debt (PYPOST-44 TD-2)

## Goals

PyPost supports optional observability: metrics may be omitted at application startup without
affecting core product behavior. When metrics is not configured, tracking calls were historically
skipped; when configured, events are recorded as today.

Optional injection created a recurring burden: every place that records a tracking event had to
decide whether metrics was present before calling it. That branching duplicated the same concern
across request handling, background workers, MCP integration, storage, and UI flows, making domain
logic harder to read and maintain.

The business need is straightforward: **observability must remain optional at the composition
root, but consumers must never need to branch on “was metrics injected?” before recording an
event.** When metrics is omitted, recording must fail silently with no user-visible change. When
metrics is present, behavior must match today.

Estimation and prior work under [PYPOST-73](https://pypost.atlassian.net/browse/PYPOST-73) and
[PYPOST-74](https://pypost.atlassian.net/browse/PYPOST-74) suggest the functional outcome may
already be satisfied. This ticket closes the debt item tracked in
[PYPOST-75](https://pypost.atlassian.net/browse/PYPOST-75) follow-ups (PYPOST-44 TD-2) by
**confirming the business outcome is met or completing any verified gap**.

## User Stories

- As a **developer**, I want to record tracking events without optional-injection checks at each
  call site, so business logic stays readable.
- As a **test author**, I want a stable no-op path when metrics is omitted, so tests do not need
  global patching or guard assertions.
- As a **maintainer**, I want one normalization point for optional metrics injection, so the
  pattern is consistent across services, workers, MCP, and UI.
- As a **product owner**, I want zero change in end-user behavior when metrics is not configured —
  tracking absence must not break sends, saves, MCP, or history.

## Functional Requirements

1. **Optional at startup** — Metrics injection remains optional at the composition root; omitting
   it must not prevent the application from starting or serving users.
2. **Direct recording** — Components that record tracking events do so directly, without
   conditional checks whose sole purpose is “is metrics present?”.
3. **Silent omission** — When metrics is not injected, recording attempts have no effect and do
   not surface errors to users or alter product workflows (sends, saves, MCP, history, UI).
4. **Preserved behavior when configured** — When metrics is injected, recorded events and
   counters behave the same as before this debt closure (no regression in observability output).
5. **Single normalization** — Optional injection is resolved once (at construction or an agreed
   upstream boundary) so downstream consumers always hold a usable tracker.
6. **Consistent coverage** — All direct tracking consumers follow the same optional-metrics
   pattern; no stray one-off guard styles remain in production paths.
7. **Closure evidence** — The PYPOST-44 TD-2 follow-up can be marked resolved with documented
   verification that the above outcomes hold, or with a minimal fix for any verified gap.

## Non-Functional Requirements

- **Zero user-visible regression** — End users must not notice any change in application behavior
  whether metrics is configured or not.
- **Maintainability** — Domain code should read as business logic; optional-injection plumbing
  should not be repeated at every tracking call site.
- **Testability** — Tests can exercise code paths with and without metrics injection without
  brittle global mocks for “metrics absent”.
- **Auditability** — Closure of PYPOST-44 TD-2 is traceable in debt artifacts and linked Jira
  tickets.

## Constraints and Assumptions

- **Implementation language:** Python (existing PyPost package and test suite).
- **Verification-first scope** — Prior tickets may have already delivered the required outcome;
  this task validates that outcome before treating the debt as closed.
- **Business-condition guards remain valid** — Recording only when a domain condition applies
  (e.g. only when a counter is positive) is not in scope for removal; only guards whose purpose
  is optional metrics injection are addressed.
- **macOS/desktop and server paths** — Acceptance applies wherever PyPost records tracking events
  (request handling, workers, MCP, storage, UI).
- **Debt lineage** — Source: [PYPOST-75](https://pypost.atlassian.net/browse/PYPOST-75) follow-up
  for PYPOST-44 TD-2; parent context is optional-metrics guard proliferation.

## Main Entities (Business Perspective)

| Entity | Role |
| --- | --- |
| Tracking event | A measurable occurrence the product may record (counter increment, gauge set, etc.) for observability. |
| Tracker | The capability a component uses to record tracking events; always available to the consumer after normalization. |
| Tracking consumer | A service, worker, MCP handler, storage layer, or UI component that records events during normal operation. |
| Composition root | The startup or wiring boundary where metrics may be supplied or omitted without affecting core product features. |
| No-op tracker | A stand-in that accepts recording calls but produces no observability output when metrics is not configured. |
| Optional metrics configuration | The operator or deployment choice to enable or omit metrics collection at startup. |

## Definition of Done

- Developers can record tracking events at consumer call sites without optional-injection guards
  whose only purpose is handling omitted metrics.
- When metrics is not configured, users experience the same product behavior as before this
  closure (sends, saves, MCP, history, UI) — tracking absence does not cause failures or visible
  changes.
- When metrics is configured, observability output matches pre-closure expectations (no
  regression in what is recorded or exposed).
- Optional metrics injection is normalized at a single boundary so all direct tracking consumers
  follow one consistent pattern.
- Automated regression verification confirms the above outcomes; any gap found is remediated
  within this ticket’s scope or explicitly deferred with its own follow-up ticket.
- PYPOST-44 TD-2 is documented as resolved in debt artifacts when verification passes.
- Out-of-scope polish (naming alignment, type-hint narrowing, adapter work, facade splits) is
  listed and linked to separate tickets rather than blocking closure.

## Task Description

**Problem:** Optional metrics injection forced defensive checks at many call sites, duplicating
the same optional-injection concern and obscuring domain logic.

**Expected outcome:** Consumers always hold a usable tracker; omitted injection resolves to a
shared no-op; tracking calls are direct; user-visible behavior is unchanged.

**In scope**

- Confirm PYPOST-44 TD-2 acceptance outcomes (functional requirements above).
- Remediate any verified gap that prevents those outcomes.
- Update debt artifacts and close this ticket when satisfied.

**Out of scope**

- Splitting metrics registry and server responsibilities ([PYPOST-75](https://pypost.atlassian.net/browse/PYPOST-75) core scope — done).
- Constructor type-hint narrowing for optional metrics ([PYPOST-675](https://pypost.atlassian.net/browse/PYPOST-675)).
- OpenTelemetry adapter work ([PYPOST-579](https://pypost.atlassian.net/browse/PYPOST-579)).
- Renaming the tracking contract for naming consistency alone, unless verification shows the
  current name blocks closure.

## Programming Language

Python (existing PyPost application and test suite).

## Q&A

| Question | Answer |
| --- | --- |
| Why was this ticket filed if prior work may already satisfy the outcome? | PYPOST-75’s debt review predated closure alignment; PYPOST-799 tracks the explicit TD-2 follow-up line for auditability. |
| Is renaming the tracking contract required? | No — the business need is a stable recording contract and no-op default when metrics is omitted; naming polish is out of scope unless it blocks closure. |
| Does omitted metrics change user-visible behavior? | No — tracking was already skipped; the no-op path must preserve silent omission. |
| What if verification finds a remaining optional-injection guard? | Remediate it as part of closure so consumers record directly through the normalized tracker. |
| What if verification finds only typing or naming gaps? | Document and link to the appropriate follow-up ticket; do not block TD-2 closure. |
