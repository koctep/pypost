# PYPOST-462: Add integration test for hidden-value masking across save/reload history flow

## Goals

PYPOST-446 established that values derived from hidden environment variables must not appear in
readable form in request history. That policy is verified today through separate, narrower
automated checks that exercise individual components in isolation.

No single acceptance check follows the full user journey from executing a request with hidden
variables through persisting history, reloading the application state, and viewing the result in
the History panel. A wiring break between execution, history persistence, and history display
could therefore regress without detection, re-exposing secrets users marked as hidden.

This task closes that quality gap. The primary deliverable is **regression protection** for the
end-to-end history-masking contract established by PYPOST-446. Product behavior should remain
as today unless an existing wiring defect is discovered and fixed.

## Programming Language

Python 3.10+

## User Stories

- As a **security-conscious user**, I want assurance that hidden variable values stay masked in
  History after I run a request, close and reopen the app, or otherwise reload persisted history,
  so my secrets are not accidentally exposed during normal workflows or screen sharing.
- As a **user troubleshooting requests**, I want History to remain useful after reload—showing
  request structure and non-sensitive values—without revealing hidden-derived secrets.
- As a **maintainer**, I want one automated acceptance check that covers the full
  execution-to-history-display flow identified in PYPOST-446 technical debt, so future refactors
  cannot silently break history masking across persistence boundaries.
- As a **quality reviewer**, I want the acceptance check to confirm that non-hidden variable
  values remain visible in History, so expanded coverage does not weaken useful debugging
  information.

## Definition of Done

1. An automated acceptance check verifies the **full user journey**: user executes a request
   that uses hidden and non-hidden environment variables, history is recorded and persisted,
   persisted history is reloaded, and the History panel presents the stored entry.
2. After reload, the acceptance check confirms that values derived from **hidden variables do
   not appear in readable form** anywhere in the displayed history entry (request URL,
   headers, and body surfaces covered by PYPOST-446).
3. After reload, the acceptance check confirms that values from **non-hidden variables remain
   visible** in the displayed history entry according to existing product behavior.
4. The acceptance check exercises the **connected flow** from execution through persistence to
   History display so wiring breaks between those stages are detectable.
