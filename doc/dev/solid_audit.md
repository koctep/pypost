# SOLID and Maintainability Audit

This document describes the PyPost codebase audit for SOLID compliance and design for
maintainability (PYPOST-40). The audit provides a foundation for refactoring decisions and
technical debt prioritization.

## Audit Report

Full report: [ai-tasks/PYPOST-40/30-audit-report.md](../../ai-tasks/PYPOST-40/30-audit-report.md)

## Key Findings

- **MainWindow** — **resolved ([PYPOST-43](https://pypost.atlassian.net/browse/PYPOST-43))**:
  Decomposed into presenters; now a composition root (audit-era god-object was 1040 LOC).
  Current baseline LOC and CI regression caps:
  [baseline-metrics.md](../../ai-tasks/PYPOST-376/baseline-metrics.md) (PYPOST-376).
- **Singletons/globals**: ~~MetricsManager~~ resolved (PYPOST-44, [PYPOST-167](../../ai-tasks/PYPOST-167/70-dev-docs.md));
  ~~`template_service` module global~~ resolved (PYPOST-45); lifecycle and test seams documented
  ([PYPOST-143](../../ai-tasks/PYPOST-143/70-dev-docs.md), [template_service.md](template_service.md)).
  Remaining direct instantiation in RequestService/RequestWorker — see [testability.md](testability.md)
  (PYPOST-382).
- **Direct instantiation**: RequestService still creates default HTTP/MCP clients when not
  injected; RequestWorker creates RequestService internally. Constructor seams and test patterns
  documented in [testability.md](testability.md) (PYPOST-382, PYPOST-46).

## Prioritized Recommendations

| Priority | Recommendation |
|----------|----------------|
| P1 | ~~Decompose MainWindow~~ **resolved** ([PYPOST-43](https://pypost.atlassian.net/browse/PYPOST-43)); ~~MetricsManager/template_service injection~~ (PYPOST-44/45/167) |
| P2 | HTTPClient protocol; ~~unified collection loading~~ (PYPOST-47); item_type strategy; ~~split MetricsManager~~ (PYPOST-49) |
| P3 | ~~StorageInterface~~ (PYPOST-50); ~~ExecuteRequestProtocol~~ (PYPOST-51) |

## Regression baseline metrics (PYPOST-376)

The audit report recorded qualitative findings but no numeric regression anchors. PYPOST-376 adds
LOC baselines and caps so god-object regressions (especially `MainWindow` growth) fail CI.

| Metric | Audit era (PYPOST-40) | Baseline (2026-06-11) | Cap |
| --- | ---: | ---: | ---: |
| `main_window.py` file LOC | 1040 | 416 | 435 |
| `MainWindow` class LOC | 1040 | 375 | 390 |

Authoritative snapshot (all module caps): [baseline-metrics.md](../../ai-tasks/PYPOST-376/baseline-metrics.md)

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

**PYPOST-728 (2026-07-14):** Verified R-P1-001 compliance — `main_window.py` (393/425),
`MainWindow` class (353/380), and `template_service.py` (204/225) all within refreshed caps.

**PYPOST-843 (2026-07-22):** Refreshed regression caps after measured growth —
`main_window.py` 435, `MainWindow` class 390, `env_presenter.py` 470 — and
confirmed `make check` green with lifecycle mid-start harness coverage.
`audit_baseline_metrics.py --check` and `test_solid_audit_baseline.py` pass.

**PYPOST-735 (2026-07-14):** Closed R-P2-006 — `pypost/core/qt/metrics.py` cap raised 165→181
(164 LOC measured); `pypost/ui/widgets/mixins.py` added at cap 411 (373 LOC). Snapshot refreshed.

**PYPOST-768 (2026-07-14):** Closed R-P2-002 (PYPOST-690) — refreshed MainWindow narrative;
marked [PYPOST-43](https://pypost.atlassian.net/browse/PYPOST-43) resolved; Key Findings and
regression table cite [baseline-metrics.md](../../ai-tasks/PYPOST-376/baseline-metrics.md)
(393 file / 353 class baseline; 425 / 380 caps).

**PYPOST-776 (2026-07-14):** Closed R-P3-004 (PYPOST-690) — regenerated
[baseline-metrics.md](../../ai-tasks/PYPOST-376/baseline-metrics.md) snapshot; regression table
synced (416 file / 375 class baseline; caps unchanged).

## Individual dialog audit (PYPOST-374)

PYPOST-40 grouped `ui/dialogs/` (~400 LOC) without per-dialog SOLID scoring. PYPOST-374 audits
each module under `pypost/ui/dialogs/` (seven files, 923 LOC as of 2026-06-11).

Full report:
[ai-tasks/PYPOST-374/30-dialogs-audit-report.md](../../ai-tasks/PYPOST-374/30-dialogs-audit-report.md)

| Dialog | LOC | Primary finding |
| --- | ---: | --- |
| `settings_dialog.py` | 423 | P1 — multi-domain SRP violation |
| `mcp_activity_dialog.py` | 117 | OK — data-injected read-only viewer |
| `hotkeys_dialog.py` | ~70 | OK — derives shortcuts from tagged QActions ([PYPOST-599](hotkeys.md)) |
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

## Collection tree performance (PYPOST-383)

The audit did not identify new performance-specific findings. Known collection-tree scale
behavior (full vs incremental model refresh) was already filed under
[PYPOST-35](https://pypost.atlassian.net/browse/PYPOST-35); follow-up work added incremental
delete ([PYPOST-334](https://pypost.atlassian.net/browse/PYPOST-334)), rename
([PYPOST-347](https://pypost.atlassian.net/browse/PYPOST-347)), and save-as insert
([PYPOST-319](https://pypost.atlassian.net/browse/PYPOST-319)).

Full inventory: [collection_tree_performance.md](collection_tree_performance.md)

## Related

- [Architecture Overview](architecture.md)
- [Technical Debt: PYPOST-40](tech-debt/PYPOST-40.md)
- [Collection Tree Performance](collection_tree_performance.md)
- [Testing: SOLID audit baseline](testing.md#solid-audit-baseline-pypost-376)
- [Testing: Dialog audit inventory](testing.md#dialog-audit-inventory-pypost-374)
