# PYPOST-433: Expand EnvironmentDialog Qt tests (copy/duplicate, edge cases)

## Goals

Increase automated coverage of the Manage Environments dialog so copy/duplicate flows,
name-validation branches, and variable-table edge cases are exercised in CI without
manual UI testing.

## User Stories

- As a maintainer, I want Qt tests for the environment **Copy** context-menu flow so
  regressions in cloning (variables, hidden flags, MCP state) are caught early.
- As a maintainer, I want tests for **QInputDialog** validation when copying (empty
  name, duplicate name, cancel) so user-facing error paths stay stable.
- As a maintainer, I want variable-table edge-case tests (trailing add row, invalid
  rename revert, empty selection) so table sync logic remains trustworthy.

## Definition of Done

| ID | Criterion |
| --- | --- |
| AC-1 | Tests cover `_duplicate_environment_at_row` success path (clone inserted after source, selected, model fields copied). |
| AC-2 | Tests cover copy cancel, empty-name reprompt, and duplicate-name reprompt (patched dialogs/message boxes). |
| AC-3 | Tests cover at least one additional variable-table edge case not previously asserted. |
| AC-4 | All new tests use explicit `pytest.mark.timeout` (module mark retained). |
| AC-5 | `pytest tests/test_env_dialog.py` passes. |

## Scope

**In scope:** `tests/test_env_dialog.py`, offscreen Qt tests with patched
`QInputDialog` / `QMessageBox` helpers as needed.

**Out of scope:** Production changes to `env_dialog.py` or widget implementations;
presenter/integration tests; manual QA checklist.

## Task Description

`tests/test_env_dialog.py` already covers selection, MCP toggle, add/delete, and basic
variable table load. Missing coverage: context-menu Copy / duplicate flow
(`_duplicate_environment_at_row`), QInputDialog validation branches (empty name,
duplicate name), and variable-table edge cases. Add Qt/offscreen tests with patched
dialogs/message boxes as needed. Refs: `pypost/ui/dialogs/env_dialog.py`,
`pypost/ui/widgets/environments/`.

## Q&A

*(No open questions.)*
