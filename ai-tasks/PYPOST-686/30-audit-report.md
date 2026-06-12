# PYPOST-686: Test Coverage and Quality Audit Report

**Task:** PYPOST-686 — Audit test coverage and test quality
**Date:** 2026-06-12
**Scope:** `tests/` suite, `pypost/` coverage, timeout compliance, CI guardrails, integration
balance, flaky patterns, maintainability
**Baseline:** `doc/dev/testing.md`, `.cursor/lsr/do-testing.md`, `pytest.ini`, Makefile,
`.github/workflows/test.yml`
**Methodology:** `make test`, batched `pytest --cov=pypost`, `pytest --collect-only`, ripgrep
for timeout markers and wait patterns, module coverage report, manual failure triage. No code
changes.

## Executive Summary

PyPost maintains a **large, mature pytest suite** — **135 test modules**, **1,423 collected test
items** in the fast suite (`-m "not slow"`), with strong conventions: **100% explicit timeout
marker compliance** enforced by `tests/conftest.py`, a **70% line-coverage gate**, and CI
guardrails for ERROR logs and duration budgets.

**Overall line coverage is healthy (~88%)** when the fast suite completes (batched measurement
excluding the segfaulting module). Core business logic (`request_service`, `http_client`,
`encryption`, `template_service`, presenters) generally exceeds 90% coverage.

**Primary risks concentrate in five areas:**

1. **Native instability** — `tests/test_mcp_server_manager.py` can **segfault** during port-busy
   startup tests on macOS Python 3.11, aborting full-suite and `make test-cov` runs locally.
2. **Regression guard drift** — `test_solid_audit_baseline.py` fails because `main_window.py` and
   `template_service.py` exceeded documented LOC caps (3 failures).
3. **Makefile test environment coupling** — 8 `test_makefile.py` failures when system `python3`
   version (3.14) differs from the pytest interpreter (3.11) used to compute marker names.
4. **Low-coverage runtime paths** — `mcp_server.py` (38%), `metrics_server.py` (50%),
   `script_executor.py` (40%), `main.py` (0%), and several UI dialogs (&lt;20%) lack direct tests.
5. **Order-sensitive GUI tests** — `test_style_manager_theme.py` fails in full suite but passes
   in isolation (likely Qt global state pollution).

Findings use **P1** (blocks confidence or merge gates), **P2** (meaningful gap or instability),
**P3** (minor gap or documentation).

---

## Suite Inventory

### Scale (measured 2026-06-12)

| Metric | Value |
| --- | --- |
| Test modules (`tests/test_*.py`) | 135 |
| Test helpers | `tests/helpers/` (3 modules + `collections_tree.py`) |
| Collected items (fast suite) | 1,423 |
| Deselected (`slow`) | 1 |
| Subtests (unittest) | 61+ in full run |
| `make test` runtime (local) | ~89s (when no segfault) |
| Fast suite pass (local macOS 3.11) | 1,408 passed, **15 failed** |

### Category breakdown (by file naming and Qt imports)

| Category | Files | Notes |
| --- | ---: | --- |
| GUI-touching (Qt imports / `qapp`) | 62 | ~46% of files; `QT_QPA_PLATFORM=offscreen` |
| Integration-named | 13 | Live HTTP, MCP, metrics, bind host, Makefile |
| E2E-named (`*_e2e.py`) | 7 | MainWindow + settings + history flows |
| Slow marker (`@pytest.mark.slow`) | 1 | `test_makefile.py` install smoke only |
| Meta / guardrail tests | 5 | Log guardrails, duration audit, exit policy, SOLID caps |

**Balance assessment:** The pyramid is **bottom-heavy with GUI unit tests** and a **solid band of
MCP/metrics integration tests**. True end-to-end GUI flows are present but limited to seven
named e2e modules. Core HTTP and encryption logic is well unit-tested; **server lifecycle
threads** (`MCPServerManager`, `MetricsServer` uvicorn) lean on integration tests that are
partially unstable.

---

## Coverage

### Gate configuration

