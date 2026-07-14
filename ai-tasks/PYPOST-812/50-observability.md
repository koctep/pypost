# PYPOST-812: Observability

## Scope

Verification and documentation task — no runtime logging or metrics changes.

## OTel test coverage preserved

- `tests/test_metrics_otel.py` runs under `make test` after `venv-otel` installs the editable
  `[otel]` extra.
- CI `test` job installs `pip install -e ".[dev,otel]"`, matching local `make install`.

## Operational visibility

| Signal | Where |
| --- | --- |
| OTel install failures | `make venv-otel` / CI pip step stdout/stderr |
| OTel functional regressions | `tests/test_metrics_otel.py` in `make test` |
| OTel pin drift | `tests/test_pyproject.py` vs `requirements-otel.in` |

## N/A

- Application request/MCP/metrics logging — not affected by this task.
