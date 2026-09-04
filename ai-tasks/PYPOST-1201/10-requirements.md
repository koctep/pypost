# PYPOST-1201: Optional shared silent transport test support

## Goals

The test suite needs a dependable way to exercise WebSocket UI lifecycle scenarios
without live network conditions or unrelated deferred failures changing the result.
This protects confidence in tests that verify user-facing connection states and keeps
asynchronous test outcomes repeatable.

The business need is to reduce maintenance cost when multiple UI scenarios require
the same silent, network-independent transport behavior. A shared capability is
valuable only when it removes meaningful duplication or inconsistency. Introducing
shared support without demonstrated reuse would add suite-wide coupling without a
corresponding benefit.

This task therefore requires an explicit reuse decision. The outcome is conditional:
retain the current local test support when reuse is not justified, or adopt shared
test support only when the reuse threshold is met.

## User Stories

- As a test maintainer, I want WebSocket UI lifecycle tests to remain isolated from
  external network behavior so that failures describe the product scenario under
  test.
- As a test maintainer, I want common silent transport behavior to have one clear
  source when multiple UI scenarios genuinely need it, so that updates do not
  diverge between consumers.
- As a test maintainer, I want to avoid shared test dependencies when there is no
  demonstrated reuse, so that the test suite remains easy to understand and change.

## Definition of Done

- The requirements review records the current consumers and the evidence for or
  against reuse at the level of relevant UI test scenarios.
- The decision uses an explicit threshold: a shared capability is justified only
  when at least one additional relevant UI test scenario needs materially the same
  silent transport behavior, or when existing consumers demonstrate meaningful
  duplication that would otherwise diverge.
- If that threshold is met, the resulting test support preserves the existing
  observable behavior for every affected scenario and does not introduce live
  network dependence.
- If that threshold is not met, the current local test support is retained and the
  decision, evidence, and reason for deferring shared support are recorded. No shared
  test surface is required in that case.
- No production runtime behavior, WebSocket protocol behavior, or user-facing
  feature is changed by this debt item.
- The relevant test scenarios remain deterministic, isolated, and compatible with
  the repository's normal test execution.
- The task scope contains only the decision record and any narrowly justified
  test-support change; unrelated test cleanup is excluded.

## Task Description

### Problem

WebSocket UI regression coverage needs silent, network-independent transport
behavior so that lifecycle results are not affected by DNS, remote services, or
unrelated delayed callbacks. The initial inventory identified one current UI test
scenario consuming this behavior and no additional relevant consumer. Similar
transport doubles in unrelated test contexts do not by themselves establish reuse
or interchangeable responsibilities.

The source issue, [PYPOST-1201](https://pypost.atlassian.net/browse/PYPOST-1201),
describes this as a non-blocking optional reuse decision. The task must first
establish whether reuse is real and beneficial. The current local test support is not
required to become shared support unless the evidence meets the stated threshold.

### Scope

In scope:

- Confirming the business need for silent, network-independent WebSocket UI test
  scenarios.
- Identifying current and plausible additional consumers of that behavior at the
  scenario level.
- Comparing the maintenance benefit of sharing against the coupling and churn of
  introducing a common test dependency.
- Recording either a justified reuse decision or an explicit decision to retain the
  current local test support.
- Preserving deterministic behavior and existing test intent for any affected
  scenarios.

Out of scope:

- Changes to production WebSocket transports, session state, or UI behavior.
- Redesigning the WebSocket test strategy or consolidating every transport double.
- Renaming or merging redundant lifecycle tests covered by PYPOST-1200.
- Adding shared support solely because similarly named doubles exist in unrelated
  tests.
- Network integration coverage, performance work, and unrelated test refactoring.

### Constraints and assumptions

- Any change remains limited to test support; production behavior is unchanged.
- No live network access or environment-dependent behavior may be introduced into
  scenarios that rely on silent transport behavior.
- The current local test support is the default when no additional consumer or
  meaningful duplication is demonstrated.
- The decision must be reversible and documented clearly enough for a later task to
  revisit it if a new consumer appears.

### Main entities and relationships

| Entity | Relevant attributes | Relationship |
| --- | --- | --- |
| UI lifecycle scenario | State assertions; deterministic, isolated result | May require silent transport behavior |
| Silent transport behavior | No external network; stable result | Supports matching UI scenarios |
| Test maintainer | Reliable feedback; low maintenance cost | Evaluates evidence and disposition |
| Reuse decision record | Evidence; disposition; revisit trigger | Explains the chosen outcome |

### Decision path

1. Inventory current and candidate UI scenarios that need silent, network-independent
   transport behavior.
2. Determine whether another relevant scenario needs materially the same behavior or
   whether duplication is substantial enough to risk divergence.
3. If the evidence meets the threshold, adopt shared test support and confirm that
   current test outcomes and isolation are preserved.
4. If the evidence does not meet the threshold, retain the current local test
   support, record the evidence, and identify the event that would justify revisiting
   the decision.

## Q&A

### Why is this task needed?

Asynchronous WebSocket UI tests should report regressions in the UI lifecycle,
not failures caused by DNS, remote services, or unrelated delayed callbacks. If
several tests need the same isolation, sharing can reduce drift and maintenance.

### Is shared support mandatory?

No. PYPOST-1201 is explicitly optional. The correct outcome may be to keep the
current local test support when reuse is not demonstrated.

### What counts as sufficient reuse evidence?

At least one additional relevant UI scenario with materially the same silent
transport need, or clear meaningful duplication that creates a realistic risk of
inconsistent maintenance. Similar names alone do not qualify.

### What happens if there is only one consumer?

The current local test support remains in place. The decision and its evidence are
recorded, and a future consumer can reopen the question without forcing suite-wide
coupling now.

### Does this task change production behavior?

No. The scope is limited to test-support organization and the decision record.
