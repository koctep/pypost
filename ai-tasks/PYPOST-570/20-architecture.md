# PYPOST-570: Architecture

## Current configuration

```ini
# pytest.ini
log_cli = true
log_cli_level = WARNING
log_format = %(asctime)s %(levelname)-8s %(name)s: %(message)s
log_date_format = %H:%M:%S
```

| Invocation | Reads pytest.ini? | Live WARNING+ logs? |
| --- | --- | --- |
| `make test` | Yes | Yes |
| `make test-cov` | Yes | Yes |
| CI `python -m pytest tests/ ...` | Yes (repo checkout) | Yes |
| Focused `pytest path::test` | Yes | Yes |

CLI overrides (`-o log_cli=false`, `--log-cli-level=ERROR`) take precedence over `pytest.ini`.

## Noise data flow

```
pytest.ini (log_cli=true, level=WARNING)
        │
        ▼
Application loggers during test execution
        │
        ▼
Live stdout (210 lines on green run — PYPOST-567)
        │
        ├── make test / CI log review (noisy)
        └── inventory.csv classification (expected / suspicious / unknown)
```

## Option landscape

| Option | Mechanism | Scope |
| --- | --- | --- |
| A. Keep as-is | No change | All invocations noisy |
| B. CI-only disable | `-o log_cli=false` in `test.yml` | CI quiet; local unchanged |
| C. Raise level to ERROR | `log_cli_level = ERROR` | Drops 138 WARNING; 72 ERROR remain |
| D. Disable globally | `log_cli = false` | Quiet everywhere; lose local live logs |
| E. Per-test `caplog` | Replace global CLI with assertions | 126+ tests; high effort |
| F. Post-run guardrail | PYPOST-571 allowlist on captured log | CI can stay quiet + fail on surprise ERROR |
| G. Log-on-failure only | Custom hook / plugin | Not in pytest core; new dependency or hook |

## Recommendation architecture (hybrid)

```
pytest.ini          → keep log_cli=true, WARNING (local default)
test.yml            → add -o log_cli=false (CI quiet green runs)
PYPOST-571          → allowlist + fail on unexpected ERROR in CI artifact
optional follow-up  → caplog on medium-risk tests (PYPOST-568)
```

## Outputs for downstream tasks

- **PYPOST-571:** Scan CI log or junit adjunct; allowlist 163 expected patterns from inventory.
- **CI follow-up (optional ticket):** Add `-o log_cli=false` to `.github/workflows/test.yml`.
- **Local verbose:** Document `pytest -o log_cli=true -o log_cli_level=DEBUG` for deep dives.
