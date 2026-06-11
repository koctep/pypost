# PYPOST-321: Save-As Original Request ID Regression Test

## Goals

Protect the Save As... workflow introduced in PYPOST-34: duplicating a request must always create
a new persisted entity. A regression that reuses the source request ID would silently overwrite the
original request and risk data loss.

## User Stories

- As a **PyPost user**, when I **Save As...** a request, I want the **original request to remain
  unchanged** in my collection, so I do not lose the source copy.
- As a **developer**, I want an **automated regression test** for save-as identity behavior, so
  future refactors cannot reintroduce overwrite-by-ID bugs.

## Definition of Done

- A unit test fails if save-as persists data under the source request ID.
- The test verifies the source request remains discoverable by its original ID after save-as.
- The test verifies persistence receives a new request ID distinct from the source.
- All existing tests pass.
- Developer documentation references the regression coverage.

## Task Description

Follow-up from PYPOST-34 technical debt (`ai-tasks/PYPOST-34/60-tech-debt.md`). Complements
PYPOST-317 save-as coverage by focusing specifically on the invariant that the original request ID
is never overwritten during save-as.

### In Scope

- Regression test in the tabs presenter test suite.
- Workflow artifacts and brief dev-doc note.

### Out of Scope

- Changing save-as production logic (already correct).
- Full GUI end-to-end save-as tests (PYPOST-320).

### Constraints and Assumptions

- Save-as orchestration lives in `TabsPresenter._handle_save_as_request`.
- `RequestManager` is the persistence boundary under test (via test doubles).

## Q&A

| Question | Answer |
| -------- | ------ |
| Why not only test the emitted signal? | Signal checks alone do not prove the source entity was not overwritten at the manager layer. |
| Relation to PYPOST-317? | PYPOST-317 covers broader save-as behavior; this task locks the ID immutability invariant. |
