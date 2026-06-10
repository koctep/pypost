# PYPOST-490: Add integration test for settings-to-masked hidden-toggle logging flow

## Goals

PYPOST-448 introduced a user-configurable logging policy for hidden-flag toggle events: by
default, variable key names must not appear in diagnostic logs in readable form; users may opt
in to full key-name visibility for troubleshooting.

That behavior is verified today through separate, narrower automated checks. No single
acceptance check follows the full user journey from changing the logging preference in
Settings through toggling a hidden flag and inspecting the resulting log output. A wiring
break between settings, application state, and observability output could therefore regress
without detection.

This task closes that quality gap. The primary deliverable is **regression protection** for
the end-to-end observability contract established by PYPOST-448. Product behavior should
remain as today unless an existing wiring defect is discovered and fixed.

## Programming Language

Python 3.10+

## User Stories

- As a **security-conscious user**, I want assurance that the default logging policy (key names
  not readable in toggle logs) still holds when I change settings and use the environment
  manager, so my organization's logging expectations are met in real usage—not only in
  isolated checks.
- As a **developer or support engineer**, I want assurance that enabling full key-name
  visibility in Settings actually produces readable key names in toggle logs after the
  preference is saved and applied, so diagnostics remain trustworthy when I opt in.
- As a **maintainer**, I want one automated acceptance check that covers the full
  settings-to-toggle-log flow identified in PYPOST-448 technical debt, so future refactors to
  settings application or environment-manager wiring cannot silently break observability
  behavior.
- As a **quality reviewer**, I want toggle logs to continue excluding variable values and to
  retain environment name and hidden-state context in both logging modes, so expanded coverage
  does not weaken existing privacy constraints.

## Definition of Done

1. An automated acceptance check verifies the **full user journey**: user saves a logging
   preference in Settings, the application applies that preference, the user opens the
   environment manager, toggles a hidden flag, and the resulting diagnostic log reflects the
   active policy.
2. With the **default logging policy** (key names suppressed), the acceptance check confirms
   the variable key name does **not** appear in the toggle log in readable form.
3. With **full key-name visibility enabled** in Settings, the acceptance check confirms the
   variable key name **does** appear in readable form in the toggle log.
4. In both modes, the acceptance check confirms the log still includes **environment name**
   and **hidden state**, and still **does not** include variable values.
