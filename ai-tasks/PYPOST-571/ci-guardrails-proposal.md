# CI guardrails proposal (PYPOST-571)

Proposal for enforceable CI guardrails after epic analysis tasks. **Analysis only** — no
implementation in PYPOST-571.

## Executive summary

| Guardrail | Recommendation | Phase | Effort |
| --- | --- | --- | --- |
| **Log allowlist** | YAML allowlist + count ceilings from PYPOST-567 baseline | 1 | **M** (1–2 d) |
| **`caplog` contract** | Document + enforce on new error-path tests; optional retrofits | 1–2 | **S** (0.5 d doc) + **S** (1 d tests) |
| **Duration budget** | Post-run audit: warn >80%, fail >95% of timeout marker | 2 | **M** (1–2 d) |
| **Post-run script** | `verify_test_log_guardrails.py` after pytest in CI | 1 | **M** (included in allowlist row) |

**Chosen bundle:** Post-run log verifier with allowlist (phase 1) + duration audit (phase 2) +
`caplog` contract in contributor docs. Keep `log_cli` enabled until PYPOST-570 recommends
otherwise — the verifier needs live-log lines.

---

## 1. Log allowlist

### Problem

Baseline capture (`tests.txt`, PYPOST-567): **72 ERROR**, **138 WARNING** during 937 passed.
Most ERROR lines are intentional error-path side effects (retry exhaustion, encryption
verify failures, delete errors). CI must **fail on new unlisted ERROR patterns** while
permitting the known set.

### Design

**File:** `tests/expected_log_allowlist.yaml`

```yaml
# Baseline: PYPOST-567 inventory (2026-06-11). Update when adding error-path tests.
version: 1
global:
  max_error_lines: 80      # baseline 72 + 10% slack
  max_warning_lines: 160   # baseline 138 + ~15% slack
entries:
  - logger: pypost.core.request_service
    prefix: request_execution_failed
    max_count: 20
    inventory_ref: PYPOST-567
  - logger: pypost.core.key_provider
    prefix: encryption_key_rotation_lookup_failed
    max_count: 10
    note: expected in rotation/migration tests; suspicious if count spikes
  # ... full list in implementation ticket
```

### ERROR prefixes to allow (baseline 72 lines)

| Prefix | Logger(s) | Baseline count | Tag (PYPOST-567) |
| --- | --- | ---: | --- |
| `request_execution_failed` | `pypost.core.request_service` | 13 | expected |
| `encryption_key_rotation_lookup_failed` | `pypost.core.key_provider` | 8 | suspicious* |
| `env_value_decrypt_failed` | `pypost.core.environment_secrets_codec` | 5 | suspicious* |
| `load_environments_failed` | `pypost.core.storage` | 4 | expected |
| `encryption_migration_missing_kids` | `pypost.core.encryption_migration` | 2 | expected |
| `encryption_migration_data_quality_errors` | `pypost.core.encryption_migration` | 2 | expected |
| `Connection failed:` | `pypost.core.http_client` | 2 | unknown* |
| `request_error` | `pypost.ui.presenters.tabs_presenter` | 2 | expected |
| `collection_item_delete_failed` | `pypost.ui.presenters.collection_tree_actions` | 3 | expected |
| `encryption_migration_decrypt_failed` | `pypost.core.encryption_migration` | 1 | expected |
| `storage_save_failed` | `pypost.ui.presenters.env_presenter` | 1 | unknown |
| `environment_storage_worker_load_failed` | `pypost.core.environment_storage_worker` | 1 | suspicious* |
| `environment_storage_worker_save_failed` | `pypost.core.environment_storage_worker` | 1 | suspicious* |
| `yaml_to_json_conversion_failed` | `pypost.core.http_client` | 1 | expected |
| `Request failed:` | `pypost.core.http_client` | 1 | unknown* |
| `Request timed out:` | `pypost.core.http_client` | 1 | expected |
| `mcp_operation_failed` | `pypost.core.mcp_client_service` | 1 | expected |
| `RequestWorker unexpected error` | `pypost.core.worker` | 1 | expected |
| `encryption_key_unavailable` | `pypost.core.key_provider` | 1 | suspicious* |
| `asyncio` / pending task | `asyncio` | 1 | unknown* |

\*Allowlisted in phase 1 with `max_count` tied to baseline; flagged for PYPOST-570/568
follow-up to migrate to structured events or `caplog` assertions.

### WARNING handling

Phase 1: **count ceiling only** (global 160). Phase 2: optional per-prefix allowlist for
high-volume groups (`alert_emitted`, `template_render_fallback_to_original`, `retryable_*`).

### Maintenance rules

1. New error-path test that emits a new prefix → add allowlist entry in the same PR.
2. Count exceeds `max_count` → CI fails; bump `max_count` only with justification in PR.
3. Quarterly: regenerate inventory (`make test > tests.txt`; parser) and diff against YAML.

---

## 2. `caplog` contract

### Problem

PYPOST-568: error-path tests assert Qt signals, metrics, or dialog mocks — not log lines.
That is **safe** (no high-risk false positives) but allows identical ERROR text in CI logs for
passing and failing runs. The contract makes log expectations explicit for new work.

### Rules (for `doc/dev/testing.md` and `.cursor/lsr/do-testing.md`)

| # | Rule |
| --- | --- |
| C1 | If a test's **primary assertion** is log content, use `caplog.at_level(...)` or `assertLogs`. |
| C2 | If a test simulates a failure path and ERROR is a **documented side effect**, either assert exactly one matching record under `caplog` **or** ensure the message prefix is in `expected_log_allowlist.yaml`. |
| C3 | Prefer **behavioral assertions first** (signal, metric, exception type); caplog is additive. |
| C4 | Never use raw log grep in pass/fail criteria without caplog — post-run script is CI-only. |
| C5 | Log tests must not leak secrets; follow existing env-dialog caplog patterns (PYPOST-448). |

