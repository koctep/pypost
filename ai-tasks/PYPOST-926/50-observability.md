# PYPOST-926: Observability

## Scope

Test-harness change only — no application logging, metrics, or tracing under `pypost/`.

## Signals

| Signal | Location | Notes |
| --- | --- | --- |
| Contract failure | `test_conftest_does_not_import_pyside6_at_module_level` | Subprocess stderr on eager reintroduction |
| qapp regression | `test_qapp_fixture_still_provides_qapplication` | Fails if fixture stops yielding singleton |
| CI | Existing GUI matrix unchanged | Full suite still exercises Qt via test modules |

## Operator notes

- Narrow non-GUI pytest runs no longer fail at conftest import for missing EGL/GL; they
  may still fail if a collected test module imports PySide6 at module level.
- No new log lines or Prometheus metrics introduced.
