# PYPOST-886: Suite-wide migrate tests onto shared conftest qapp

## Goals

Maintainers need the Qt/GUI automated suite to obtain a single shared suite Qt
application the same way gateway and collection-worker units already do after
PYPOST-830 / PYPOST-884. Today dozens of modules still own a module-local
application lifecycle (`setUpClass` creation or a duplicate local `qapp`
fixture). That split is leftover consistency debt (PYPOST-830 TD-4) and makes
Qt tests harder to compare, extend, and reason about under one process.

The business outcome is a substantial, ordered migration of remaining modules
onto the shared suite Qt application convention (prefer workers → presenters →
editors), without changing product desktop behavior. Remaining surfaces after a
safe first wave may be recorded as non-blocking follow-ups with a clear
inventory.

## Programming Language

Python 3.10+

## User Stories

- As a **maintainer**, I want remaining Qt test modules to obtain a Qt
  application the same way already-aligned storage modules do, so the suite
  does not maintain dozens of local application lifecycles.
- As a **contributor**, I want one clear convention for Qt tests
  (`unittest.TestCase` and free-function styles), so editing presenter/editor
  tests does not require inventing a second local setup pattern.
- As a **desktop user** (indirect), I want this debt work not to change product
  request/collection/environment UX—only how automated checks obtain a Qt
  application.

## Definition of Done

- A meaningful ordered migration advances substantially: priority batches
  workers → presenters → editors are aligned onto the shared suite Qt
  application fixture convention (same business convention as PYPOST-830 /
  PYPOST-884).
- Covered automated checks for migrated modules continue to pass under the
  default quality gate with equivalent coverage intent (no intentional drop of
  assertions).
- An automated inventory/alignment guard proves the priority batches stay on
  the shared convention (and was red before migration).
- Any remaining non-priority modules are listed with a clear inventory as
  non-blocking follow-ups in tech-debt artifacts (or fully migrated if safe).
- No intentional change to product encryption, on-disk formats, or user-visible
  desktop UX.
- Steps 1–8 task artifacts exist for PYPOST-886.

## Task Description

**Problem:** After PYPOST-830 / PYPOST-884 aligned gateway and collection-worker
modules onto the shared suite Qt application fixture, a large remainder of the
suite still creates module-local applications (~35 `setUpClass` modules and
~23 duplicate local `qapp` fixtures at ticket creation). Source:
[PYPOST-886](https://pypost.atlassian.net/browse/PYPOST-886), from
[PYPOST-830](https://pypost.atlassian.net/browse/PYPOST-830) TD-4 /
`ai-tasks/PYPOST-830/60-tech-debt.md`.

**Business need:** Close this suite consistency debt in incremental, safe
batches so maintainers have one Qt application convention across the priority
test surfaces, without a product feature change and without an unsafe giant
sweep that risks suite hangs.

### In Scope

- Migrating remaining Qt test modules onto the shared suite fixture convention,
  preferring batches: workers → presenters → editors.
- Preserving existing check intent under the default quality gate for migrated
  modules.
- Recording any leftover inventory as non-blocking follow-ups when a full
  sweep is unsafe or too large for one task.
- Completing Steps 1–8 workflow artifacts.

### Out of Scope

- Product changes to workers, presenters, editors, dialogs, or persistence UX.
- Converting all `TestCase` modules to free-function style (optional polish;
  already related to PYPOST-885).
- Broader suite redesign, marker policy overhaul, or unrelated flake fixes
  (e.g. PYPOST-883 hang investigation) unless required to keep a migrated
  batch green.
- Changing the shared fixture’s scope or replacing it with an external plugin
  as a prerequisite for Done.

## Functional Requirements

- Priority-batch modules (workers, then presenters, then editors) must obtain a
  Qt application via the shared suite fixture convention, not via module-local
  application lifecycle ownership.
- After migration, covered checks in those modules must still exercise the same
  business behaviors they already assert, with no intentional loss of coverage
  intent.
- Product desktop behavior must remain unchanged by this task.
- Remaining non-migrated modules (if any) must be inventoriable for follow-up.

## Non-functional Requirements

- **Consistency:** Migrated modules match the shared-suite convention from
  PYPOST-830 / PYPOST-884.
- **Maintainability:** Contributors should not need a second, module-local
  pattern for the migrated surfaces.
- **Quality gate stability:** Default quality gate remains green for covered /
  migrated modules; migration must not introduce known flaky lifecycle
  failures for those surfaces.
- **Incremental safety:** Prefer small batches over one giant unsafe sweep.
- **Clarity:** Task artifacts must state what was migrated and what remains.

## Constraints and Assumptions

- Programming language: Python 3.10+.
- Shared suite Qt application fixture already exists; gateway and collection
  worker units already demonstrate the `unittest.TestCase` consumption
  convention.
- Parent / related: [PYPOST-830](https://pypost.atlassian.net/browse/PYPOST-830)
  TD-4; artifact `ai-tasks/PYPOST-830/60-tech-debt.md`. Sibling worker alignment:
  [PYPOST-884](https://pypost.atlassian.net/browse/PYPOST-884).
- Story points: 8; issue type: Debt; priority: Low.
- Approval for step artifacts is treated as granted under fully autonomous
  batch execution (no per-step user gates; no Jira calls; no git commit in this
  run).

## Main Entities and Interactions

| Entity | Attributes (business) | Role |
| --- | --- | --- |
| Maintainer / contributor | Need consistent Qt test setup | Authors and runs Qt checks |
| Shared suite Qt application fixture | Single established convention | Source of Qt application for aligned tests |
| Worker / presenter / editor checks | Priority migration batches | Must align onto shared fixture |
| Fast-follow UI / dialog / settings checks | Remaining inventory | Follow-up if not migrated safely here |
| Default quality gate | Pass/fail for covered modules | Must stay green with same coverage intent |
| Product desktop surfaces | Unchanged behavior | Out of product-change scope |

Interaction overview:

1. Maintainer inventories modules still using module-local Qt application
   lifecycle.
2. Priority batches adopt the shared suite fixture convention used by gateway /
   worker units.
3. Covered checks continue to assert the same business outcomes under the
   default quality gate.
4. Remaining inventory (if any) is recorded for follow-up; task artifacts record
   what was aligned.

## Q&A

- Q: Why migrate suite-wide now?
  A: PYPOST-830 TD-4 explicitly deferred this work; gateway/worker alignment
  left a large mixed suite that undoes the consistency win.
- Q: Does this change product desktop behavior?
  A: No. Only how automated checks obtain a Qt application instance.
- Q: Must every last dialog/settings module be migrated for Done?
  A: Prefer full migration; if unsafe or too large, Done is substantial
  progress on workers → presenters → editors plus a clear remaining inventory
  as non-blocking follow-ups.
- Q: Why omit naming specific test APIs in requirements?
  A: Step 1 states outcomes (shared convention; no product change; gate green).
  How modules are refactored belongs in architecture and development.
