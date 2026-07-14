# PYPOST-804: Observability

## Scope

CI lock verification is build infrastructure — no runtime logging or metrics changes.

## Existing observability preserved

- CI job summaries unchanged for pytest matrix and `security-audit`.
- No new application log lines or Prometheus metrics.

## Operational visibility

| Signal | Where |
| --- | --- |
| Dev lock drift | `check-lock-dev` job exit code + step summary in GitHub Actions |
| Compile failure | `make check-lock-dev` step log (uv output) |
| Local parity | `make check-lock-dev` (same command as CI) |

## N/A

- Application request/MCP/metrics logging — not affected by this task.