5. The acceptance check is **traceable** to the missing-coverage item in
   [PYPOST-448 technical-debt analysis](ai-tasks/PYPOST-448/60-tech-debt.md) and to Jira
   [PYPOST-490](https://pypost.atlassian.net/browse/PYPOST-490).
6. **No product behavior change** unless a wiring defect is found; the deliverable is test
   coverage, not new user-facing functionality.

## Task Description

### Problem Statement

After PYPOST-448, hidden-flag toggle observability depends on a user setting that flows from
Settings through application state into the environment manager. Unit-level checks cover
individual pieces (settings UI, settings application, dialog logging) but not the connected
flow. That split increases the risk of undetected regressions in security-relevant logging
behavior.

### In Scope

- Acceptance coverage for the **end-to-end flow** from saving the logging preference through
  hidden-flag toggle log output.
- Verification of **both logging modes**: default suppression and opt-in full key-name
  visibility.
- Verification that **privacy constraints** from PYPOST-437 and PYPOST-448 still hold
  (no variable values in logs; environment and hidden state remain observable).

### Out of Scope

- New product features or changes to hidden-flag UI, persistence, or preview masking.
- Replacing or duplicating existing unit-level checks (this task **adds** integration
  coverage).
- Environment persistence round-trip logging behavior ([PYPOST-489](https://pypost.atlassian.net/browse/PYPOST-489)).
- Refactors such as shared mask constants or settings-dialog layout
  ([PYPOST-491](https://pypost.atlassian.net/browse/PYPOST-491),
  [PYPOST-492](https://pypost.atlassian.net/browse/PYPOST-492)).
- Live hot-reload of logging policy while the environment manager is already open (accepted
  PYPOST-448 limitation: policy applies to subsequently opened dialogs only).
- Observability changes (new logs, metrics, or user-facing documentation).

## Functional Requirements

- The project must include an automated acceptance check that exercises the connected flow
  from Settings save through hidden-flag toggle logging.
- The check must assert default-policy behavior: key names not readable in toggle logs.
- The check must assert opt-in full-visibility behavior: key names readable in toggle logs.
- The check must assert that environment name and hidden state remain present in toggle logs
  in both modes.
- The check must assert that variable values are not written to toggle logs in either mode.

## Non-Functional Requirements

- **Security / compliance:** acceptance coverage must guard the default suppressed-key-name
  policy so org-sensitive deployments do not regress to readable key names without an explicit
  user choice.
- **Observability:** coverage must confirm that opt-in full visibility remains effective
  end-to-end for teams that rely on key-name diagnostics.
- **Maintainability:** the acceptance check must be focused, traceable to PYPOST-448 debt,
  and resistant to brittle duplication of existing unit scenarios.
- **Stability:** adding the check must not alter hidden-flag behavior, variable persistence,
  or UI display unless a discovered wiring defect requires a minimal fix.

## Constraints and Assumptions

- PyPost is a desktop Python application; PYPOST-448 behavior and defaults are already
  shipped.
- Variable values must not be logged; this constraint is inherited and must remain verified.
- Step 1 defines **what** must be verified, not **how** the acceptance check is implemented.
- The logging policy applies to toggle events after the user saves Settings and opens the
  environment manager anew (consistent with PYPOST-448 accepted UX).
- Existing unit tests remain the baseline for component-level behavior; this task adds the
  missing connected-flow check only.
- Project markdown and 100-character line-length rules apply to all generated artifacts.

## Main Entities and Interactions (Business View)

- **User** — configures logging policy in Settings and toggles hidden flags in the environment
  manager.
- **Application settings** — persisted preference controlling key-name visibility in toggle
  logs.
- **Environment manager** — UI where the user marks variables as hidden or visible.
- **Hidden-flag toggle event** — user action that triggers a diagnostic log entry.
- **Diagnostic log entry** — observability output describing environment, hidden state, and
  optionally the variable key name per policy.
- **Maintainer / CI** — runs automated acceptance checks to detect regressions.

Interaction flow under test:

1. User sets logging policy in Settings and saves.
2. Application applies the saved preference.
3. User opens the environment manager and toggles a hidden flag on a variable.
4. Application writes a diagnostic log entry governed by the active policy.
5. Automated acceptance verifies log content matches the selected policy and privacy rules.

## Q&A

| Question | Answer |
|----------|--------|
| Is this a feature or test task? | **Test-coverage debt task**; behavior should remain as today unless a wiring defect is found. |
| Why is end-to-end coverage needed if unit tests exist? | Unit tests validate pieces in isolation; a break in how settings reach the environment manager would not be caught by any single existing check. |
| What is the boundary with PYPOST-489? | PYPOST-490 owns the **settings → apply → environment manager → toggle log** flow. PYPOST-489 owns persistence round-trip scenarios with default masked logging; separate ticket. |
| Must the test cover policy change while the dialog is open? | No. PYPOST-448 accepts that policy updates apply only when the environment manager is opened after saving Settings. |
| What logging modes must be covered? | Default suppression (key name not readable) and opt-in full key-name visibility (key name readable). |
| Should variable values ever appear in logs? | No. Inherited from PYPOST-437 / PYPOST-448. |
| Source of this task? | Follow-up from [PYPOST-448 technical-debt analysis](ai-tasks/PYPOST-448/60-tech-debt.md); Jira [PYPOST-490](https://pypost.atlassian.net/browse/PYPOST-490). |
