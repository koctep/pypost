# PYPOST-884: Align collection storage worker tests on shared Qt application

## Goals

Maintainers need collection storage worker automated checks to obtain a Qt
application the same way gateway units already do after PYPOST-830. Today
`tests/test_collection_storage_worker.py` still owns a module-local application
lifecycle while sibling gateway modules use the shared suite fixture. That split
is leftover consistency debt (PYPOST-830 TD-2) and makes storage Qt tests harder
to compare and extend.

The business outcome is alignment of this one worker test module onto the shared
suite Qt application convention, without changing product collection load
behavior and without expanding into a suite-wide Qt migration.

## Programming Language

Python 3.10+

## User Stories

- As a **maintainer**, I want collection storage worker tests to obtain a Qt
  application the same way collection/environment gateway units do, so worker
  and gateway modules do not maintain separate application lifecycles.
- As a **contributor**, I want one clear convention for storage Qt
  `unittest.TestCase` modules, so editing worker tests does not require a
  second local setup pattern.
- As a **desktop user** (indirect), I want this debt work not to change
  collection persistence product behavior—only how automated checks obtain a Qt
  application.

## Definition of Done

- Collection storage worker unit tests no longer rely on module-local Qt
  application creation; they use the shared suite Qt application fixture
  convention (same business convention as gateway units aligned in PYPOST-830).
- Covered worker automated checks continue to pass under the default quality
  gate with equivalent coverage intent (no intentional drop of worker
  assertions).
- No intentional change to product encryption, on-disk formats, or
  user-visible collection persistence UX.
- Steps 1–8 task artifacts exist for PYPOST-884.

## Task Description

**Problem:** After PYPOST-830 aligned gateway (and H3 stress) modules onto the
shared suite Qt application fixture, the closest remaining storage Qt sibling—
collection storage worker tests—still creates a module-local application
lifecycle. Source:
[PYPOST-884](https://pypost.atlassian.net/browse/PYPOST-884), from
[PYPOST-830](https://pypost.atlassian.net/browse/PYPOST-830) TD-2 /
`ai-tasks/PYPOST-830/60-tech-debt.md`.

**Business need:** Close this small consistency debt so maintainers have one Qt
application convention for this storage worker surface, matching gateway units,
without a product feature change and without a repo-wide Qt test migration.

### In Scope

- Aligning the collection storage worker unit test module onto the shared suite
  Qt application fixture convention.
- Preserving existing worker check intent under the default quality gate.
- Completing Steps 1–8 workflow artifacts.

### Out of Scope

- Migrating the entire Qt/GUI test suite onto the shared fixture (tracked under
  broader suite migration debt such as PYPOST-886).
- Product changes to collection storage workers, gateways, encryption, or
  persistence UX.
- Converting worker `TestCase` modules to free-function style (optional polish,
  not required for Done).
- Broader suite redesign, marker policy, or unrelated flaky tests.

## Functional Requirements

- Collection storage worker unit checks must obtain a Qt application via the
  shared suite fixture convention, not via a module-local application lifecycle.
- After alignment, covered worker checks must still exercise the same business
  behaviors they already assert (worker load finished / failed outcomes), with
  no intentional loss of coverage intent.
- Product collection persistence behavior must remain unchanged by this task.

## Non-functional Requirements

- **Consistency:** Worker module matches the gateway units’ Qt application
  convention from PYPOST-830.
- **Maintainability:** Contributors should not need a second, module-local
  pattern to run this worker automated check surface.
- **Quality gate stability:** Default quality gate remains green for covered
  modules; alignment must not introduce known flaky lifecycle failures for this
  surface.
- **Scope discipline:** Do not expand into unrelated Qt test modules.
- **Clarity:** Task artifacts must state what was aligned.

## Constraints and Assumptions

- Programming language: Python 3.10+.
- Shared suite Qt application fixture already exists; gateway units already
  demonstrate the `unittest.TestCase` consumption convention.
- Parent / related: [PYPOST-830](https://pypost.atlassian.net/browse/PYPOST-830)
  TD-2; artifact `ai-tasks/PYPOST-830/60-tech-debt.md`.
- Story points: 2; issue type: Debt; priority: Low.
- Approval for step artifacts is treated as granted under fully autonomous
  batch execution (no per-step user gates; no Jira calls in this run).

## Main Entities and Interactions

| Entity | Attributes (business) | Role |
| --- | --- | --- |
| Maintainer / contributor | Need consistent storage Qt test setup | Authors and runs worker checks |
| Shared suite Qt application fixture | Single established convention | Source of Qt application for aligned tests |
| Collection storage worker checks | Async worker load finished/failed | Must align onto shared fixture |
| Gateway unit checks (reference) | Already aligned (PYPOST-830) | Consistency reference |
| Default quality gate | Pass/fail for covered modules | Must stay green with same coverage intent |
| Product collection storage worker | Unchanged load behavior | Out of product-change scope |

Interaction overview:

1. Maintainer identifies the worker module still using module-local Qt
   application lifecycle.
2. That module adopts the shared suite fixture convention used by gateway units.
3. Covered worker checks continue to assert the same business outcomes under the
   default quality gate.
4. Task artifacts record what was aligned.

## Q&A

- Q: Why align this worker module now?
  A: It is the closest remaining storage Qt sibling called out as PYPOST-830
  TD-2; leaving it on module-local setup undoes the consistency win for this
  surface.
- Q: Does this change product collection load behavior?
  A: No. Only how automated checks obtain a Qt application instance.
- Q: Is suite-wide migration required for Done?
  A: No. Done is alignment of the collection storage worker test module.
- Q: Why omit naming specific test APIs in requirements?
  A: Step 1 states outcomes (shared convention; no product change; gate green).
  How the module is refactored belongs in architecture and development.
