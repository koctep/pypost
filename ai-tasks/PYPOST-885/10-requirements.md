# PYPOST-885: Convert gateway TestCase modules to free functions with qapp

## Goals

Maintainers need collection/environment gateway and H3 stress automated checks
to consume the shared suite Qt application the same way responsiveness tests
already do: plain pytest functions with a `qapp` parameter. Today those three
modules still use `unittest.TestCase` plus `@pytest.mark.usefixtures("qapp")`
after PYPOST-830. That split is leftover style debt (PYPOST-830 TD-3) and makes
sibling storage Qt tests harder to compare and extend.

The business outcome is optional style polish that unifies this gateway surface
onto the free-function `qapp` convention, without changing product storage
behavior and without expanding into a suite-wide TestCase migration.

## Programming Language

Python 3.10+

## User Stories

- As a **maintainer**, I want gateway and H3 stress checks to obtain a Qt
  application the same way responsiveness tests do, so storage Qt modules do
  not maintain two fixture-consumption styles for the same surface.
- As a **contributor**, I want one clear free-function convention for these
  gateway modules, so editing them does not require `unittest.TestCase` plus
  `usefixtures` when siblings already use a `qapp` parameter.
- As a **desktop user** (indirect), I want this debt work not to change
  environment or collection persistence product behavior—only how automated
  checks are structured.

## Definition of Done

- Collection gateway, environment gateway, and H3 stress test modules no longer
  use `unittest.TestCase` + `usefixtures("qapp")`; they use free pytest
  functions with a `qapp` parameter (same business convention as
  `test_env_storage_responsiveness.py`).
- Covered gateway/stress automated checks continue to pass under the default
  quality gate with equivalent coverage intent (no intentional drop of
  assertions).
- No intentional change to product encryption, on-disk formats, or
  user-visible persistence UX.
- Steps 1–8 task artifacts exist for PYPOST-885.
- If conversion is judged large/risky, deferral is documented with evidence and
  DoD is adjusted accordingly (this run prefers convert when low-risk).

## Task Description

**Problem:** After PYPOST-830 aligned gateway (and H3 stress) modules onto the
shared suite Qt application fixture via `usefixtures`, an optional style debt
remains: those modules still use `unittest.TestCase` while responsiveness uses
free functions with a `qapp` parameter. Source:
[PYPOST-885](https://pypost.atlassian.net/browse/PYPOST-885), from
[PYPOST-830](https://pypost.atlassian.net/browse/PYPOST-830) TD-3 /
`ai-tasks/PYPOST-830/60-tech-debt.md`.

**Business need:** Close this optional consistency debt so maintainers have one
fixture-consumption style for this gateway surface, matching responsiveness,
without a product feature change and without a repo-wide TestCase rewrite.

### In Scope

- Converting the three target modules (collection gateway, environment gateway,
  H3 stress) from `TestCase` + `usefixtures` to free functions with `qapp`.
- Preserving existing check intent under the default quality gate.
- Completing Steps 1–8 workflow artifacts.

### Out of Scope

- Migrating the entire Qt/GUI test suite away from `unittest.TestCase`
  (broader debt such as PYPOST-886 / other surfaces).
- Product changes to storage gateways, workers, encryption, or persistence UX.
- Converting collection storage worker `TestCase` (related polish may reuse
  this ticket’s pattern later; not required for Done here).
- Broader suite redesign, marker policy, or unrelated flaky tests.

## Functional Requirements

- Target gateway/stress checks must be expressed as free pytest functions that
  request the shared suite Qt application via a `qapp` parameter.
- After conversion, covered checks must still exercise the same business
  behaviors they already assert (async load/save / queue / H3 stress cycles),
  with no intentional loss of coverage intent.
- Product environment and collection persistence behavior must remain unchanged
  by this task.

## Non-functional Requirements

- **Consistency:** Target modules match the responsiveness free-function `qapp`
  convention.
- **Maintainability:** Contributors should not need `TestCase` + `usefixtures`
  for this gateway surface when siblings already use a parameter.
- **Quality gate stability:** Default quality gate remains green for covered
  modules; conversion must not introduce known flaky lifecycle failures.
- **Scope discipline:** Do not expand into unrelated Qt test modules.
- **Clarity:** Task artifacts must state what was converted (or why deferred).

## Constraints and Assumptions

- Programming language: Python 3.10+.
- Shared suite Qt application fixture already exists; responsiveness already
  demonstrates the free-function consumption convention.
- Parent / related: [PYPOST-830](https://pypost.atlassian.net/browse/PYPOST-830)
  TD-3; artifact `ai-tasks/PYPOST-830/60-tech-debt.md`.
- Story points: 2; issue type: Debt; priority: Lowest.
- Approval for step artifacts is treated as granted under fully autonomous
  batch execution (no per-step user gates; no Jira calls; no git commit in
  this run).

## Main Entities and Interactions

| Entity | Attributes (business) | Role |
| --- | --- | --- |
| Maintainer / contributor | Need consistent gateway test style | Authors and runs checks |
| Shared suite Qt application fixture | Single established convention | Source of Qt application |
| Gateway / H3 stress checks | Async load/save / queue / stress | Must adopt free-function style |
| Responsiveness checks (reference) | Already free functions + `qapp` | Style reference |
| Default quality gate | Pass/fail for covered modules | Must stay green with same coverage intent |
| Product storage gateways | Unchanged load/save behavior | Out of product-change scope |

Interaction overview:

1. Maintainer identifies gateway/stress modules still on `TestCase` +
   `usefixtures` while responsiveness uses free functions + `qapp`.
2. Those modules adopt the free-function convention.
3. Covered checks continue to assert the same business outcomes under the
   default quality gate.
4. Task artifacts record what was converted (or deferred with evidence).

## Q&A

- Q: Why convert these modules now?
  A: They are the exact optional polish called out as PYPOST-830 TD-3; leaving
  two styles on the same surface undoes the consistency win for maintainers.
- Q: Does this change product persistence behavior?
  A: No. Only how automated checks are structured to obtain a Qt application.
- Q: Is suite-wide TestCase removal required for Done?
  A: No. Done is conversion of the three gateway/stress modules (or documented
  deferral if conversion is large/risky).
- Q: Why omit naming specific test APIs in requirements?
  A: Step 1 states outcomes (free-function convention; no product change; gate
  green). How modules are refactored belongs in architecture and development.
