# PYPOST-177: Code Cleanup

## Lint / Format

- New test modules follow existing unittest + `pytestmark` conventions.
- Line length within 100 characters.

## Refactoring

- None required — tests only; no production code changes.

## Notes

- `MetricsServer._create_app()` accessed in tests (same pattern as private seams elsewhere).
- `generate_latest` patched at `pypost.core.metrics_server` import site for error-path test.
