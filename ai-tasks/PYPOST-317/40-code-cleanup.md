# PYPOST-317: Code Cleanup

## Lint and Format

- Test-only diff; no production code changes.
- Reused `_mock_save_dialog` helper to avoid duplicated mock setup across save-as cases.

## Review Checklist

- [x] Module-level `pytestmark = pytest.mark.timeout(60)` unchanged.
- [x] Test names describe behavior under test.
- [x] Uses existing `FakeRequestManager` / `FakeStateManager` from `test_tabs_presenter.py`.
- [x] No overlap with presenter signal/tab tests beyond orchestrator seam.
