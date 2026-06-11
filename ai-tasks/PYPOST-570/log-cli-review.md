# pytest log_cli review (PYPOST-570)

## Executive summary

**Recommendation:** **Change config split, not a global disable.**

1. **Keep** `log_cli = true` and `log_cli_level = WARNING` in `pytest.ini` for local `make test`
   (developer ergonomics when debugging failures).
2. **Disable live CLI logging in CI** via `-o log_cli=false` on the pytest command in
   `.github/workflows/test.yml` (eliminates 210 noise lines on green runs).
3. **Implement PYPOST-571** — post-run guardrail with an allowlist derived from PYPOST-567
   inventory (expected ERROR/WARNING patterns) so CI still catches *unexpected* log emissions
   without printing them live on every green run.

Do **not** migrate the full suite to `caplog` now (126 distinct tests, ~210 lines); use targeted
`caplog` only for medium-risk tests identified in PYPOST-568.

---

## 1. Quantified noise (PYPOST-567 baseline)

Source: `make test > tests.txt 2>&1` (2026-06-11), parsed by
`scripts/parse_test_log_inventory.py`.

| Metric | Count |
| --- | ---: |
| Tests passed | 937 |
| Live-log ERROR lines | 72 |
| Live-log WARNING lines | 138 |
| **Total live-log lines** | **210** |
| Distinct tests with ≥1 line | 126 |

### Classification (per inventory classifier)

| Tag | Lines | Share | Meaning |
| --- | ---: | ---: | --- |
| expected | 163 | 78% | Intentional error-path / observability logs |
| suspicious | 21 | 10% | Passing tests; review encryption/key paths |
| unknown | 26 | 12% | Needs manual review or allowlist entry |

### Logger hotspots (top 5)

| Logger | Total | ERROR | WARNING |
| --- | ---: | ---: | ---: |
| `pypost.core.request_service` | 61 | 19 | 42 |
| `pypost.core.template_service` | 39 | 0 | 39 |
| `pypost.core.alert_manager` | 28 | 0 | 28 |
| `pypost.core.encryption_migration` | 12 | 6 | 6 |
| `pypost.core.key_provider` | 12 | 12 | 0 |

### Relationship to PYPOST-568

Error-path audit found **no high-risk false positives** — tests assert signals, dialogs, and
metrics independently of log output. The problem is **visibility**, not **test correctness**.

---

## 2. Option comparison

### A. Keep current config everywhere

| Pros | Cons |
| --- | --- |
| Zero migration | 210 alarming lines every green CI run |
| Local + CI behave identically | `grep ERROR` on CI output is unusable |
| | Blocks meaningful log-based CI gates |

**Verdict:** Reject as long-term state; acceptable only until PYPOST-571 ships.

### B. Disable `log_cli` in CI only (`-o log_cli=false`)

| Pros | Cons |
| --- | --- |
| Verified: suppresses live ERROR on worker test | CI and local behavior diverge |
| No pytest.ini change | Requires PYPOST-571 for regression detection |
| Small diff (one workflow line) | |

**Verdict:** **Recommended** alongside kept local defaults.

```bash
# Verified locally:
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/test_worker.py::... -o log_cli=false
# → 0 live ERROR lines vs 1 with default ini
```

### C. Raise `log_cli_level` to ERROR globally

| Pros | Cons |
| --- | --- |
| Halves noise (drops 138 WARNING) | 72 ERROR lines still alarm on green runs |
| Single ini change | Loses WARNING signal locally without extra flags |

**Verdict:** Insufficient alone; use only if WARNING noise is the sole concern.

### D. Disable `log_cli` globally

| Pros | Cons |
| --- | --- |
| Quiet everywhere | Developers must remember to re-enable for debugging |
| | Loses PYPOST-52 rationale (correlate logs with failing test) |

**Verdict:** Reject; prefer CI-only disable (B).

### E. Per-test `caplog` instead of global CLI

| Pros | Cons |
| --- | --- |
| Asserts log intent explicitly | ~126 tests touch inventory lines |
| Best practice for error-path tests | Large migration; unrelated modules |
| | Does not help discover *new* unexpected logs |

**Verdict:** Optional follow-up for PYPOST-568 medium-risk rows; not a replacement for global
policy.

### F. Fail-on-unexpected-ERROR (plugin or post-processing)

| Pros | Cons |
| --- | --- |
| CI can stay quiet (B) and still gate | Needs allowlist maintenance (PYPOST-571) |
| Inventory provides 163 expected patterns | Custom script or pytest plugin work |
| Aligns with epic PYPOST-566 goals | |

**Verdict:** **Recommended** as phase 2 (PYPOST-571).

### G. `--log-cli-level` override on failure only

| Pros | Cons |
| --- | --- |
| Ideal UX if available | **Not supported** by pytest core `log_cli` |
| | Requires custom `pytest_runtest_makereport` hook or plugin |

**Verdict:** Defer; B + F achieves similar CI outcome with less custom code.

---

## 3. Alignment with `.cursor/lsr/do-testing.md`

Agent testing rules mandate **per-test timeouts** and bounded waits. They do **not** prescribe
live CLI logging. No conflict with disabling CI live logs or keeping local WARNING output.

When agents run `make test`, they still see live WARNING/ERROR locally — useful when a test
fails. CI quiet mode does not affect agent local runs unless they invoke pytest with
`-o log_cli=false`.

---

## 4. Recommendation and migration steps

### Decision

| Setting | Recommendation |
| --- | --- |
| `pytest.ini` `log_cli` | **Keep** `true` |
| `pytest.ini` `log_cli_level` | **Keep** `WARNING` |
| CI workflow | **Change** — add `-o log_cli=false` |
| PYPOST-571 | **Implement** allowlist guardrail |
| Global `caplog` migration | **Defer** |

### Migration steps

**Phase 1 — CI quiet (small follow-up ticket or PYPOST-571 preamble)**

1. Edit `.github/workflows/test.yml` pytest invocation:

   ```yaml
   python -m pytest tests/ -v --tb=short --cov=pypost \
     -o log_cli=false \
     ...
   ```

2. Confirm green CI: no live ERROR/WARNING lines in job log; junit/coverage unchanged.

**Phase 2 — PYPOST-571 guardrail**

1. Re-run `make test > tests.txt` (or capture CI log with logging enabled once for baseline).
2. Seed allowlist from `ai-tasks/PYPOST-567/inventory.csv` expected + reviewed unknown rows.
3. Add CI step: parse log or use pytest plugin; fail build on unlisted ERROR (and optionally
   WARNING).
4. Document allowlist update process in `doc/dev/testing.md`.

**Phase 3 — Optional hardening (low priority)**

1. Add `caplog` to PYPOST-568 medium-risk tests (`test_execution_error_timeout_shows_timeout_message`).
2. Re-classify PYPOST-567 **suspicious** groups (key_provider, environment_secrets_codec).

### Local debugging after CI change

```bash
# Default (ini): live WARNING+
make test

# Explicit verbose logging
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/ -o log_cli=true -o log_cli_level=DEBUG

# Quiet local run (matches CI)
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/ -o log_cli=false
```

---

## 5. What we are not changing in PYPOST-570

This task is analysis-only. `pytest.ini`, `test.yml`, and tests are unchanged here. Implementation
belongs to PYPOST-571 (guardrail) and an optional CI workflow follow-up.
