# PYPOST-787: Optional OpenTelemetry architecture

## Approach

Extend the **PYPOST-779/780 two-file lock pattern** to OpenTelemetry:

```
requirements-otel.in  ──(uv pip compile)──►  requirements-otel.txt
         ▲                                           │
         │ edit direct pins                         │ pip install -r
         │                                           ▼
    maintainer                         make venv-otel / CI test jobs
```

Production graph (`requirements.in` → `requirements.txt`) no longer includes OTel. The
`pyproject.toml` `[project.optional-dependencies].otel` group mirrors `requirements-otel.in`.

## File roles

| File | Maintainer action | Consumer |
| --- | --- | --- |
| `requirements-otel.in` | Edit direct OTel pins | `make lock-otel` input |
| `requirements-otel.txt` | Regenerate via `make lock-otel` | `make venv-otel`, CI test jobs |
| `pyproject.toml` `[otel]` | Sync with `requirements-otel.in` | `pip install -e ".[otel]"` |

## Makefile targets

| Target | Purpose |
| --- | --- |
| `lock-otel` | Regenerate `requirements-otel.txt` |
| `check-lock-otel` | Fail if OTel lock is stale |
| `venv-otel` | Install OTel overlay into `.venv` |
| `install` | Adds `venv-otel` prerequisite for contributor test parity |
| `test` / `test-cov` | Depend on `venv-otel` for OTel unit tests |

## CI integration

- Main `test` job: install `requirements-otel.txt` after production + dev locks.
- `make-install-smoke`: install OTel overlay before slow Makefile tests.
- `security-audit`: unchanged (production lock only).
- Pip cache keys include `requirements-otel.in` and `requirements-otel.txt`.

## Runtime impact

`pypost/core/metrics_otel.py` still imports OpenTelemetry directly. The module is not loaded by
default app startup; callers opt in when OTel is installed. No lazy-import refactor in this
ticket.
