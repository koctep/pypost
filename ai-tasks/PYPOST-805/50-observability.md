# PYPOST-805: Observability

## Scope

Dev lock and CI/Makefile wiring — no runtime logging or metrics changes.

## Existing observability preserved

- CI `security-audit` job name and failure semantics unchanged (PYPOST-778).
- Job summary still documents production CVE scan on `requirements.txt`.
- `make security-audit` exit code remains non-zero when vulnerabilities are found.

## Operational visibility

| Signal | Where |
| --- | --- |
| CVE findings | `pip-audit` stdout/stderr in CI job log or local terminal |
| Scanner version | Pinned in `requirements-dev.txt` (`pip-audit==2.10.1`) |
| Stale dev lock | Existing `check-lock-dev` CI job (PYPOST-804) |

## N/A

- Application request/MCP/metrics logging — not affected by this task.
