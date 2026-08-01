# PYPOST-916: Extend agent select beyond combo boxes

## Goals

Agent and automated harness flows must select items in list and tree
controls the same way they already select combo options — by what the
operator sees (display text) or by a stable position (index) — so
golden-flow and seed drive proofs are not blocked when the target is not
a drop-down.

This debt comes from [PYPOST-851](https://pypost.atlassian.net/browse/PYPOST-851)
/ [PYPOST-836](https://pypost.atlassian.net/browse/PYPOST-836) follow-up:
combo-only select left tree/list selection to ad-hoc helpers.

## Programming Language

Python (PySide6), with English Markdown developer docs.

## User Stories

- As an **agent / e2e author**, I want to select a list or tree row by
  display text so drive scripts match what appears on screen.
- As an **agent / e2e author**, I want to select a list or tree row by
  index when text is unstable or redundant.
- As a **maintainer**, I want a documented select API that covers combo,
  list, and tree so callers do not invent one-off click helpers for
  selection.
- As a **CI owner**, I want at least one automated non-combo select path
  so the capability does not regress.

## Definition of Done

- Documented API for selecting list/tree items by display text or index.
- Automated tests cover at least one non-combo (list or tree) path.
- Existing combo select by display text remains usable for current
  golden / seed call sites.
- Unticketed follow-ups (if any) live only in this task’s
  `60-tech-debt.md` (no Jira ticket creation in this run).

## Task Description

**Problem:** Agent `ui_select` only works on combo boxes. Collection
trees, history lists, and environment lists need selection for
golden-flow and seed drive proofs; authors today use separate helpers
or raw widget APIs.

**Business need:** One agent-facing select capability for the common
named controls so harnesses stay consistent and documented.

### In Scope

- Extend the agent select capability beyond combo boxes to list and/or
  tree selection by display text or index.
- Document the API for callers.
- Add automated coverage for at least one non-combo path.
- Keep existing combo-by-text call sites working.

### Out of Scope

- Changing production UI widgets or identity catalog.
- Replacing every ad-hoc tree *click* helper used to open a request
  (selection vs open/activate may remain distinct when product needs a
  click).
- Out-of-process MCP packaging of UI actions.
- Creating Jira Debt tickets (orchestrator Phase D).
- Commit or Jira status transitions (orchestrator).

## Functional Requirements

- FR1: Callers can select a list item by display text.
- FR2: Callers can select a list or tree item by index.
- FR3: Callers can select a tree item by display text.
- FR4: Combo select by display text continues to work.
- FR5: Missing target, wrong type, or missing option/index raises the
  same class of actionable agent UI errors as today.
- FR6: Developer docs describe the extended select API.
- FR7: Tests prove at least one non-combo path.

## Non-Functional Requirements

- NFR1: Suit fixture-style tests (offscreen Qt); no live network.
- NFR2: Explicit pytest timeouts per `.cursor/lsr/do-testing.md`.
- NFR3: Logs must not dump item payloads beyond existing action scalars
  (`widget_id`, outcome, duration).
- NFR4: English docs; line length ≤ 100 where practical.

## Constraints and Assumptions

- Parent debt: PYPOST-836 / PYPOST-851 “broader select targets”.
- Widgets are already named via stable `objectName` / widget ids.
- Selection sets current/selected row; it does not replace product
  double-click or open-request behavior unless that already follows
  from selection signals.
- Sprint-task-runner batch: no user approval gates; no commit / Jira
  writes in this subagent run.

## Main Entities (business)

| Entity | Role |
| --- | --- |
| Agent / harness | Drives named UI after ready |
| Select action | Chooses one option on a named control |
| Combo control | Existing drop-down select target |
| List control | Flat item list (history, env names, …) |
| Tree control | Hierarchical collection / folder rows |
| Display text | Visible label used to find the item |
| Index | Zero-based position used to find the item |

## Q&A

| Q | A |
| --- | --- |
| Why not keep ad-hoc tree click helpers only? | Selection is a first-class agent action; docs + one API reduce drift. |
| Why text *and* index? | Acceptance requires both; text matches UI, index helps when labels collide. |
| Must every tree click migrate? | No — open-via-click helpers may remain for activate/open flows. |
| Jira / commit in this run? | No — parent orchestrator owns Phase D/F. |
