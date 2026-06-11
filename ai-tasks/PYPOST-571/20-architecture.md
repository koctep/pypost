# PYPOST-571: Architecture

## Approach

Layered **post-run verification** on top of existing pytest success criteria. No pytest plugins
in phase 1 — extend the PYPOST-567 offline parser into a CI gate script. Complement with a
documented `caplog` contract for new error-path tests and a duration audit hook fed by
`--durations` / JUnit timing.

## Guardrail stack

```
make test / CI pytest
        │
        ├─► pytest exit code (existing gate)
        │
        ├─► junit.xml + --durations output
        │         │
        │         ▼
        │   duration budget check (>80% of timeout marker → warn, then fail)
        │
        └─► captured stdout/stderr (tests.txt)
                  │
                  ▼
            verify_test_log_guardrails.py
                  │
                  ├─ parse ERROR/WARNING live-log lines
                  ├─ match against tests/expected_log_allowlist.yaml
                  ├─ enforce count ceilings (baseline + slack)
                  └─ exit 1 on unlisted ERROR or threshold breach
```

## Component map

| Component | Role | Phase |
| --- | --- | --- |
| `tests/expected_log_allowlist.yaml` | Logger + message-prefix allowlist with inventory refs | 1 |
| `scripts/verify_test_log_guardrails.py` | Post-run parser + gate (extends PYPOST-567 parser) | 1 |
| `.github/workflows/test.yml` step | Capture log, run verifier after pytest | 1 |
| `doc/dev/testing.md` + `do-testing.md` | `caplog` contract for error-path tests | 1 |
| `scripts/audit_test_durations.py` | Join `--durations` / JUnit with timeout markers | 2 |
| Optional `caplog` on 2–3 focus tests | Tighten medium-risk rows from PYPOST-568 | 2 |

## Allowlist design

- **Key:** `(logger, message_prefix)` where `message_prefix` is the structured event name
  (first token before `key=value` pairs), e.g. `request_execution_failed`.
- **Source rows:** PYPOST-567 groups tagged **expected**; PYPOST-568 focus-module ERROR rows.
- **Exclude from allowlist (fail if seen):** **suspicious** groups (`encryption_key_unavailable`
  without matching test, raw `Connection failed:` without structured event) until reclassified.
- **Count ceilings:** Per-prefix max count from baseline + 10% slack; global ERROR cap 80
  (baseline 72 + headroom for new tests).

## `caplog` contract (summary)

| Scenario | Requirement |
| --- | --- |
| Test asserts ERROR/WARNING in message text | Must use `caplog.at_level(...)` |
| Test simulates failure path; log is side effect only | Register prefix in allowlist **or** add caplog assertion |
| New error-path test | At least one behavioral assertion **and** allowlist entry or caplog |

## Duration budget (summary)

| Threshold | Action |
| --- | --- |
| duration > 80% of closest `timeout` marker | CI warning annotation |
| duration > 95% of marker | CI failure (flake / unbounded wait) |
| No tests currently ≥5 s | Enable with `--durations-min=1` in audit script |

## Rejected alternatives

| Option | Verdict | Reason |
| --- | --- | --- |
| Fail on any ERROR without allowlist | Reject | 72 baseline ERROR lines; breaks CI until all paths reclassified |
| Disable `log_cli` in CI only | Defer to PYPOST-570 | Reduces noise but removes signal for post-run script; keep both initially |
| pytest plugin / logging hook | Defer | Higher maintenance; offline script matches PYPOST-567 investment |
| `filterwarnings=error` globally | Reject | Starlette deprecation and third-party noise; unrelated to app ERROR |
| Production log level changes | Out of scope | Product decision; guardrails are test/CI side |

## Outputs for implementation follow-ups

See `ci-guardrails-proposal.md` for effort estimates and ticket breakdown.
