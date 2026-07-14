# PYPOST-806: Observability

## Scope

Makefile and CI install wiring — no runtime logging or metrics changes.

## Existing observability preserved

- CI job names and failure semantics unchanged.
- `security-audit` job summary still documents production CVE scan on `requirements.txt`.
- `make security-audit` exit code remains non-zero when vulnerabilities are found.

## Operational visibility

| Signal | Where |
| --- | --- |
| Install failures | `make install` / CI pip step stdout/stderr |
| CVE findings | `pip-audit` stdout/stderr in CI job log or local terminal |
| Lock drift | Existing `check-lock-dev` CI job (PYPOST-804) |

## N/A

- Application request/MCP/metrics logging — not affected by this task.