| Setting | Location | Value |
| --- | --- | --- |
| `--cov-fail-under` | `pytest.ini` `addopts` | **70%** |
| CI display threshold | `.github/workflows/test.yml` | **70%** |
| Documented historical baseline | `pytest.ini` comment | ~86% (PYPOST-565) |
| **Measured (audit)** | Batched `--cov=pypost`, excl. segfault file | **88%** (8,873 stmts, 1,060 miss) |

`make test` does **not** enable coverage; `make test-cov` and CI do. Local `make test-cov`
**aborted with segfault** on macOS during `test_mcp_server_manager.py` in this audit.

### Modules below 70% line coverage (audit measurement)

| Module | Coverage | Risk |
| --- | ---: | --- |
| `pypost/main.py` | 0% | Entry point untested (expected for GUI apps) |
| `pypost/ui/dialogs/mcp_activity_dialog.py` | 17% | Operator MCP log viewer |
| `pypost/ui/dialogs/save_dialog.py` | 17% | Save-as flow UI |
| `pypost/ui/dialogs/mcp_tools_overview_dialog.py` | 18% | MCP tools overview |
| `pypost/ui/delegates/environment_name_delegate.py` | 34% | Env rename delegate |
| `pypost/core/mcp_server.py` | 38% | **MCPServerManager** thread lifecycle |
| `pypost/core/script_executor.py` | 40% | Post-script execution for MCP |
| `pypost/core/metrics_server.py` | 50% | Metrics uvicorn + MCP resource server |
| `pypost/ui/widgets/paste_json_worker.py` | 59% | Background JSON paste worker |
| `pypost/core/encryption_migration_worker.py` | 63% | Qt worker for migration UI |

### Modules with no direct test file reference (heuristic)

Fifteen modules had no string match in test sources (some have **indirect** coverage via parents):

- `encryption_migration_worker`, `key_sources.registry_validation`, `script_executor`
- `template_expression_types` (likely covered via tokenizer tests)
- UI: `environment_name_delegate`, `mcp_activity_dialog`, `mcp_tools_overview_dialog`,
  `paste_json_worker`, settings sections (`_common`, `editor_section`, `encryption_config_section`,
  `request_section`, `retry_policy_section`, `security_alert_section`, `server_bind_section`)

Settings sections show **high line coverage indirectly** via `test_settings_dialog.py`; dialogs
and server managers are the real gaps.

### Well-covered critical paths (PASS)

| Area | Representative modules | Coverage |
| --- | --- | ---: |
| Request execution | `request_service.py`, `http_client.py`, `worker.py` | 91–97% |
| Encryption | `environment_secrets_codec.py`, `encryption_migration.py` | 90–93% |
| MCP schema / call_tool | `mcp_server_impl.py`, `mcp_secrets_policy.py` | 90–97% |
| History masking | `sensitive_data_masking_policy.py`, `history_manager.py` | 98–100% |
| Presenters | `tabs_presenter.py`, `env_presenter.py` | 86–91% |

---

## Timeout Compliance

### Enforcement (PASS)

`tests/conftest.py` **`pytest_runtest_setup`** fails any collected test without a closest
`timeout` marker — no reliance on global `pytest.ini` timeout defaults.

```31:36:tests/conftest.py
def pytest_runtest_setup(item):
    if item.get_closest_marker("timeout") is None:
        pytest.fail(
            f"{item.nodeid}: missing pytest.mark.timeout marker "
            "(declare module/class/function timeout; see do-testing.md)",
            pytrace=False,
        )
```

### Marker coverage (PASS)

| Check | Result |
| --- | --- |
| Test files with timeout declaration | **135 / 135** (100%) |
| Files missing module-level `pytestmark` | 0 (function/class overrides only where needed) |

### Timeout tier distribution (module-level `pytestmark`)

| Timeout (s) | Files | Recommended tier (`do-testing.md`) |
| ---: | ---: | --- |
| 10 | 8 | Pure unit |
| 30 | 44 | Pure unit |
| 60 | 65 | GUI / presenter |
| 120 | 30 | Integration / e2e / benchmark |

**Assessment:** Distribution aligns with documented tiers. Integration modules appropriately use
120s. A few GUI files use 60s with internal `QTest.qWait(350)` in `test_settings_persistence.py`
— still bounded and within marker.

### Internal waits (PASS with notes)

