# PYPOST-830: Align gateway tests on shared Qt application fixture

## Goals

Maintainers need a single, consistent way for storage-gateway automated checks
to obtain a Qt application instance. Today some gateway unit modules still
create their own module-local application lifecycle, while the environment
storage responsiveness suite already uses the shared suite fixture. That split
duplicates lifecycle setup, makes gateway tests harder to compare and extend,
and leaves an open consistency debt from PYPOST-823.

The business outcome is alignment: remaining gateway (and closely related
gateway stress) checks use the same shared Qt application fixture convention as
the responsiveness suite, without changing product load/save behavior and
without expanding into a suite-wide Qt migration.

## Programming Language

Python 3.10+

## User Stories

- As a **maintainer**, I want environment and collection storage gateway unit
  tests to obtain a Qt application the same way the responsiveness suite does,
  so gateway test modules do not each maintain a separate application lifecycle.
- As a **contributor**, I want gateway-related automated checks to follow one
  clear convention for Qt application setup, so adding or editing gateway tests
  does not require inventing another local lifecycle pattern.
- As a **maintainer**, I want gateway (and closely related gateway stress)
  modules that still use module-local application setup brought onto the shared
  fixture, so PYPOST-823 / PYPOST-829 deferred consistency debt is closed for
  this surface.
- As a **desktop user** (indirect), I want this debt work not to change
  environment or collection load/save product behavior—only how automated
  checks obtain a Qt application.

## Definition of Done

- Environment and collection storage gateway unit test modules no longer rely on
  module-local Qt application creation for their checks; they use the shared
  suite Qt application fixture convention (same business convention as the
  environment storage responsiveness suite).
- Any closely related gateway stress module that still uses module-local Qt
  application creation for the same reason is aligned the same way, or an
  explicit out-of-scope deferral with rationale is recorded in task artifacts.
- Gateway automated checks covered by this task continue to pass under the
  default quality gate with equivalent coverage intent (no intentional drop of
  gateway assertions).
- No intentional change to product encryption, on-disk formats, or user-visible
  environment/collection persistence UX.
- Steps 1–7 task artifacts exist for PYPOST-830.

## Task Description

