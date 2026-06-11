# PYPOST-320: Code Cleanup

## Lint and Format

- Test-only diff; no production code changes.
- Module uses shared helpers from `tests/test_request_save_orchestrator.py` and
  `tests/test_tabs_presenter.py` to avoid duplication.

## Review Checklist

- [x] Explicit `pytestmark = pytest.mark.timeout(120)` on integration module.
- [x] Test names describe GUI entry point and expected outcome.
- [x] Reuses existing fake managers and dialog mock pattern.
- [x] No overlap with orchestrator-only tests (different entry layer).