Bounded polling patterns found in server/metrics tests (`deadline = time.time() + 10.0` loops with
`time.sleep(0.05)`). `QTest.qWaitForWindowExposed` used in editor tests — acceptable with outer
timeout. No unbounded `Event.wait()` without timeout observed.

**Note:** `test_mcp_server_manager.py` uses `time.sleep(0.05)` inside Qt event loops — bounded but
coincides with **segfault** on port-busy path (native crash, not timeout hang).

---

## Integration vs Unit Balance

### Integration test inventory

| Module | Level | Upstream mock? |
| --- | --- | --- |
| `test_mcp_server_integration.py` | Live Streamable HTTP + uvicorn | `RequestService` mocked |
| `test_mcp_test_collection_integration.py` | Collection tools round-trip | `RequestService` mocked |
| `test_metrics_server_integration.py` | Live `/metrics` + MCP resource | Partial live |
| `test_metrics_server_startup.py` | Bind / port busy signaling | Mixed |
| `test_mcp_server_manager.py` | MCPServerManager thread lifecycle | Live bind (**unstable**) |
| `test_server_bind_host_integration.py` | Bind address fidelity | Live sockets |
| `test_save_flow_integration.py` | Save orchestration | Mocked storage |
| `test_*_e2e.py` (7 files) | MainWindow flows | Mixed |
| `test_makefile.py` | Makefile smoke | Isolated temp workspace |

**Assessment:** MCP and metrics have **good integration depth** with deterministic mocks for HTTP.
Gap: **`mcp_server.py` manager class** is integration-tested but the test module is the **primary
instability source**. Unit coverage of `MCPServerImpl` is strong; manager thread orchestration is
not.

### Unit test strengths

- Protocol and parsing (`test_http_client_protocol.py`, `test_template_expression_tokenizer.py`)
- Policy objects (`test_sensitive_data_masking_policy.py`, `test_mcp_secrets_policy.py`)
- Registry/metrics primitives (`test_metrics_registry.py`, `test_function_registry.py`)
- Widget-level GUI with mocks (`test_response_view_search.py`, `test_code_editor.py`)

---

## Flaky Patterns and Audit Run Failures

### Local `make test` failures (15 total)

| Module | Failures | Root cause |
| --- | ---: | --- |
| `test_makefile.py` | 8 | Marker expects `.initialized-3.11` but isolated `make` uses system `python3` → **3.14** marker |
| `test_solid_audit_baseline.py` | 3 | `main_window.py` 383 LOC (cap 300), class 343 (cap 260); `template_service.py` 204 (cap 200) |
| `test_style_manager_theme.py` | 4 | **Order-dependent** — pass in isolation, fail after full suite |

### Segfault (P1)

`tests/test_mcp_server_manager.py::TestMCPServerManagerStartup::test_port_busy_emits_start_failed`
triggers **Fatal Python error: Segmentation fault** after expected ERROR log on macOS Python
3.11.15 with PySide6. Documented in [PYPOST-429](../PYPOST-429/investigation-report.md). Effect:

- Aborts `make test-cov` mid-run
- May reduce developer trust in local `make test` on macOS
- CI (Linux) may not reproduce — **CI/local divergence**

### asyncio teardown noise (P3)

`test_mcp_server_integration.py` logs `Task was destroyed but it is pending!` from
`sse_starlette` shutdown — test passes; indicates **async cleanup gap**, not a hang.

### Python version matrix

CI runs **3.11 and 3.13** on Ubuntu. Audit host used **3.11.15** with system **3.14** as
default `python3` for subprocess `make` — explains Makefile test drift, not application bugs.

---

## CI Test Configuration

### Main job (`.github/workflows/test.yml`)

| Step | Purpose |
| --- | --- |
| Qt/EGL packages | PySide6 headless dependencies on Ubuntu |
| `pytest pytest-cov flake8 pytest-timeout` | Aligned with `make install` / `venv-test` |
| `pytest tests/ -m "not slow" --cov=pypost` | Fast suite + coverage |
| `--durations=0 --durations-min=1` | Slowest-test output for audit script |
| `--log-file=pytest.log` | Captured logs for guardrails |
| `verify_test_log_guardrails.py` | ERROR log allowlist enforcement |
| `audit_test_durations.py` | 80% warn / 95% fail vs timeout markers |
| Artifacts | `junit.xml`, `coverage.xml` per Python version |

