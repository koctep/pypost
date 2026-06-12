# PYPOST-671: Architecture

## Problem

`pytest.ini` sets `log_cli = true` and `log_cli_level = WARNING`. CI inherits these defaults,
printing ~210 application log lines on every green run (PYPOST-567 baseline) alongside pytest
progress output.

## Solution: split CLI logging from file logging

```
pytest.ini (log_cli=true, WARNING)     ← unchanged; local default
        │
        ▼
CI pytest command overrides:
  -o log_cli=false                      ← quiet stdout
  --log-file=pytest.log                 ← app logs to file
  --log-file-level=WARNING              ← same level as local CLI
  2>&1 | tee pytest-output.txt          ← pytest progress + durations
        │
        ├── pytest.log → verify_test_log_guardrails.py (PYPOST-572)
        └── pytest-output.txt → audit_test_durations.py (PYPOST-573)
```

| Artifact | Contents | Consumer |
| --- | --- | --- |
| `pytest.log` | Application WARNING+ lines (`HH:MM:SS LEVEL logger: msg`) | `verify_test_log_guardrails.py` |
| `pytest-output.txt` | Pytest stdout: `-v` progress, `--durations`, coverage summary | `audit_test_durations.py` |

## Why not tee alone?

Before PYPOST-671, CI tee'd all stdout to `pytest.log`. Disabling `log_cli` stops application
logs from reaching stdout — and therefore from the tee capture. `--log-file` writes the same
log records pytest would have printed via `log_cli`, keeping the verifier input format unchanged.

## Precedence

`-o log_cli=false` overrides `pytest.ini` for CI only. `make test` and local pytest invocations
are unaffected.

## Related design

Hybrid recommendation from [PYPOST-570](../PYPOST-570/20-architecture.md):

- Local: live logs for debugging.
- CI: quiet stdout + post-run guardrails on captured log file.
