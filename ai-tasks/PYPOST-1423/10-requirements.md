# PYPOST-1423: Extract Virtualization Components into Dedicated Modules

## Goals

Maintainers and contributors working on the collection-variable import experience need a
dialog module that stays focused on dialog orchestration. Today the import dialog file
bundles table model, view, delegate, and background-fetch worker concerns in one place
(~1,300 lines), which slows review, raises merge conflict risk, and makes it harder to
reuse or unit-test virtualization pieces independently.

This task extracts those virtualization components into dedicated UI modules so the
dialog stays a thin coordinator, the package layout matches existing UI conventions
(models / delegates / views / workers), and the dialog module is reduced toward the
maintainability target of under 500 lines.

Related origin: `ai-tasks/PYPOST-1415/60-tech-debt.md` follow-up #1.

## Implementation Language

- **Implementation language**: Python

## User Stories

- As a **PyPost UI maintainer**, I want virtualization components (model, view, delegate,
  fetch worker) in dedicated modules so I can change table behavior without wading through
  dialog layout and import orchestration code.
- As a **contributor reviewing import-dialog changes**, I want the dialog file under a
  clear size budget so diffs stay reviewable and conflicts stay localized.
- As a **QA / test author**, I want existing import-dialog and virtualization tests to keep
  passing with the same observable behavior after the extract (including
  backward-compatible import paths where callers already import symbols from the dialog
  module).

## Definition of Done

1. `CollectionVariablesTableModel` lives under `pypost/ui/models/`.
2. `ConflictStrategyDelegate` lives under `pypost/ui/delegates/`.
3. `CollectionVariablesTableView` lives under `pypost/ui/views/`.
4. `CollectionFetchWorker` lives under `pypost/ui/workers/`.
5. `pypost/ui/dialogs/import_collection_variables_dialog.py` is under 500 lines of code,
   **or** (minimum gate) the four classes above are defined in their target modules and
   the dialog imports them rather than defining them inline.
6. Existing import-dialog / virtualization / related UI tests remain green; public import
   surfaces used by tests keep working (re-exports from the dialog module are allowed).
7. No intentional behavior change to import UX, masking, strategies, or fetch/cancel
   semantics.

## Task Description

**Problem:** The virtualization work from PYPOST-1415 landed inside a single dialog module,
creating a monolithic file that mixes presentation, Qt model/view/delegate plumbing, and
background I/O.

**Outcome:** Same user-facing import dialog behavior, with clear module boundaries and a
smaller dialog file that is easier to maintain.

**Out of scope:** Asynchronous connection/manifest discovery, socket-level abort,
paged/chunked models for 50k+ rows, and new fault-injection suites (already ticketed
separately under PYPOST-1424–1427).

## Q&A

- **Q:** Why extract rather than only document the monolith?
  **A:** Reviewability and reuse; the debt item explicitly targets dedicated packages and
  a dialog LOC budget.
- **Q:** May the dialog re-export extracted symbols?
  **A:** Yes — keeping `from pypost.ui.dialogs.import_collection_variables_dialog import …`
  working is required for existing tests and callers.