### Retrofit candidates (optional, phase 2)

From PYPOST-568:

| Test | Change | Effort |
| --- | --- | --- |
| `test_worker_wraps_unexpected_exception_as_execution_error_unknown` | `caplog.at_level(ERROR)` + assert 1 `RequestWorker unexpected error` | S |
| `test_execution_error_timeout_shows_timeout_message` | Add `assert_called_once()` on dialog mock | S |

### Rejected: mandatory caplog on all 72 ERROR lines

Too much churn for phase 1; allowlist covers CI gate; caplog retrofits are optional hygiene.

---

## 3. Duration budget

### Problem (PYPOST-569)

Tests that consume nearly 100% of their `pytest.mark.timeout` budget may pass while hiding
unbounded waits or polling loops. Epic scope: flag duration **>80%** of marker.

### Current state (2026-06-11 probe)

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/ -q \
  --durations=25 --durations-min=5
```

Result: **no test ≥5 s**; full suite **~45–48 s**. No immediate offenders at the 5 s floor.

### Proposed enforcement

**Script:** `scripts/audit_test_durations.py` (phase 2)

1. Run pytest with `--durations=0 --durations-min=0.5` (or parse JUnit `time` attribute).
2. For each test, read closest `pytest.mark.timeout(N)` from AST or `pytest --markers` cache.
3. Compute `ratio = duration / N`.
4. Emit GitHub Actions annotations:
   - `ratio > 0.80` → **warning** (`::warning::`)
   - `ratio > 0.95` → **failure** (exit 1)
5. Upload report artifact for trend tracking.

### CI placement

After pytest, before log verifier. Does not block phase 1 rollout (no current offenders).

### Rejected: lowering all timeout markers globally

Risk of flaky failures on loaded CI runners; ratio-based gate is more precise.

---

## 4. Post-run script

### Problem

Pytest exit code 0 does not inspect application log lines. Need a deterministic offline check
aligned with PYPOST-567 parser investment.

### Proposed script

**File:** `scripts/verify_test_log_guardrails.py`

Extends `scripts/parse_test_log_inventory.py`:

```bash
# Local
make test 2>&1 | tee tests.txt
.venv/bin/python scripts/verify_test_log_guardrails.py tests.txt \
  --allowlist tests/expected_log_allowlist.yaml

# CI (.github/workflows/test.yml)
python -m pytest tests/ ... 2>&1 | tee pytest.log
python scripts/verify_test_log_guardrails.py pytest.log \
  --allowlist tests/expected_log_allowlist.yaml
```

### Behaviour

| Check | On failure |
| --- | --- |
| Parse live-log lines matching `LOG_RE` from PYPOST-567 parser | Exit 2 (parse error) |
| ERROR line not matching any `(logger, prefix)` allowlist entry | Exit 1; print test node id + message |
| ERROR count > `global.max_error_lines` | Exit 1 |
| WARNING count > `global.max_warning_lines` | Exit 1 (phase 1); warn-only option `--warnings=annotate` |
| Unlisted ERROR from **suspicious** inventory tag | Exit 1 with `suspicious` hint |

### Exit codes

| Code | Meaning |
| --- | --- |
| 0 | All guardrails passed |
| 1 | Policy violation (unlisted ERROR, count ceiling, duration ratio) |
| 2 | Input/log format error |

### CI workflow change (implementation ticket)

```yaml
- name: Run tests
  run: |
    python -m pytest tests/ -v --tb=short --cov=pypost \
      --cov-report=term-missing --cov-report=xml:coverage.xml \
      --junit-xml=junit.xml 2>&1 | tee pytest.log

- name: Verify test log guardrails
  if: success()
  run: |
    python scripts/verify_test_log_guardrails.py pytest.log \
      --allowlist tests/expected_log_allowlist.yaml
```

### Rejected alternatives

| Alternative | Verdict |
| --- | --- |
| **Strict pytest warnings / custom logging hook** | Defer — fights Starlette deprecation and duplicates offline parser |
| **Fail on any ERROR** | Reject — breaks on baseline 72 lines |
| **Disable `log_cli` in CI** | Defer to PYPOST-570 — verifier needs log lines; can combine later |
| **Third-party pytest-log-fail plugin** | Reject — less control over allowlist/count semantics |

---

## Implementation roadmap

| Ticket | Scope | Effort | Depends on |
| --- | --- | --- | --- |
| [PYPOST-572](https://pypost.atlassian.net/browse/PYPOST-572) | `expected_log_allowlist.yaml` + `verify_test_log_guardrails.py` + CI step | **M** (1–2 d) | PYPOST-571 |
| [PYPOST-573](https://pypost.atlassian.net/browse/PYPOST-573) | `audit_test_durations.py` + CI warn/fail annotations | **M** (1–2 d) | PYPOST-569 final list |
| [PYPOST-574](https://pypost.atlassian.net/browse/PYPOST-574) | `caplog` contract in `do-testing.md` + 2 retrofit tests | **S** (1 d) | PYPOST-568 |
| PYPOST-570 | `log_cli` keep vs CI-only override recommendation | **S** | Independent |

**Total implementation estimate:** ~4–6 developer-days across three follow-up tickets.

---

## Acceptance mapping

| Jira acceptance criterion | Section |
| --- | --- |
| Proposal with chosen approach | Executive summary + four pillars |
| Rejected alternatives | §1 maintenance, §2 rejected mandatory caplog, §3 rejected global timeouts, §4 rejected table |
| Effort estimate | Implementation roadmap table |
