# PYPOST-570: pytest log_cli review

## Current config (`pytest.ini`)

```ini
log_cli = true
log_cli_level = WARNING
log_format = %(asctime)s %(levelname)-8s %(name)s: %(message)s
```

## Effect

- Every test run prints **all WARNING and ERROR** application logs to stdout.
- Baseline green run: **210** such lines (72 ERROR, 138 WARNING) per PYPOST-567.
- Mixes **expected** error-path test output with genuine regressions.
- Developers learn to ignore ERROR lines — undermines log review in CI.

## Options evaluated

| Option | Pros | Cons |
| --- | --- | --- |
| **Keep as-is** | Easy local debugging | CI noise; false alarm fatigue |
| **Disable `log_cli` in CI** | Clean CI output | Less context on failure unless re-run locally |
| **`log_cli_level = ERROR` in CI only** | Drops WARNING noise (138 lines) | Still shows expected ERROR paths |
| **Per-test `caplog`** | Precise assertions | Migration cost across error-path tests |
| **Post-run inventory script (PYPOST-567)** | Detects unknown ERROR spikes | Does not prevent, only audit |

## Recommendation

1. **Local default:** keep `log_cli = true`, `log_cli_level = WARNING` for developer
   visibility.
2. **CI:** add `PYTEST_ADDOPTS=--log-cli-level=ERROR` or disable log_cli in CI workflow
   (when CI exists) — reduces noise by ~66% (drops WARNING-only lines).
3. **Guardrail (PYPOST-571):** post-run allowlist script fails CI on unknown ERROR prefixes.
4. **Do not** remove live logging globally without developer consultation.

## Verdict

**SAFE TO CLOSE** — recommendation documented; implementation deferred to CI/guardrails tasks.
