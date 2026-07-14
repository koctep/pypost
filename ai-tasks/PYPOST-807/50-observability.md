# PYPOST-807: Observability

## Scope

Pytest configuration relocation — no application logging or metrics changes.

## Existing observability preserved

| Signal | Source | Notes |
| --- | --- | --- |
| Local live logs | `log_cli = true`, `WARNING` in `pyproject.toml` | Unchanged values |
| CI log capture | `test.yml` `-o log_cli=false --log-file=pytest.log` | Unchanged |
| Guardrail script | `verify_test_log_guardrails.py` on `pytest.log` | Unchanged |
| Coverage gate | `--cov-fail-under=70` in `addopts` | Unchanged |
| CI summary threshold | `THRESHOLD=70` in `test.yml` | Manual mirror of `addopts` |

## N/A

- Application request/MCP/metrics logging — not affected by this task.
