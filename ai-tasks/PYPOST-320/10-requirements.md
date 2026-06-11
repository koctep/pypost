# PYPOST-320: GUI-Level Tests for Save and Save-As Behavior

## Goals

Close the PYPOST-34 technical-debt gap for end-to-end save wiring: automated tests must exercise
GUI entry points on `RequestWidget` through `TabsPresenter`, not only direct handler or
orchestrator calls.

## User Stories

- As a **developer**, I want **integration tests that trigger save from menu and shortcut**, so
  signal wiring regressions are caught in CI.
- As a **maintainer**, I want **happy and cancel paths for both save and save-as**, so dismissed
  dialogs and declined confirmations leave tab state unchanged.

## Definition of Done

- Integration tests drive `RequestWidget` menu/shortcut callbacks connected to `TabsPresenter`.
- Save happy path persists an existing request and emits `request_saved`.
- Save cancel paths cover dialog dismiss (new request) and overwrite decline.
- Save-as happy path persists a copy with a new ID and emits `request_save_as_completed`.
- Save-as cancel path leaves tab identity and persistence unchanged.
- Developer docs list integration test locations and focused run command.

## Task Description

Follow-up from PYPOST-34 (`ai-tasks/PYPOST-34/60-tech-debt.md`). Orchestrator and presenter
handler tests exist (PYPOST-317, PYPOST-321); this task adds GUI-level wiring coverage.

### In Scope

- New integration test module for save/save-as flows.
- Workflow artifacts and dev-doc update.

### Out of Scope

- Production save/save-as behavior changes.
- Live `SaveRequestDialog` interaction or full `MainWindow` e2e tests.
- Collections tree refresh verification (MainWindow layer).

### Constraints and Assumptions

- Dialogs and confirmations remain mocked at the orchestrator boundary.
- Tests run headlessly with explicit pytest timeouts.

## Q&A

| Question | Answer |
| -------- | ------ |
| Why not full MainWindow e2e? | Presenter integration covers widget → orchestrator wiring; tree refresh is separate. |
| Relation to PYPOST-317/321? | Those tasks cover orchestrator and presenter handlers; this task covers GUI entry points. |
