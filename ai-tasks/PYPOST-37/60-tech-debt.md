# PYPOST-37: Technical Debt Analysis

## Shortcuts Taken

- Reused existing `SaveRequestDialog` for the save-as flow to minimize UI surface changes.

## Code Quality Issues

- Repository-wide flake8 baseline remains noisy across many files unrelated to this task,
  reducing value of global lint as a strict quality gate.
- `MainWindow` continues to aggregate multiple UI orchestration responsibilities; save and save-as
  flows are still controller-heavy in one class.

## Missing Tests

- No automated tests currently verify the `Save As...` behavior:
  - new entity ID creation
  - source request immutability after save-as
  - correct tab rebinding to the newly created request
- Test suite currently has zero collected tests in this repository context.

## Performance Concerns

- `Save As...` triggers full collections reload and tree restore; acceptable for current scale but
  may become noticeable with large collection sets.

## Follow-up Tasks

- Add GUI-level tests for save and save-as behavior (happy path and cancel path).
- Add regression test ensuring save-as never overwrites original request ID.
- Consider extracting save orchestration from `MainWindow` into a dedicated service/controller.
- Plan a separate repository-wide lint debt reduction task to restore useful global lint gates.
