# PYPOST-671: Observability

## CI stdout (before vs after)

| Surface | Before | After |
| --- | --- | --- |
| GitHub Actions log | ~210 app WARNING/ERROR lines + pytest progress | Pytest progress, coverage, durations only |
| `pytest.log` | Tee of stdout (mixed pytest + app logs) | App logs only (`--log-file-level=WARNING`) |
| `pytest-output.txt` | N/A | Tee of pytest stdout for duration audit |

## Unchanged guardrails

| Step | Input | Behavior |
| --- | --- | --- |
| Verify test log guardrails | `pytest.log` | Fails on unlisted ERROR or count > 77 |
| Audit test duration budgets | `pytest-output.txt` | Warns at 80%, fails at 95% of timeout |

Disabling `log_cli` does not weaken ERROR detection — the verifier reads `--log-file` output,
not live stdout.

## Local behavior

`make test` still prints live WARNING+ logs (`log_cli = true` in `pytest.ini`). Developers
who want CI-quiet runs locally:

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/ -o log_cli=false
```
