# PYPOST-279: Observability

## Logging and metrics

No new application logging or Prometheus metrics. This task defines a **CI/Makefile exit-code
contract**, not runtime observability.

## Verification signals

| Signal | Where | Expected on zero collection |
| --- | --- | --- |
| pytest stderr | `make test` / CI | `no tests collected`, exit `5` |
| Make stderr | `make test` | `Error 5` (pytest exit forwarded) |
| CI job status | `.github/workflows/test.yml` | Step fails (non-zero shell exit) |

Developers diagnose misconfiguration by running `make test` locally and checking for exit code
`5` or `collected 0 items` in output.
