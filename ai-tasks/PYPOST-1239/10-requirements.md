# PYPOST-1239: Make intentional assertion repetition discoverable

## Goals

Make the intentional repeated assertions in the DisplayRole ownership suite
understandable to maintainers before they refactor the test. The business reason
is to preserve regression protection: the repetition carries information about
the ownership cases being checked, and an apparently harmless simplification can
weaken that protection.

## User Stories

- As a maintainer, I want the repeated assertions to be clearly identified as
  intentional so that I do not remove load-bearing coverage during cleanup.
- As a reviewer, I want the reason for the repetition to be documented where the
  assertions are maintained so that a proposed refactor can be evaluated against
  the regression contract.
- As a maintainer, I want developer documentation to explain the same constraint
  so that the knowledge is available beyond the test file.
- As a quality-gate owner, I want validation to detect when the required
  explanation is missing or detached from the assertion group so that the
  discoverability guarantee does not silently regress.

## Definition of Done

- **AC-1 — Local discoverability:** In
  `tests/test_display_role_scan_ownership.py`, each intentional
  `_calls_name`/`_has_display_role_attr` assertion pair has an explicit,
  readable explanation at its maintenance location:
  - the pair for `find_child`, covering delegation by
    `find_child_index_by_display_text` and the absence of its own inline
    DisplayRole ownership;
  - the pair for `find_tree`, covering delegation by
    `find_tree_index_by_display_text` and the absence of its own inline
    DisplayRole ownership; and
  - the pair for `_select_item_view`, covering delegation to the flat-child
    lookup and the absence of its own inline DisplayRole ownership.
- **AC-2 — Rationale is actionable:** The explanation states that the repetition
  is intentional, identifies the regression protection it preserves, and warns
  why combining or simplifying the assertions requires care.
- **AC-3 — Developer documentation:** The relevant developer documentation
  describes the intentional repetition, its purpose, and the maintenance
  constraint in language consistent with the local explanation.
- **AC-4 — Missing explanation is detected:** Removing the required local
  explanation causes the validation to fail with a diagnostic that identifies
  the discoverability requirement.
- **AC-5 — Detached explanation is detected:** For each of `find_child`,
  `find_tree`, and `_select_item_view`, the explanation must be locally
  associated with both assertions in its matching
  `_calls_name`/`_has_display_role_attr` pair. An explanation associated only
  with another target, only with one assertion in the pair, or only with a
  remote summary does not satisfy the requirement.
- **AC-6 — Present explanation is accepted:** The documented assertion group
  passes validation when the required explanation is present at its maintenance
  location.
- **AC-7 — Existing behavior is preserved:** The DisplayRole ownership checks,
  lookup results, user-facing behavior, and unrelated validation rules are
  unchanged.
- **AC-8 — Scope remains focused:** The change is limited to the ownership-suite
  discoverability contract, its developer documentation, and the associated task
  artifacts; it does not introduce broad cleanup or unrelated refactoring.

## Scope

### In Scope

- Making the three intentional `_calls_name`/`_has_display_role_attr` assertion
  pairs for `find_child`, `find_tree`, and `_select_item_view` identifiable to
  maintainers in `tests/test_display_role_scan_ownership.py`.
- Recording the reason that the repetition protects the ownership regression
  contract.
- Guarding the presence and association of that explanation with the assertion
  group.
- Updating the relevant developer documentation.
- Preserving clear diagnostics for a missing or misplaced explanation.

### Out of Scope

- Changing DisplayRole ownership rules or lookup semantics.
- Changing application runtime behavior, public interfaces, or user-interface
  selection behavior.
- Replacing the repeated assertions with a shared abstraction, loop, or other
  broad test refactor.
- Modifying unrelated tests, documentation, or quality-gate rules.
- Adding production logging, metrics, services, or external dependencies.

## Constraints and Assumptions

- The existing DisplayRole ownership suite is the authoritative regression
  contract for the assertion group.
- The explanation must remain understandable in the code-review context and in
  the relevant developer documentation.
- The discoverability check must distinguish the target assertion group from
  unrelated comments or documentation.
- The task must not require a display server, network service, or external data
  to verify the documentation contract.
- The repository's existing bounded quality checks remain the verification
  boundary.
- Later Top-Down steps define design and implementation details; this document
  specifies observable outcomes only.

## Main Entities and Interactions

- **Intentional assertion group:** The repeated DisplayRole ownership assertions
  whose structure is part of the regression protection.
- **Ownership regression contract:** The set of conditions the assertion group
  protects against accidental weakening during maintenance.
- **Maintenance explanation:** The local, human-readable rationale that tells a
  maintainer why the assertion group must remain recognizable.
- **Developer guidance:** The durable documentation that explains the same
  constraint and its maintenance implications.
- **Discoverability validation result:** The success or failure outcome stating
  whether the required explanation is present and associated with the target
  assertion group.

The interaction is: a maintainer encounters the intentional assertion group,
reads its local explanation, and consults the developer guidance for broader
context. A validation run checks that the explanation remains associated with
the group; it succeeds when the contract is present and reports a focused
failure when the explanation is absent or detached.

## Non-Functional Requirements

- **Determinism:** The discoverability result must be repeatable across local and
  standard CI runs, with stable diagnostics.
- **Bounded execution:** Validation must complete within the repository's normal
  fast quality checks and must not use unbounded retries, sleeps, or external
  services.
- **Maintainability:** The local explanation and developer guidance must use
  consistent, plain English and identify the protected contract clearly.
- **Low impact:** The task must not materially increase quality-gate runtime or
  introduce application stability risk.
- **Compatibility:** No application runtime behavior or user-visible behavior
  may change as a result of this maintenance contract.

## Task Description

PYPOST-1239 is a follow-up from the PYPOST-1041 technical-debt analysis. The
DisplayRole ownership suite intentionally repeats assertion pairs, but the
reason for that repetition is currently recorded only in an earlier task
artifact. A maintainer reading the suite can therefore mistake the repetition
for accidental duplication and weaken the regression coverage during cleanup.

The task makes the constraint discoverable at the point of maintenance and in
developer documentation, and keeps that discoverability requirement protected
by validation. The task is a Python repository maintenance task focused on test
and documentation contracts; it does not change production behavior.

## Q&A

**Q: Why is the repetition being preserved?**

A: The repeated assertions are load-bearing regression coverage. Simplifying
them without understanding the contract can make the ownership guard pass for
the wrong reason.

**Q: Does this task change the ownership checks?**

A: No. It makes the existing maintenance constraint discoverable and protects
that discoverability; the ownership rules and lookup behavior remain unchanged.

**Q: What counts as sufficient documentation?**

A: A maintainer must be able to identify the matching `_calls_name` and
`_has_display_role_attr` assertions for each of `find_child`, `find_tree`, and
`_select_item_view`; recognize both assertions as one intentional local pair;
understand why the repetition matters; and find matching context in the
developer guide.

**Q: Which language governs the task?**

A: Python, based on the repository's existing package and test structure.

**Q: What is the Step 1 status?**

A: Step 1 has passed acceptance. The requirements are fixed and approved as the
basis for the Step 2 architectural design.
