# PYPOST-317: Automated Tests for Save As Behavior

## Goals

Close the PYPOST-34 technical-debt gap: save-as must be guarded by automated tests so regressions
in new-entity creation, source immutability, and post-save tab identity are caught in CI.

## User Stories

- As a **developer**, I want **orchestrator-level save-as tests with mocked dialogs**, so save
  flows can be verified without GUI interaction.
- As a **maintainer**, I want **coverage for cancel and failure paths**, so dismissed dialogs and
  missing targets do not silently persist data.

## Definition of Done

- `RequestSaveOrchestrator.save_as_request` has automated tests for:
  - new request ID and name from dialog
  - dialog cancel (no persistence)
  - missing target collection (no persistence)
  - new collection creation via dialog
  - expanded-collection state update
  - source request immutability in `RequestManager`
- Existing presenter save-as tests remain passing.
- Developer docs list save-as test locations and focused run command.

## Task Description

### Problem Statement

Save As was added in PYPOST-34 without orchestrator-level test coverage. Regressions could
overwrite the source entity, skip collection expansion, or persist on cancel.

### Programming Language

Python

### Functional Requirements

- Tests mock `SaveRequestDialog` and drive `RequestSaveOrchestrator.save_as_request`.
- Happy path asserts new ID, dialog name, collection ID, and persistence call.
- Cancel path asserts `SaveAction.CANCELLED` and zero `save_request` calls.
- Source immutability asserts the original ID remains registered unchanged on disk.

### Non-Functional Requirements

- Tests run headlessly with explicit per-module timeout (pytest).
- No production behavior changes unless a test reveals a defect.

### Constraints and Assumptions

- Orchestrator tests complement existing presenter tests (tab rebinding, signals).
- Full GUI end-to-end flows remain out of scope ([PYPOST-320](https://pypost.atlassian.net/browse/PYPOST-320)).

### System Boundaries (Scope)

- In scope: `tests/test_request_save_orchestrator.py`, dev docs for save-as testing.
- Out of scope: production save-as logic changes, live dialog interaction, metrics changes.

### Main Entities and Interactions

- **RequestSaveOrchestrator** — coordinates save-as dialog and persistence.
- **SaveRequestDialog (mocked)** — supplies collection and name without UI.
- **RequestManager (fake)** — records persistence and lookup for assertions.

## Q&A

| Question | Answer |
| -------- | ------ |
| Why orchestrator-level? | Dialog and persistence logic live in `RequestSaveOrchestrator`; fast, precise coverage. |
| Relation to PYPOST-321? | PYPOST-321 guards presenter/tab ID rebinding; this task covers orchestrator flows broadly. |
