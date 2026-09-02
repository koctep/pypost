# PYPOST-1237: Report all DisplayRole ownership violations together

## Goals

Ensure that validation of DisplayRole ownership reports every violation found in the evaluated
scope in one failure result. The business reason is to give maintainers a complete and actionable
diagnosis in a single run, reducing repeated fix-and-rerun cycles and preventing later violations
from being hidden by an earlier failure.

## User Stories

- As a maintainer, I want one validation result to list all DisplayRole ownership violations so
  that I can address the complete set of problems without repeated discovery cycles.
- As a reviewer, I want each reported violation to remain identifiable so that I can understand
  which ownership rule is affected and verify the corrective change.
- As a CI consumer, I want validation to fail when any violation exists while still showing all
  discovered violations so that the result is useful for prioritizing fixes.

## Definition of Done

- **AC-1 — Complete aggregation:** When multiple DisplayRole ownership violations are present in
  the evaluated scope, one failure result reports every discovered violation from that scope.
- **AC-2 — No fail-fast loss:** The first discovered violation does not prevent subsequent
  DisplayRole ownership violations in the same scope from being reported.
- **AC-3 — Single failure outcome:** A scope containing one or more violations produces one
  failing validation outcome rather than separate outcomes that require multiple reruns to reveal
  the complete set.
- **AC-4 — Diagnostic identity:** Each reported violation retains enough identifying information
  to distinguish the affected lookup context and ownership condition.
- **AC-5 — Clean control:** A scope with no DisplayRole ownership violations continues to produce
  a successful validation outcome with no violation diagnostics.
- **AC-6 — Scope preservation:** Existing DisplayRole ownership rules and the meaning of an
  individual violation remain unchanged; only the completeness and presentation of the failure
  result are changed.
- The change does not alter lookup results, public interfaces, user-facing selection behavior,
  or unrelated validation outcomes.

## Non-Functional Requirements

- Reporting must be deterministic and repeatable in local runs and the standard CI quality gate.
- Violation reporting must preserve a stable, understandable order so that repeated runs are easy
  to compare.
- The validation must remain bounded and must not depend on unbounded retries, sleeps, or external
  services.
- The combined diagnostic must remain readable and actionable when several violations are found.
- The change must not introduce material performance or stability risk to the fast test suite.

## Business Entities and Interactions

- **DisplayRole ownership rule:** The business rule that determines which lookup context owns and
  validates a display value.
- **Lookup context:** A flat or hierarchical collection in which DisplayRole ownership is checked.
  It identifies where a violation occurs and which ownership condition is affected.
- **Ownership violation:** A discovered mismatch between the required DisplayRole ownership rule
  and the behavior of a lookup context, including the identifying information needed for diagnosis.
- **Validation scope:** The set of lookup contexts evaluated together during one validation run.
- **Validation result:** The success or failure outcome for one validation scope. A failing result
  contains all ownership violations discovered in that scope.

The interaction is: a validation run evaluates the DisplayRole ownership rule across its validation
scope; each violating lookup context contributes an identifiable diagnostic; and the validation
result combines all such diagnostics into one failure outcome. A violation-free scope produces a
successful result.

## Task Description

The current validation behavior stops at the first DisplayRole ownership violation. This obscures
additional violations in the same evaluated scope and forces maintainers to repeat the validation
after each correction. PYPOST-1237 changes the requirement to complete reporting: one validation
outcome must report all ownership violations found in the evaluated scope.

**Programming language:** Python.

**In scope:**

- Aggregating all DisplayRole ownership violation diagnostics found in one validation scope.
- Preserving distinct identity and stable ordering for the included diagnostics.
- Preserving successful validation when no violations are found.
- Regression coverage for multiple violations, a single violation, and a clean control case.

**Out of scope:**

- Changing the DisplayRole ownership rules or lookup semantics.
- Changing public APIs, user-interface behavior, selection results, logging, or metrics.
- Aggregating unrelated assertion failures or validation domains.
- Broad refactoring or unrelated cleanup.

**Constraints and assumptions:**

- The existing ownership rules and individual violation diagnostics are the source of truth.
- The requirement applies to violations discovered within one validation scope; separate runs may
  continue to produce separate validation results.
- The combined failure must remain compatible with the repository's normal bounded CI checks.
- Later workflow steps will define the design and implementation details; this Step 1 artifact
  does not prescribe them.

## Q&A

**Q: Why report all violations together?**

A: A complete result lets maintainers fix all known ownership problems in one iteration and makes
the validation outcome more useful for review and CI triage.

**Q: Does this change which situations are violations?**

A: No. It changes only whether multiple already-detected violations are exposed together.

**Q: What happens when there are no violations?**

A: Validation remains successful and produces no ownership-violation diagnostics.

**Q: Which language governs the task?**

A: Python, based on the repository's existing package and test structure.

**Q: What happens to Step 1 status?**

A: It remains `[/]` for review; only the acceptance gate owner may mark it `[x]`.