5. The acceptance check is **traceable** to the missing-coverage item in
   [PYPOST-446 technical-debt analysis](ai-tasks/PYPOST-446/60-tech-debt.md) and to Jira
   [PYPOST-462](https://pypost.atlassian.net/browse/PYPOST-462).
6. **No product behavior change** unless a wiring defect is found; the deliverable is test
   coverage, not new user-facing functionality.

## Task Description

### Problem Statement

After PYPOST-446, request history must mask values derived from hidden environment variables
before they are stored and shown to users. Unit-level checks cover the masking rules and
history recording in isolation, but not the connected flow through persistence and UI display.
That split increases the risk of undetected regressions in security-relevant history behavior,
especially across application restarts or history reload.

### In Scope

- Acceptance coverage for the **end-to-end flow** from request execution through history
  persistence, reload, and History panel display.
- Verification that **hidden-derived values remain masked** after the persistence-reload
  cycle.
- Verification that **non-hidden values remain visible** in the same history entry.
- Coverage aligned with the history surfaces addressed by PYPOST-446 (request URL, headers,
  and body in history records).

### Out of Scope

- New product features or changes to hidden-variable UI, masking rules, or preview behavior.
- Replacing or duplicating existing unit-level masking checks (this task **adds** integration
  coverage).
- Explicit masking-metric behavior with empty vs non-empty hidden keys
  ([PYPOST-464](https://pypost.atlassian.net/browse/PYPOST-464)).
- Refactoring history-recording logic for maintainability
  ([PYPOST-463](https://pypost.atlassian.net/browse/PYPOST-463)).
- Provisioning CI/local test environments or full-project regression runs
  ([PYPOST-465](https://pypost.atlassian.net/browse/PYPOST-465)).
- Settings-to-toggle-log integration coverage
  ([PYPOST-490](https://pypost.atlassian.net/browse/PYPOST-490)).
- Environment encryption at rest behavior ([PYPOST-447](https://pypost.atlassian.net/browse/PYPOST-447)).
- Observability changes (new logs, metrics, or user-facing documentation).

## Functional Requirements

- The project must include an automated acceptance check that exercises the connected flow
  from request execution through history persistence, reload, and History panel display.
- The check must assert that hidden-derived values are **not readable** in the displayed
  history entry after reload.
- The check must assert that non-hidden variable values **remain visible** in the displayed
  history entry after reload.
- The check must exercise the connected flow end-to-end so breaks between stages are
  detectable.
- The check must align with the history-masking policy delivered by PYPOST-446.

## Non-Functional Requirements

- **Security / compliance:** acceptance coverage must guard against secret exposure in
  persisted and reloaded history, protecting users who rely on hidden variables during
  screen sharing and collaborative debugging.
- **Usability:** coverage must confirm that history remains useful for troubleshooting by
  preserving visibility of non-hidden values.
- **Maintainability:** the acceptance check must be focused, traceable to PYPOST-446 debt,
  and resistant to brittle duplication of existing unit scenarios.
- **Stability:** adding the check must not alter history masking behavior, hidden-variable
  handling, or UI display unless a discovered wiring defect requires a minimal fix.

## Constraints and Assumptions

- PyPost is a desktop Python application; PYPOST-446 history-masking behavior is already
  shipped.
- Hidden variables are a display-and-history policy concern; request execution still uses real
  values at runtime (inherited from PYPOST-437).
- Step 1 defines **what** must be verified, not **how** the acceptance check is implemented.
- Existing unit tests remain the baseline for component-level behavior; this task adds the
  missing connected-flow check only.
- Project markdown and 100-character line-length rules apply to all generated artifacts.

## Main Entities and Interactions (Business View)

- **User** — executes requests that reference environment variables, some marked hidden.
- **Hidden variable** — environment value the user marked as sensitive.
- **Non-hidden variable** — environment value shown and stored without masking.
- **Request execution** — resolves variables and produces a history-worthy snapshot of the
  outbound request.
- **History record** — persisted record of a past request, including URL, headers, and body.
- **History panel** — UI surface where users review past requests.
- **Maintainer / CI** — runs automated acceptance checks to detect regressions.

Interaction flow under test:

1. User configures an environment with hidden and non-hidden variables.
2. User executes a request that references those variables.
3. Application records a history entry and persists it.
4. Application reloads persisted history (simulating restart or fresh load).
5. User views the entry in the History panel.
6. Automated acceptance verifies hidden-derived values are masked and non-hidden values remain
   visible.

## Q&A

- **Is this a feature or test task?**
  Test-coverage debt task; behavior should remain as today unless a wiring defect is found.
- **Why is end-to-end coverage needed if unit tests exist?**
  Unit tests validate pieces in isolation; wiring breaks between execution, persistence, and
  the History panel would not be caught by any single existing check.
- **What history surfaces must be covered?**
  Request URL, headers, and body in history records—the surfaces addressed by PYPOST-446.
- **Must non-hidden values stay visible?**
  Yes. Masking applies only to hidden-derived values; debugging usefulness must be preserved.
- **What is the boundary with PYPOST-464?**
  PYPOST-462 owns execution → history save → reload → History panel. PYPOST-464 owns metric
  behavior for empty vs non-empty hidden keys.
- **What is the boundary with PYPOST-490?**
  PYPOST-490 owns settings-to-toggle-log coverage. PYPOST-462 owns history-masking coverage.
- **Should response bodies be in scope?**
  Only if covered by PYPOST-446 policy; this task follows that parent scope.
- **Source of this task?**
  Follow-up from [PYPOST-446 technical-debt analysis](ai-tasks/PYPOST-446/60-tech-debt.md);
  Jira [PYPOST-462](https://pypost.atlassian.net/browse/PYPOST-462).
