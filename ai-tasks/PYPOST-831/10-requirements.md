# PYPOST-831: After bulk-closing request tabs, stay on a request workspace

## Goals

Users who remove several open request tabs at once (for example when deleting
requests that still have tabs open) must end on a remaining request workspace,
never on the trailing `+` (new tab) control. Single-tab close already obeys that
product rule ([PYPOST-824](https://pypost.atlassian.net/browse/PYPOST-824)); the
bulk-close path can still leave the active tab on `+` when the rightmost open
request tab(s) are removed. This debt follow-up closes that gap so every close
path leaves the user in a real request workspace.

## Programming Language

Python 3.10+

## User Stories

- As a **desktop user**, when several of my open request tabs are closed together
  (including the rightmost ones next to `+`), I want a remaining request tab to
  become active so I can keep editing or sending without first clicking away
  from `+`.
- As a **desktop user**, I want bulk close to follow the same focus rule as
  closing one tab at a time: if any request tab remains, the active tab must be
  a request tab, not `+`.
- As a **maintainer**, I want this bulk-close focus rule protected by automated
  checks under the default quality gate so the gap left by PYPOST-824 does not
  regress.

## Definition of Done

- After bulk-closing one or more open request tabs while at least one request
  tab remains, the active tab is a remaining request tab, not `+`.
- Bulk-closing the rightmost open request tab(s) (those next to `+`) leaves the
  active tab on a remaining request tab, not `+`.
- Bulk-closing that removes every open request tab still leaves the user on a
  blank replacement request tab (existing product rule), not on `+`.
- Single-tab close behavior from PYPOST-824 remains correct (no regression).
- Automated coverage exists (new or extended) that fails if bulk close leaves
  the active tab on `+` when a request tab remains; that coverage passes under
  `make test` / the default quality gate.
- No intentional change to plus-tab semantics (still not a request workspace;
  still used to open a new tab) or to unrelated tab navigation beyond what
  bulk-close focus requires.

## Task Description

**Problem:** Closing one request tab already reselects a remaining request
workspace so the user never lands on `+`. Closing several open request tabs in
one operation (bulk close, such as when removing requests that still have tabs
open) can still leave the active tab on `+` when the rightmost open request
tab(s) are among those removed. Source:
[PYPOST-831](https://pypost.atlassian.net/browse/PYPOST-831), deferred from
[PYPOST-824](https://pypost.atlassian.net/browse/PYPOST-824) tech debt.

**Business need:** Focus after any tab removal must be consistent. Landing on
`+` interrupts work and breaks the multi-tab editing workflow the same way for
bulk close as it did for single close. Maintainers need the bulk path covered
so the product rule stays locked in CI.

### In Scope

- Correct post-bulk-close focus so the active tab is always a request tab when
  any remain (including after removing the rightmost open request tab(s)).
- Alignment of bulk-close focus with the same product rule already applied to
  single-tab close.
- Automated regression protection for the bulk-close focus rule under the
  default quality gate.
- Completing Steps 1–7 workflow artifacts.

### Out of Scope

- Redesign of the plus-tab chrome or new-tab UX.
- Changing when bulk close runs (for example which product actions close tabs
  for deleted requests); only the post-close focus outcome after bulk removal.
- Broader tab-bar redesign or keyboard next/previous navigation changes beyond
  what bulk-close focus consistency requires.
- New MainWindow e2e / GUI automation beyond presenter-level (or equivalent
  existing) automated checks for this rule.

## Functional Requirements

- After bulk-closing any set of open request tabs while at least one request tab
  remains, the active tab must be a request tab (not `+`).
- Bulk-closing the rightmost open request tab(s) must obey the same rule.
- If bulk close removes all open request tabs, the user must still land on a
  blank replacement request tab (existing product rule), not on `+`.
- Single-tab close must continue to obey the same focus rule (no regression from
  PYPOST-824).
- Closing `+` remains a no-op; `+` is never treated as a closable request
  workspace.

## Non-functional Requirements

- **Consistency:** Post-close focus after bulk removal must match the product
  rule already enforced for single-tab close and for next/previous navigation
  (skip `+`).
- **Regression protection:** Bulk-close focus must be covered by automated
  checks under the default quality gate.
- **Minimal change:** Prefer the smallest product fix that restores correct
  focus after bulk close; avoid unrelated tab-bar changes.
- **Quality gate stability:** Existing single-close focus coverage remains green.

## Constraints and Assumptions

- Programming language: Python 3.10+.
- Parent / related: [PYPOST-824](https://pypost.atlassian.net/browse/PYPOST-824)
  fixed single-tab close focus; this ticket is the recorded Low-priority debt
  follow-up for the bulk-close path.
- “Bulk close” means removing more than one open request tab in one user- or
  system-driven operation that closes tabs for a set of requests (for example
  after deleting requests that still have tabs open).
- Story points: 3; issue type: Debt; priority: Medium; sprint: Gateway & tab
  test debt.
- Approval for Step 1 artifacts is treated as granted under sprint-task-runner
  autonomy.

## Main Entities and Interactions

| Entity | Role |
| --- | --- |
| Request tab | Editable request workspace the user focuses on |
| Plus / new-tab control | Trailing chrome to open a tab; not a request workspace |
| Active tab | Currently focused tab after close |
| Single-tab close | User closes one request tab (already fixed in PYPOST-824) |
| Bulk close | Operation that closes several open request tabs at once |
| Navigable request tabs | Request tabs the user may focus (excludes `+`) |

Interaction overview:

1. User has two or more request tabs open, plus trailing `+`.
2. A bulk-close operation removes one or more of those request tabs, including
   possibly the rightmost one(s) next to `+`.
3. System finishes removal and selects a remaining request tab when any remain.
4. User continues work on a request workspace; `+` is never the active tab.

## Q&A

- Q: Why is this a separate ticket from PYPOST-824?
  A: PYPOST-824 fixed single-tab close and deferred bulk close as tech debt so
  the single-close fix could ship without expanding scope. Users can still hit
  the same focus trap via bulk close.
- Q: What is the business “why” behind the technical debt note?
  A: After bulk removal of rightmost open request tabs, the user can be left on
  `+`, which is not a request workspace. The product rule is the same as for
  single close: stay on a request tab when any remain.
- Q: Does this change when tabs are closed in bulk?
  A: No. It only requires correct focus afterward. Triggers for bulk close stay
  as they are today.
- Q: Must single-close behavior change again?
  A: No. Single close must stay correct; bulk close must catch up to the same
  rule.
- Q: Is redesign of `+` in scope?
  A: No. `+` remains new-tab chrome, not a request workspace.
- Q: Why omit naming specific APIs or helpers in requirements?
  A: Step 1 states the focus outcome. How bulk close reselects a request tab
  belongs in architecture and development.
