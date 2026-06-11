# SOLID and Maintainability Audit

This document describes the PyPost codebase audit for SOLID compliance and design for
maintainability (PYPOST-40). The audit provides a foundation for refactoring decisions and
technical debt prioritization.

## Audit Report

Full report: [ai-tasks/PYPOST-40/30-audit-report.md](../../ai-tasks/PYPOST-40/30-audit-report.md)

## Key Findings

- **MainWindow** (282 file / 246 class LOC as of 2026-06-11 baseline; 1040 at audit time):
  Acts as a composition root after PYPOST-43 presenter split. Regression caps in
  [baseline-metrics.md](../../ai-tasks/PYPOST-376/baseline-metrics.md).
- **Singletons/globals**: MetricsManager and template_service hinder testability and DIP.
  Replace with constructor injection.
- **Direct instantiation**: RequestService still creates default HTTP/MCP clients when not
  injected; RequestWorker creates RequestService internally. Constructor seams and test patterns
  documented in [testability.md](testability.md) (PYPOST-382). Full protocol refactor: PYPOST-46.

## Prioritized Recommendations

| Priority | Recommendation |
|----------|----------------|
| P1 | Decompose MainWindow; replace MetricsManager/template_service with injection |
| P2 | HTTPClient protocol; ~~unified collection loading~~ (PYPOST-47); item_type strategy; split MetricsManager |
| P3 | StorageInterface; ExecuteRequestProtocol |

## Regression baseline metrics (PYPOST-376)

The audit report recorded qualitative findings but no numeric regression anchors. PYPOST-376 adds
LOC baselines and caps so god-object regressions (especially `MainWindow` growth) fail CI.

| Metric | Audit era (PYPOST-40) | Baseline (2026-06-11) | Cap |
| --- | ---: | ---: | ---: |
| `main_window.py` file LOC | 1040 | 282 | 300 |
| `MainWindow` class LOC | 1040 | 246 | 260 |

Full module table: [ai-tasks/PYPOST-376/baseline-metrics.md](../../ai-tasks/PYPOST-376/baseline-metrics.md)

**Regenerate snapshot:**

```bash
.venv/bin/python scripts/audit_baseline_metrics.py \
  --markdown ai-tasks/PYPOST-376/baseline-metrics.md
```

**Verify caps (local or CI):**

```bash
.venv/bin/python scripts/audit_baseline_metrics.py --check
pytest tests/test_solid_audit_baseline.py -v
```

Caps live in `scripts/audit_baseline_metrics.py`. After intentional module growth, remeasure,
update caps with ~10% headroom, and refresh the snapshot.

## Individual dialog audit (PYPOST-374)

PYPOST-40 grouped `ui/dialogs/` (~400 LOC) without per-dialog SOLID scoring. PYPOST-374 audits
each module under `pypost/ui/dialogs/` (seven files, 923 LOC as of 2026-06-11).

Full report:
[ai-tasks/PYPOST-374/30-dialogs-audit-report.md](../../ai-tasks/PYPOST-374/30-dialogs-audit-report.md)

| Dialog | LOC | Primary finding |
| --- | ---: | --- |
| `settings_dialog.py` | 423 | P1 — multi-domain SRP violation |
| `mcp_activity_dialog.py` | 117 | OK — data-injected read-only viewer |
| `hotkeys_dialog.py` | 91 | P2 — hardcoded shortcut list |
| `save_dialog.py` | 91 | OK — thin save-as form |
| `env_dialog.py` | 89 | OK — widget composition facade |
| `mcp_tools_overview_dialog.py` | 72 | OK — data-injected read-only viewer |
| `about_dialog.py` | 40 | P3 — hardcoded version string |

**Regenerate inventory:**

```bash
.venv/bin/python scripts/audit_dialogs_inventory.py --markdown
```

**Verify audit report lists every dialog module:**

```bash
.venv/bin/python scripts/audit_dialogs_inventory.py --check
pytest tests/test_dialogs_audit.py -v
```

When adding a new dialog, extend `30-dialogs-audit-report.md` so `--check` and
`test_dialogs_audit.py` keep passing.

## Related

- [Architecture Overview](architecture.md)
- [Technical Debt: PYPOST-40](tech-debt/PYPOST-40.md)
- [Testing: SOLID audit baseline](testing.md#solid-audit-baseline-pypost-376)
- [Testing: Dialog audit inventory](testing.md#dialog-audit-inventory-pypost-374)
