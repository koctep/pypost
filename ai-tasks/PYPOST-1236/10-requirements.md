# PYPOST-1236: Pin display-value ownership regression coverage

## Goals

Protect the display-value ownership contract so that a green regression suite reliably proves the
three relevant acceptance conditions independently:

- flat-item lookup delegates display matching to the shared ownership rule;
- flat-item lookup does not perform its own duplicate display comparison; and
- tree lookup retains the same shared matching ownership and its existing contract checks.

The business reason is to prevent future maintenance changes from weakening the ownership guard
while leaving the regression suite falsely green. This gives maintainers trustworthy CI feedback
when the shared display-value contract is changed or an ownership check is accidentally disabled.

## User Stories

- As a maintainer, I want each display-value ownership condition to be independently protected so
  that removing one condition causes a clear regression failure.
- As a reviewer, I want the regression coverage to exercise both flat and tree lookup ownership so
  that the acceptance contract is visible through the lookup results and diagnostics.
- As a CI consumer, I want failures to identify the specific ownership condition that was violated
  so that the next corrective action is apparent.

## Definition of Done

- **AC-1 — Shared ownership:** The regression coverage fails when flat-item lookup no longer uses
  the shared display-value matching rule, even if it still contains another display-related check.
- **AC-2 — No duplicate ownership:** The regression coverage reports the flat duplicate-comparison
  diagnostic when flat-item lookup applies display-value ownership twice, even if the final lookup
  result appears correct.
- **AC-4 — Tree ownership:** The regression coverage independently protects the tree lookup's
  shared display-value matching behavior and existing tree ownership assertions. If tree lookup
  violates shared ownership while preserving its other checks, the regression must report the
  tree shared-ownership diagnostic. This diagnostic must be distinct from the flat delegation and
  flat duplicate-comparison diagnostics.
- The three acceptance conditions are independently pinned; a failure in one condition is not
  accepted merely because a different condition also reports a failure.
- The scope remains limited to regression coverage and introduces no change to runtime lookup
  behavior, public APIs,
  user-facing errors, logging, metrics, performance expectations, or security behavior.
- The regression coverage remains bounded and suitable for the repository's standard quality gate.
- The requirements artifact and roadmap are present, written in English, and the roadmap leaves
  Step 1 in progress (`[/]`) until the acceptance gate owner reviews it.

## Non-Functional Requirements

- Each regression scenario must complete within the repository's existing bounded test-execution
  limits and must not rely on unbounded waiting, retries, or external services.
- The scenarios must be deterministic and repeatable in local runs and in the standard CI quality
  gate.
- A failure must identify the affected ownership condition and its expected diagnostic without
  requiring interpretation of unrelated failures.
- The coverage must remain lightweight enough for the fast test suite and must not introduce
  material performance or stability risk to CI.

## Business Entities and Interactions

- **Lookup item:** A selectable item considered by lookup, with a display value and an ownership
  context that determines how that value is matched.
- **Flat lookup collection:** A set of lookup items evaluated without parent-child relationships.
  It delegates display-value matching to the shared ownership rule and must not duplicate that
  rule locally.
- **Tree lookup collection:** Lookup items arranged in parent-child relationships. It uses the
  same shared display-value ownership rule while preserving tree-specific ownership assertions.
- **Shared display-value ownership rule:** The single business rule responsible for deciding
  whether an item's display value matches the requested value. Flat and tree lookup collections
  rely on this rule rather than defining competing ownership behavior.
- **Ownership diagnostic:** The expected, condition-specific result reported when a lookup
  collection violates the ownership contract. Flat delegation, flat duplicate ownership, and tree
  shared-ownership violations each have a distinguishable diagnostic.

The interactions are: a lookup request is evaluated against lookup items; the applicable
collection delegates display-value matching to the shared rule; and an ownership violation
produces the diagnostic assigned to that condition.

## Task Description

PYPOST-1236 follows the display-value ownership hardening work in PYPOST-1041 (TD-3). The existing
regression matrix has a blind spot: one flat lookup variation combines two ownership violations,
and its expected failure wording does not distinguish them. The tree lookup's corresponding
ownership condition is also not exercised by an equivalent variation.

This task expands the regression requirements so the matrix distinguishes the flat delegation and
flat no-duplicate conditions, and so the tree condition has its own independent coverage. The work
must remain limited to regression-test assets and must not change production behavior.

**Programming language:** Python.

**In scope:**

- Independent regression protection for AC-1, AC-2, and AC-4.
- Clear association between each simulated ownership violation and its expected diagnostic.
- Preservation of existing display-value ownership and export-contract coverage.

**Out of scope:**

- Changes to production lookup functions or any runtime behavior.
- Changes to user-interface behavior, selection semantics, APIs, errors, logs, or metrics.
- Broad refactoring or unrelated improvements to the existing ownership suite.

**Constraints and assumptions:**

- The current runtime behavior already satisfies the ownership contract; this task addresses
  confidence in the guard, not a known runtime defect.
- The test suite's existing bounded-execution convention remains applicable, and all scenarios
  must be deterministic under the standard CI quality gate.
- The previously recorded PYPOST-1041 TD-3 evidence is the source context for the missing coverage.
- Later workflow steps will define the test design and implementation; no Step 3 work is performed
  as part of these requirements.

## Q&A

**Q: Why is this needed if production behavior is already correct?**

A: The risk is regression protection failure: a future change could remove or bypass one
ownership condition while all current checks remain green. Independent condition coverage makes
that loss visible in CI.

**Q: Does this change lookup behavior?**

A: No. The intended scope is limited to the regression coverage and its diagnostics.

**Q: Which language governs the task?**

A: Python, based on the repository's test and package structure.

**Q: What happens to Step 1 status?**

A: It remains `[/]` for orchestrator review; only the acceptance gate owner may mark it `[x]`.
