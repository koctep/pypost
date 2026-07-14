# PYPOST-779: Observability

## Scope

Dependency lock adoption is build/CI infrastructure — no runtime logging or metrics changes.

## Existing observability preserved

- `make security-audit` / CI `pip-audit` job scans the locked `requirements.txt` graph.
- CI job summaries unchanged; dependency install steps remain visible in workflow logs.
- No new application log lines or Prometheus metrics.

## Operational visibility

| Signal | Where |
| --- | --- |
| Lock drift | `make check-lock` exit code (local/optional CI) |
| CVE findings | `security-audit` job (unchanged) |
| Cache miss | GitHub Actions `setup-python` cache log when lock files change |

## N/A

- Application request/MCP/metrics logging — not affected by this task.
