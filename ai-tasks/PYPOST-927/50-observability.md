# PYPOST-927: Observability

## Scope

CI lock verification is build infrastructure — no runtime logging or metrics changes.

## Existing observability preserved

- CI job summaries unchanged for pytest matrix and other audit jobs.
- No new application log lines or Prometheus metrics.

## Operational visibility

| Signal | Where |
| --- | --- |
| Production lock drift | `check-lock` job exit code + step summary in GitHub Actions |
| Compile failure | `make check-lock` step log (uv output) |
| Local parity | `make check-lock` (same command as CI) |

## N/A

- Application request/MCP/metrics logging — not affected by this task.
