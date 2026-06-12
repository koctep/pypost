# PYPOST-686: Observability Implementation

**Task type:** Audit only — no application code changes.

## Logging Implementation

### Added Logs

None. This step documents **test and CI observability** posture.

### Test-run logging configuration

| Setting | `pytest.ini` | CI (`.github/workflows/test.yml`) |
| --- | --- | --- |
| `log_cli` | `true` | `false` (via `-o log_cli=false`) |
| `log_cli_level` | `WARNING` | N/A (file capture instead) |
| Log file | — | `--log-file=pytest.log --log-file-level=WARNING` |
| Format | `%(asctime)s %(levelname)-8s %(name)s: %(message)s` | Same via ini |

**Impact:** Local runs surface WARNING+ to the console (including expected ERROR paths in tests).
CI captures logs to a file for deterministic guardrail parsing without console noise.

## Metrics Implementation

N/A — no new application metrics. Tests **assert on** `MetricsManager` / Prometheus counters in
modules such as `test_request_editor_gui_metrics.py`, `test_mcp_server_impl.py`,
`test_history_masking_metrics.py`.

## Monitoring Integration

### CI guardrail: ERROR log inventory (PYPOST-572)

`scripts/verify_test_log_guardrails.py` runs after a successful pytest job:

1. Parses `pytest.log` via `parse_test_log_inventory.py`
2. Compares ERROR records against `tests/expected_log_allowlist.yaml` (prefix rules + baseline
   count margin)
3. Fails CI on unknown ERROR lines or count regression

**Meta-coverage:** `tests/test_verify_test_log_guardrails.py` (7 tests, 30s timeout).

**Assessment (PASS):** Strong contract for preventing silent ERROR log growth. Aligns with
`do-testing.md` caplog/allowlist rules for **new** error-path tests.

### CI guardrail: duration vs timeout (PYPOST-573)

`scripts/audit_test_durations.py` parses pytest `--durations` output from CI:

| Utilization | Action |
| --- | --- |
| ≥ 80% of declared timeout | Warning annotation |
| ≥ 95% | Fail job |

Resolves per-test timeout from markers via `parse_timeout_audit.py`.

**Meta-coverage:** `tests/test_audit_test_durations.py`.

**Assessment (PASS):** Prevents tests from creeping toward hangs without raising explicit
timeouts.

### caplog contract (`do-testing.md`)

Tests using deliberate ERROR logs should assert via `caplog` or allowlist. Observed `caplog`
usage in:

- `test_env_dialog.py`, `test_env_presenter.py`, `test_env_persistence_e2e.py`
- `test_encryption_migration.py`, `test_settings_*_e2e.py`
- `test_worker.py`, `test_worker_race.py`, `test_settings_dialog.py`
- `test_main_window_alert_reload.py`

**Gap (P3):** Not all modules with ERROR logs in tests use `caplog`; some rely on allowlist
only. Acceptable for legacy paths but new tests should follow C1–C5 from `do-testing.md`.

## Validation Results

- [x] CI observability pipeline documented (log file → guardrails → duration audit)
- [x] No production instrumentation changes required
- [x] Test observability gaps noted for Step 6 follow-ups

## Audit Findings (test observability)

| ID | Severity | Finding |
| --- | --- | --- |
| O-001 | PASS | CI ERROR log guardrails active with allowlist and meta-tests |
| O-002 | PASS | Duration budget audit active with 80/95% thresholds |
| O-003 | P3 | Local `log_cli=true` differs from CI — developers see more WARNING noise |
| O-004 | P3 | MCP integration teardown logs asyncio pending-task ERROR |
| O-005 | P2 | Segfault aborts log capture mid-suite on macOS — no graceful degradation |

## Follow-up

See `60-tech-debt.md` — observability-related items are folded into flaky/CI parity tickets
(R-P1-001, R-P2-005, R-P3-002, R-P3-003).
