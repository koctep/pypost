# PYPOST-316: Technical Debt Analysis

## Resolution

**Debt item closed.** Save/save-as orchestration was extracted in PYPOST-322 to
`RequestSaveOrchestrator`. `MainWindow` no longer contains save handler logic.

## Shortcuts Taken

- None for this verification task; no new code required.

## Code Quality Issues

- **Presenter still owns stale-tab resolution UI** (NON-BLOCKER, inherited from PYPOST-322):
  `_offer_stale_tab_resolution` in `TabsPresenter` is sibling-tab UX, not save orchestration.
- **Orchestrator uses Qt parent widget** (NON-BLOCKER): Dialogs require QWidget parent.

## Missing Tests

- **GUI end-to-end save flows** (NON-BLOCKER): Follow-up PYPOST-320.
- Unit coverage exists in `tests/test_request_save_orchestrator.py` and save sections of
  `tests/test_tabs_presenter.py`.

## Performance Concerns

- Save-as tree update path tracked separately under PYPOST-319 (NON-BLOCKER).

## Follow-up Tasks

- Add GUI-level tests for save and save-as behavior — [PYPOST-320](https://pypost.atlassian.net/browse/PYPOST-320)
- Repository-wide lint debt — [PYPOST-323](https://pypost.atlassian.net/browse/PYPOST-323)

## Blocker Review Verdict

**SAFE TO CLOSE** — MainWindow save concentration resolved; tests pass; no blockers.
