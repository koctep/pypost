# PYPOST-322: Extract Save Orchestration from MainWindow

## Goals

Save and save-as workflows coordinate dialogs, confirmations, persistence, and UI refresh.
Concentrating that logic in a large window/presenter class makes the code harder to test and
evolve. This task isolates save orchestration so tab/window layers focus on layout and signals.

## User Stories

- As a **developer**, I want save orchestration in a dedicated component, so I can unit test
  persistence decisions without wiring the full tab widget.
- As a **maintainer**, I want `TabsPresenter` to delegate save flows, so future save features
  have a single extension point.

## Definition of Done

- Save and save-as orchestration live outside `TabsPresenter` handler bodies in a dedicated
  service/controller module.
- `TabsPresenter` retains only tab-specific UI updates (labels, baselines, signals).
- Existing save/save-as behavior and tests pass unchanged.
- Developer documentation describes the new component.

## Task Description

Follow-up from PYPOST-34 technical debt (`ai-tasks/PYPOST-34/60-tech-debt.md`). Save flows
were previously noted in `MainWindow`; they now run in `TabsPresenter` and should be extracted
further.

### In Scope

- New save orchestrator module.
- Refactor presenter to delegate.
- Unit tests for orchestrator.
- Workflow artifacts and dev-doc update.

### Out of Scope

- Changing save/save-as user-visible behavior.
- Full GUI end-to-end tests (PYPOST-320).
- Repository-wide lint debt (PYPOST-323).

### Constraints and Assumptions

- `RequestManager` remains the persistence boundary.
- Qt dialogs (`SaveRequestDialog`, `QMessageBox`) stay in the UI layer.
- Logging and metrics for save flows remain at INFO level with existing event names.

## Q&A

| Question | Answer |
| -------- | ------ |
| Why not move orchestration to `core/`? | Dialogs and QMessageBox are Qt UI concerns; module lives under `pypost/ui/`. |
| Does MainWindow change? | No — it already delegates tabs to `TabsPresenter`. |
