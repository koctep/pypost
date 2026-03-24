# PYPOST-34: Technical Debt Analysis


## Shortcuts Taken

- Reused existing `SaveRequestDialog` for the save-as flow to minimize UI surface changes.
  — [PYPOST-314](https://pypost.atlassian.net/browse/PYPOST-314)

## Code Quality Issues

- **Noisy global flake8 baseline** ([PYPOST-315](https://pypost.atlassian.net/browse/PYPOST-315)):
  Many unrelated files still fail flake8, which weakens lint as a strict quality gate.
- **Save flows in MainWindow** ([PYPOST-316](https://pypost.atlassian.net/browse/PYPOST-316)):
  Save and save-as flows remain concentrated in one large class.

## Missing Tests

- **Save As behavior untested** ([PYPOST-317](https://pypost.atlassian.net/browse/PYPOST-317)):
  - new entity ID creation
  - source request immutability after save-as
  - correct tab rebinding to the newly created request
- Test suite currently has zero collected tests in this repository context.
  — [PYPOST-318](https://pypost.atlassian.net/browse/PYPOST-318)

## Performance Concerns

- **Save As reloads full tree** ([PYPOST-319](https://pypost.atlassian.net/browse/PYPOST-319)):
  Full collections reload and tree restore are acceptable at current scale but may lag with very
  large collection sets.

## Follow-up Tasks

- Add GUI-level tests for save and save-as behavior (happy path and cancel path).
  — [PYPOST-320](https://pypost.atlassian.net/browse/PYPOST-320)
- Add regression test ensuring save-as never overwrites original request ID.
  — [PYPOST-321](https://pypost.atlassian.net/browse/PYPOST-321)
- Consider extracting save orchestration from `MainWindow` into a dedicated service/controller.
  — [PYPOST-322](https://pypost.atlassian.net/browse/PYPOST-322)
- Plan a separate repository-wide lint debt reduction task to restore useful global lint gates.
  — [PYPOST-323](https://pypost.atlassian.net/browse/PYPOST-323)
