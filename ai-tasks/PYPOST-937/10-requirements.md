# PYPOST-937: Share Makefile help/recipe parse helpers

## Goals

PYPOST-922 added Makefile contract locks for the `test-agent-e2e` packaging
entry, with local parsers (`_test_agent_e2e_help_comment` and
`_test_agent_e2e_default_recipe_body`) embedded in `tests/test_makefile.py`.
As more make-entry locks land, duplicating that parsing logic would increase
maintenance cost and drift risk.

Business value: one reusable, tested parser surface for Makefile `##` help
lines and target recipe bodies so future packaging/CI contract locks stay
consistent and cheap to add.

Source: [PYPOST-922](https://pypost.atlassian.net/browse/PYPOST-922)
`60-tech-debt.md` follow-up 2.

## Programming Language

Python (`.cursor/lsr/do-python.md`) for test helpers and contract locks.
Developer docs in English Markdown (`.cursor/lsr/do-markdown.md`).

## User Stories

- As a **maintainer adding a make-entry lock**, I want shared help/recipe
  parsers so I do not copy-paste Makefile parsing logic.
- As a **reviewer**, I want existing PYPOST-922 contract tests to stay green
  after the refactor so packaging discoverability locks do not regress.
- As a **contributor reading tests**, I want parser helpers in a small module
  with unit coverage so behavior is obvious and stable.

## Definition of Done

- Shared helpers extract `##` help text and recipe body for an arbitrary make
  target name from Makefile source text.
- At least two make-entry lock surfaces use the shared helpers (not only
  `test-agent-e2e`).
- Existing PYPOST-922 contract tests for `test-agent-e2e` remain green.
- Unit tests cover the shared helpers against committed Makefile content.
- Developer docs note the helper module for future lock authors.
- No git commit in this run (orchestrator constraint).

Acceptance (from Jira): **Shared helpers used by multiple make-entry locks;
existing PYPOST-922 contract tests stay green.**

## Task Description

**Problem:** Makefile contract tests in `tests/test_makefile.py` embed
target-specific parser helpers for `test-agent-e2e`. PYPOST-922 tech debt
flagged deduplication once additional make-entry locks appear.

**Business need:** Reduce duplication and standardize Makefile static parsing
for contract tests.

### In Scope

- Extract generic `makefile_target_help_comment` and
  `makefile_target_recipe_body` helpers.
- Refactor `test-agent-e2e` locks to use shared helpers.
- Add at least one additional make-entry lock consumer (e.g. `test` target).
- Unit tests for the helper module.
- Brief dev-doc pointer for future lock authors.

### Out of Scope

- Changing Makefile recipes or help wording (unless a lock proves drift).
- Production code changes.
- New product packaging behavior.
- Git commit / Jira transitions (orchestrator).

## Functional Requirements

- FR1: Helpers accept Makefile text and target name; return help comment or
  recipe body string.
- FR2: `TestAgentE2eTargetRecipe` (PYPOST-922 locks) uses shared helpers.
- FR3: A second make-entry lock class uses the same helpers.
- FR4: All existing PYPOST-922 assertions remain satisfied.
- FR5: Helper module has dedicated unit tests with timeout markers.

## Non-Functional Requirements

- **Stability:** Parser behavior matches prior local helpers for
  `test-agent-e2e`.
- **Minimalism:** Small module; no over-abstraction beyond two functions.
- **Test hygiene:** Explicit timeout markers per `.cursor/lsr/do-testing.md`.

## Constraints and Assumptions

- Refactor-only; no runtime behavioral change to make targets.
- Sprint-task-runner autonomy — no per-step user approval gates.
- Do not commit in this run.

## Main Entities and Interactions

| Entity | Role |
| --- | --- |
| Shared parser module | Generic Makefile text parsers |
| Make-entry lock tests | Static contract asserts on help/recipe |
| PYPOST-922 locks | Primary consumer; must stay green |
| Second lock surface | Proves reuse (e.g. `test` target) |

## Q&A

- Q: Is Step 3 N/A?
  A: No. New helper module + import test is red until Step 4 lands the
  implementation.

- Q: Must we add a brand-new packaging lock?
  A: No. A second make-entry lock on an existing target (e.g. `test`) is
  sufficient to meet acceptance.
