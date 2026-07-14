# PYPOST-811: Dev Docs Summary

## Updated files

No `doc/dev/` edits required — behavior is an internal import guard on an already-documented
optional OTel backend (`doc/dev/testability.md`, `doc/dev/mcp_integration.md`).

## Key behavior change

| Before (PYPOST-787) | After (PYPOST-811) |
| --- | --- |
| `import pypost.core.metrics_otel` fails without OTel overlay | Import succeeds; tracker construction requires OTel |

Install guidance in error message: `pip install -e '.[otel]'` or `make venv-otel`.

## Cross-links

- Parent deferral: `ai-tasks/PYPOST-787/60-tech-debt.md` (Lazy-import metrics_otel)
- OTel overlay architecture: `ai-tasks/PYPOST-787/20-architecture.md`
- Optional import pattern: `pypost/core/environment_secrets_codec.py`

## Worklog

role: execution, steps: 1-7, step_name: PYPOST-811 end-to-end, tokens_used: 42000