**Problem:** After PYPOST-823, remaining storage-gateway unit tests still create
a module-local Qt application lifecycle instead of using the shared suite
fixture already used by the environment storage responsiveness suite. Related
follow-ups (PYPOST-827–829) deferred that alignment to this ticket. Duplicate
lifecycle setup increases maintenance cost and inconsistency across the gateway
test surface. Source:
[PYPOST-830](https://pypost.atlassian.net/browse/PYPOST-830), follow-up from
[PYPOST-823](https://pypost.atlassian.net/browse/PYPOST-823).

**Business need:** Close consistency debt for the storage-gateway automated
check surface so maintainers have one Qt application convention there, matching
the responsiveness suite, without a product feature change and without a
repo-wide Qt test migration.

### In Scope

- Aligning environment and collection storage gateway unit test modules onto
  the shared suite Qt application fixture convention.
- Aligning any closely related gateway stress module that still uses
  module-local Qt application creation for the same gateway surface, when it is
  part of the remaining debt called out for this ticket.
- Preserving existing gateway check intent (pass/fail meaning of assertions)
  under the default quality gate.
- Completing Steps 1–7 workflow artifacts.

### Out of Scope

- Migrating the entire Qt/GUI test suite onto the shared fixture.
- Product changes to environment or collection storage gateways, encryption, or
  persistence UX.
- Re-doing hang-resistant wait work (PYPOST-823 / PYPOST-827), timeout
  diagnostics (PYPOST-828), or H3 worker-teardown investigation/fix
  (PYPOST-829), except where a gateway stress module’s application setup is
  the only remaining alignment item for this ticket.
- Broader suite redesign, marker policy, or unrelated flaky tests.

## Functional Requirements

- Environment storage gateway unit checks must obtain a Qt application via the
  shared suite fixture convention, not via a module-local application lifecycle.
- Collection storage gateway unit checks must do the same.
- Closely related gateway stress checks that still use module-local application
  creation for this surface must either align the same way or be explicitly
  deferred with rationale in task artifacts.
- After alignment, covered gateway checks must still exercise the same business
  behaviors they already assert (load/save gateway outcomes and related
  guarantees), with no intentional loss of coverage intent.
- Product environment and collection persistence behavior must remain unchanged
  by this task.

## Non-functional Requirements

- **Consistency:** Gateway unit (and in-scope stress) modules match the
  responsiveness suite’s Qt application convention.
- **Maintainability:** Contributors should not need a second, module-local
  pattern to run gateway automated checks that need a Qt application.
- **Quality gate stability:** Default quality gate remains green for covered
  modules; alignment must not introduce known flaky lifecycle failures for this
  surface.
- **Scope discipline:** Do not expand into unrelated Qt test modules.
- **Clarity:** Task artifacts must state which modules were aligned and any
  explicit deferrals.

## Constraints and Assumptions

- Programming language: Python 3.10+.
- Shared suite Qt application fixture already exists and is the established
  convention for modules such as the environment storage responsiveness suite.
- Prior work: PYPOST-823 deferred shared-fixture alignment as Low debt;
  PYPOST-827–829 kept product/wait/diagnostics/H3 work separate and pointed
  consistency debt here.
- Parent / related: [PYPOST-823](https://pypost.atlassian.net/browse/PYPOST-823);
  debt also referenced from PYPOST-827/828/829 tech-debt artifacts.
- “Module-local Qt application lifecycle” means a test module creating or
  owning its own application instance setup instead of using the shared suite
  fixture convention.
- Story points: 2; issue type: Debt; priority: Medium.
- Approval for Step 1 artifacts is treated as granted under sprint-task-runner
  autonomy.

## Main Entities and Interactions

| Entity | Attributes (business) | Role |
| --- | --- | --- |
| Maintainer / contributor | Need consistent gateway test setup | Authors and runs gateway checks |
| Shared suite Qt application fixture | Single established convention | Source of Qt application for aligned tests |
| Environment storage gateway unit checks | Async env load/save assertions | Must align onto shared fixture |
| Collection storage gateway unit checks | Async collection load/save assertions | Must align onto shared fixture |
| Gateway stress checks (if in remaining debt) | Heavy churn on gateway surface | Align or explicitly defer |
| Environment storage responsiveness suite | Already uses shared fixture | Consistency reference |
| Default quality gate | Pass/fail for covered modules | Must stay green with same coverage intent |
| Product storage gateways | Unchanged load/save UX | Out of product-change scope |

Interaction overview:

1. Maintainer identifies gateway (and closely related stress) modules that still
   use module-local Qt application lifecycle.
2. Those modules adopt the shared suite fixture convention used by the
   responsiveness suite.
3. Covered gateway checks continue to assert the same business outcomes under
   the default quality gate.
4. Task artifacts record what was aligned and any explicit deferral.

## Q&A

- Q: Why align on a shared fixture instead of leaving module-local setup?
  A: Duplicate Qt application lifecycle across gateway modules increases
  maintenance cost and inconsistency. PYPOST-823 already established the shared
  convention via the responsiveness suite; remaining gateway modules should
  match it.
- Q: Why is this a business/test-quality goal rather than a product feature?
  A: Users do not see a new feature. Maintainers get a clearer, single
  convention for gateway automated checks, reducing debt and future churn risk.
- Q: Which modules are primary?
  A: Environment and collection storage gateway unit test modules. Closely
  related gateway stress modules that still use module-local setup are in scope
  when they are part of this deferred debt; otherwise defer with rationale.
- Q: Does this change product load/save behavior?
  A: No. Only how automated checks obtain a Qt application instance.
- Q: Is a full-suite Qt migration required for Done?
  A: No. Suite-wide migration is out of scope. Done is alignment of the remaining
  gateway surface called out for this ticket.
- Q: How does this relate to PYPOST-823 / 827 / 828 / 829?
  A: 823 deferred shared-fixture consistency; 827–829 owned wait sharing,
  timeout diagnostics, and H3 teardown. This ticket only closes the gateway
  shared-fixture alignment debt.
- Q: Why omit naming specific test APIs or refactor steps in requirements?
  A: Step 1 states outcomes (shared convention; no product change; gate green).
  How modules are refactored belongs in architecture and development.
