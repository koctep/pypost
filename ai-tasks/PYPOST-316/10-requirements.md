# PYPOST-316: Extract Save/Save-As Orchestration from MainWindow

## Goals

Save and save-as workflows involve dialogs, confirmations, persistence, and UI refresh. When
these concerns live in `MainWindow`, the class becomes harder to test and evolve. This task
reduces that concentration so the main window focuses on layout and cross-presenter wiring.

## User Stories

- As a **developer**, I want save orchestration outside `MainWindow`, so I can unit test
  persistence decisions without constructing the full application shell.
- As a **maintainer**, I want a single extension point for save features, so future changes
  do not require editing a large window class.

## Definition of Done

- Save and save-as orchestration (dialogs, confirmations, persistence) live outside
  `MainWindow` in a dedicated component.
- `MainWindow` retains only composition-root signal wiring (e.g. collections refresh on save).
- Tab-specific UI updates remain in `TabsPresenter`.
- Existing save/save-as behavior and tests pass unchanged.

## Task Description

Follow-up from PYPOST-34 technical debt (`ai-tasks/PYPOST-34/60-tech-debt.md`). Save flows
were previously controller-heavy in `MainWindow`; extraction scope is limited to save/save-as
without a broader MainWindow refactor.

### In Scope

- Confirm or complete extraction to a dedicated save orchestrator module.
- Ensure `TabsPresenter` delegates persistence to the orchestrator.
- Verify `MainWindow` has no save handler methods.
- Workflow artifacts and dev-doc verification.

### Out of Scope

- Changing save/save-as user-visible behavior.
- Extracting other MainWindow responsibilities (settings, env, collections).
- Full GUI end-to-end tests (PYPOST-320).
- Repository-wide lint debt (PYPOST-323).

### Constraints and Assumptions

- `RequestManager` remains the persistence boundary.
- Qt dialogs stay in the UI layer.
- Implementation may already exist via PYPOST-322; this task closes the PYPOST-34 debt item.

## Q&A

| Question | Answer |
| -------- | ------ |
| Why not move orchestration to `core/`? | Dialogs and QMessageBox are Qt UI concerns; module lives under `pypost/ui/`. |
| Does MainWindow change for collections refresh? | No — wiring `request_saved` to tree refresh is appropriate composition-root duty. |
| Relation to PYPOST-322? | PYPOST-322 implemented the extraction; PYPOST-316 verifies and closes the debt. |
