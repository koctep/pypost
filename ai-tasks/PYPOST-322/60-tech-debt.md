# PYPOST-322: Technical Debt Analysis

## Shortcuts Taken

- None for this extraction; behavior preserved one-to-one.

## Code Quality Issues

- **Presenter still owns stale-tab resolution UI** (NON-BLOCKER): `_offer_stale_tab_resolution`
  remains in `TabsPresenter` because it is sibling-tab UX, not save orchestration.
- **Orchestrator uses Qt parent widget** (NON-BLOCKER): Dialogs require a QWidget parent; a
  future port could inject dialog factories for headless testing.

## Missing Tests

- **GUI end-to-end save flows** (NON-BLOCKER): Covered by follow-up PYPOST-320.

## Performance Concerns

- None introduced.

## Follow-up Tasks

- Add GUI-level tests for save and save-as behavior (happy path and cancel path).
  — [PYPOST-320](https://pypost.atlassian.net/browse/PYPOST-320)
- Plan repository-wide lint debt reduction.
  — [PYPOST-323](https://pypost.atlassian.net/browse/PYPOST-323)

## Blocker Review Verdict

**SAFE TO CLOSE** — extraction complete, tests pass, no acceptance-criteria blockers.