### Slow job (`make-install-smoke`)

Separate job runs `pytest tests/test_makefile.py -m slow` on Python 3.11 — install smoke isolated
from fast matrix.

### Makefile targets

| Target | Command |
| --- | --- |
| `test` | `pytest tests/ -m "not slow"` |
| `test-cov` | fast suite + HTML/term coverage |
| `test-slow` | `-m slow` only |

**Gap:** `pytest.ini` includes `--cov-fail-under=70` in `addopts` but `make test` does not pass
`--cov` — the fail-under is inert unless coverage plugin is active. CI always passes `--cov`.

---

## Test Maintainability

### Strengths

- **Shared helpers:** `tests/helpers/mcp_live_server.py`, `mcp_test_collection.py` reduce
  duplication for MCP round-trips.
- **Meta-tests** validate guardrail scripts themselves (`test_verify_test_log_guardrails.py`,
  `test_audit_test_durations.py`).
- **Injection seams** documented in `doc/dev/testability.md` — consistently used in MCP and
  request tests.
- **Explicit slow marker** keeps default feedback loop under ~90s.

### Weaknesses

| ID | Finding | Severity |
| --- | --- | --- |
| M-001 | Mix of `unittest.TestCase` and pytest functions — harder to apply shared fixtures | P3 |
| M-002 | Duplicate polling loops across server manager / metrics startup tests | P3 |
| M-003 | `test_solid_audit_baseline.py` caps stale vs growing `MainWindow` | P2 |
| M-004 | `test_makefile.py` binds marker name to `sys.version_info` of pytest, not `make` PYTHON | P2 |
| M-005 | Large presenter test files (`test_tabs_presenter.py`, GUI metrics) — high mock setup cost | P3 |

---

## Test Observability

See `50-observability.md` for detail. Summary:

| Mechanism | Status |
| --- | --- |
| CI ERROR log guardrails | Active (`expected_log_allowlist.yaml`) |
| Duration vs timeout audit | Active (PYPOST-573) |
| `caplog` error-path tests | Present in ~10 modules; not universal |
| `log_cli=true` in pytest.ini | WARNING level — noisy locally; CI uses `log_cli=false` |

---

## Prioritized Recommendations

| ID | Priority | Title |
| --- | --- | --- |
| R-P1-001 | P1 | Stabilize or quarantine `test_mcp_server_manager.py` segfault on port-busy path |
| R-P1-002 | P1 | Refresh SOLID audit baseline caps or refactor `main_window` / `template_service` |
| R-P1-003 | P1 | Fix Makefile test Python version coupling for marker assertions |
| R-P2-001 | P2 | Add unit/integration tests for `mcp_server.py` manager without native crash |
| R-P2-002 | P2 | Raise coverage for `metrics_server.py` and `script_executor.py` |
| R-P2-003 | P2 | Add GUI tests for `save_dialog`, `mcp_activity_dialog`, `mcp_tools_overview_dialog` |
| R-P2-004 | P2 | Fix order-dependent `test_style_manager_theme.py` (isolate Qt style state) |
| R-P2-005 | P2 | Document macOS vs Linux test parity and Python version requirements |
| R-P3-001 | P3 | Test `encryption_migration_worker` and `paste_json_worker` directly |
| R-P3-002 | P3 | Expand `caplog` coverage for new ERROR paths per `do-testing.md` |
| R-P3-003 | P3 | Clean up asyncio pending-task warnings in MCP integration teardown |
| R-P3-004 | P3 | Consider pytest-style migration for remaining unittest server tests |

---

## Out of Scope

- Implementing test fixes (ticketed separately)
- Raising `--cov-fail-under` above 70%
- Security/secrets or architecture audits (PYPOST-685, PYPOST-684)
- Manual MCP/Prometheus test procedures
- Mutation testing or load testing

## References

- [doc/dev/testing.md](../../doc/dev/testing.md)
- [.cursor/lsr/do-testing.md](../../.cursor/lsr/do-testing.md)
- [PYPOST-429 investigation](../PYPOST-429/investigation-report.md)
- [doc/dev/testability.md](../../doc/dev/testability.md)
