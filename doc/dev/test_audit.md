# Test Coverage and Quality Audit

This document summarizes the PyPost test suite health audit (PYPOST-686). It complements
[testing.md](testing.md) (how to run tests) and
[do-testing.md](../../.cursor/lsr/do-testing.md) (agent timeout rules).

## Audit Report

Full report:
[ai-tasks/PYPOST-686/30-audit-report.md](../../ai-tasks/PYPOST-686/30-audit-report.md)

**Date:** 2026-06-12 | **Scope:** Coverage, timeouts, CI guardrails, integration balance,
flaky patterns, maintainability

## Executive Summary

| Metric | Value |
| --- | --- |
| Test modules | 135 |
| Fast suite tests collected | 1,423 |
| Line coverage (audit measurement) | **~88%** |
| CI coverage gate | **70%** (`pytest.ini`, `test.yml`) |
| Timeout marker compliance | **100%** (enforced in `conftest.py`) |
| Typical `make test` runtime | ~90s |

The suite is **large and well-instrumented**: explicit per-test timeouts, ERROR log guardrails,
and duration-vs-timeout audits in CI. Core paths (HTTP execution, encryption, MCP schemas,
history masking) are strongly covered.

**Top risks:**

1. **Segfault** in `tests/test_mcp_server_manager.py` on macOS during port-busy startup test —
   can abort `make test-cov` locally ([PYPOST-429](../ai-tasks/PYPOST-429/investigation-report.md)).
2. **Regression guard failures** — `test_solid_audit_baseline.py` (MainWindow / template_service
   LOC caps exceeded).
3. **Makefile tests** — marker version mismatch when system `python3` ≠ pytest interpreter.
4. **Coverage gaps** — `mcp_server.py`, `metrics_server.py`, `script_executor.py`, several UI
   dialogs.
5. **Order-dependent** `test_style_manager_theme.py` failures in full suite.

## Timeout Compliance

Every collected test must declare `@pytest.mark.timeout(...)` or module `pytestmark`. Missing
markers fail at setup via `tests/conftest.py` — see [do-testing.md](../../.cursor/lsr/do-testing.md).

Typical tiers: 10–30s (unit), 60s (GUI), 120s (integration/e2e).

## CI Guardrails

| Script | Purpose |
| --- | --- |
| `scripts/verify_test_log_guardrails.py` | Reject unexpected ERROR logs vs allowlist |
| `scripts/audit_test_durations.py` | Warn at 80%, fail at 95% of declared timeout |

CI matrix: Python **3.11** and **3.13** on Ubuntu; separate slow job for `make install` smoke.

## Coverage Gaps (below 70%)

| Module | Coverage | Notes |
| --- | ---: | --- |
| `pypost/main.py` | 0% | GUI entry — optional smoke |
| `pypost/core/mcp_server.py` | 38% | Manager thread lifecycle |
| `pypost/core/script_executor.py` | 40% | Post-script MCP logs |
| `pypost/core/metrics_server.py` | 50% | Metrics uvicorn server |
| MCP/save dialogs | 17–18% | Low direct GUI coverage |

## Local vs CI

- Use `make install` then `make test` for fast regression.
- macOS may hit Qt segfaults not seen on Linux CI — run problematic modules in isolation if needed.
- Ensure `python3` for Makefile subprocess tests matches your `.venv` interpreter when debugging
  `test_makefile.py`.

## Follow-up Work

Prioritized remediation items (3 P1, 5 P2, 4 P3) are listed in
[ai-tasks/PYPOST-686/60-tech-debt.md](../../ai-tasks/PYPOST-686/60-tech-debt.md). Jira tickets
are created by the sprint orchestrator.
