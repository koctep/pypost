# PYPOST-686: Technical Debt Analysis

**Task type:** Test coverage and quality audit (no application code changes).

**Source:** `30-audit-report.md` — P1/P2/P3 remediation recommendations.

Twelve remediation items ticketed in Jira (PYPOST-716–727).

## Shortcuts Taken

- **Batched coverage measurement:** Full `make test-cov` segfaulted locally; coverage obtained via
  chunked `pytest --cov` runs excluding `test_mcp_server_manager.py`.
- **Heuristic untested-module list:** String search in test sources; indirect coverage not fully
  traced.
- **No CI artifact pull:** Findings rely on local runs + workflow inspection; Linux CI may differ.
- **No code fixes in scope:** Findings document gaps; remediation deferred to follow-up work.

## Code Quality Issues

Test suite health issues observed in the audited codebase (not introduced by this task):

- **Segfault in server manager tests (P1):** `test_port_busy_emits_start_failed` aborts suite on
  macOS (PYPOST-429 context).
- **Stale SOLID baseline caps (P1):** `test_solid_audit_baseline.py` fails on `main_window` and
  `template_service` growth.
- **Makefile test version coupling (P1):** Marker assertions assume pytest interpreter version
  matches `make` `PYTHON`.
- **Low coverage on server lifecycle (P2):** `mcp_server.py`, `metrics_server.py`,
  `script_executor.py`.
- **Untested dialogs (P2):** `save_dialog`, `mcp_activity_dialog`, `mcp_tools_overview_dialog`.
- **Order-dependent theme tests (P2):** `test_style_manager_theme.py` fails in full suite only.

## Missing Tests

Coverage gaps from audit (see `30-audit-report.md` for evidence):

- No stable automated tests for full `MCPServerManager` port-busy path on macOS
- UI dialogs with &lt;20% line coverage lack focused widget tests
- `main.py` entry point untested (common for Qt apps; optional smoke)
- `encryption_migration_worker` — partial indirect coverage only

## Performance Concerns

- Fast suite ~89s local — acceptable for 1,400+ tests
- 30 files use 120s timeout tier — appropriate for integration; monitor via duration audit
- `test_settings_persistence.py` uses `QTest.qWait(350)` — within 120s marker but relatively slow

## Follow-up Tasks

### P1 — Critical / merge-gate or suite-abort risk

#### R-P1-001 — Stabilize MCPServerManager port-busy test (segfault)

- **Priority:** P1
- **Finding refs:** Flaky — segfault
- **Description:** `test_mcp_server_manager.py::test_port_busy_emits_start_failed` segfaults on
  macOS Python 3.11 after expected ERROR log, aborting `make test-cov` and sometimes full suite.
- **Remediation:** Reproduce on Linux CI; mock uvicorn bind, split Qt/thread concerns, or mark
  platform-specific skip until PYPOST-429 root cause fixed.

#### R-P1-002 — Update SOLID audit baseline caps for MainWindow growth

- **Priority:** P1
- **Finding refs:** M-003, `test_solid_audit_baseline.py` failures
- **Description:** `main_window.py` (383 LOC, cap 300) and `MainWindow` class (343, cap 260);
  `template_service.py` (204, cap 200) fail regression guards.
- **Remediation:** Refactor to reduce LOC **or** update `scripts/audit_baseline_metrics.py` caps
  with documented justification in `doc/dev/solid_audit.md`.

#### R-P1-003 — Fix Makefile test Python version marker coupling

- **Priority:** P1
- **Finding refs:** M-004, 8 `test_makefile.py` failures
- **Description:** Tests compute `MARKER_NAME` from pytest's `sys.version_info` but isolated
  `make` uses system `python3` (e.g. 3.14), producing `.initialized-3.14` vs expected 3.11.
- **Remediation:** Pass explicit `PYTHON=` to make in tests matching the pytest interpreter, or
  read marker from `make` stdout instead of hardcoding version.

### P2 — Meaningful coverage or stability gaps

#### R-P2-001 — Unit test MCPServerManager lifecycle without live segfault path

- **Priority:** P2
- **Finding refs:** `mcp_server.py` 38% coverage
- **Description:** Manager thread orchestration under-tested at unit level; integration tests
  unstable.
- **Remediation:** Mock `_run_server`, assert signals (`start_failed`, `status_changed`) without
  occupying ports on main thread.

#### R-P2-002 — Raise coverage for metrics_server and script_executor

- **Priority:** P2
- **Finding refs:** Coverage table
- **Description:** `metrics_server.py` 50%, `script_executor.py` 40% — MCP metrics resource and
  post-script paths.
- **Remediation:** Unit tests with mocked uvicorn/HTTP; script_executor with isolated sandbox.

#### R-P2-003 — GUI tests for save and MCP overview dialogs

- **Priority:** P2
- **Finding refs:** Low-coverage dialogs
- **Description:** `save_dialog.py`, `mcp_activity_dialog.py`, `mcp_tools_overview_dialog.py`
  below 20% coverage.
- **Remediation:** Offscreen Qt tests with mocked dependencies per `doc/dev/gui_testing.md`.

#### R-P2-004 — Isolate Qt style state in theme tests

- **Priority:** P2
- **Finding refs:** Order-dependent `test_style_manager_theme.py`
- **Description:** Four tests fail in full suite, pass in isolation — global `QApplication` style
  pollution.
- **Remediation:** Module-scoped style reset fixture or `qapp` isolation pattern.

#### R-P2-005 — Document local vs CI test parity (macOS, Python versions)

- **Priority:** P2
- **Finding refs:** Makefile failures, segfault
- **Description:** Developers on macOS with multiple Python versions see different results than
  Ubuntu CI matrix.
- **Remediation:** Add section to `doc/dev/testing.md` / `test_audit.md` with troubleshooting.

### P3 — Minor gaps and hygiene

#### R-P3-001 — Direct tests for encryption_migration_worker and paste_json_worker

- **Priority:** P3
- **Finding refs:** Untested module heuristic
- **Description:** Workers have partial indirect coverage; no focused failure-path tests.
- **Remediation:** Qt signal tests with mocked codec/gateway.

#### R-P3-002 — Expand caplog coverage for ERROR-path tests

- **Priority:** P3
- **Finding refs:** O-003, `do-testing.md` C1–C5
- **Description:** ~10 modules use `caplog`; others rely solely on allowlist.
- **Remediation:** Prefer caplog assertions when adding or touching error-path tests.

#### R-P3-003 — Clean up MCP integration asyncio teardown warnings

- **Priority:** P3
- **Finding refs:** O-004
- **Description:** `Task was destroyed but it is pending!` from sse_starlette on shutdown.
- **Remediation:** Await transport shutdown or suppress in test harness with bounded wait.

#### R-P3-004 — Migrate unittest server tests to pytest style

- **Priority:** P3
- **Finding refs:** M-001
- **Description:** `test_mcp_server_manager.py` uses `unittest.TestCase` with manual polling.
- **Remediation:** pytest fixtures for port helpers; shared wait helper to reduce duplication.

## Blocker Review

**SAFE TO CLOSE** — audit deliverables complete; no application code changes required. Suite is
broad and timeout-compliant; follow-up work addresses instability, baseline drift, and targeted
coverage gaps. Twelve follow-up items ticketed in Jira (PYPOST-716–727).
