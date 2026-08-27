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

### Architecture and sources of truth

| Component | Responsibility |
| --- | --- |
| `scripts/audit_baseline_metrics.py` | Define monitored paths and caps; measure and render |
| `ai-tasks/PYPOST-376/baseline-metrics.md` | Store the canonical generated snapshot |
| `tests/test_solid_audit_baseline.py` | Enforce caps and exact snapshot equality |
| `doc/dev/solid_audit.md` | Explain policy, maintenance, and summary values |

`measure_all()` reads the configured modules, counts physical file lines, and uses the Python
AST for top-level class spans. `format_markdown()` is the only snapshot renderer. The
regression test compares its output exactly with the committed UTF-8 text, including the final
newline.

PYPOST-1025 kept application behavior unchanged while restoring the guards. Collection sidebar
layout is built by the stateless `collections_panel` factory; `CollectionsPresenter` retains
tree and workflow coordination. `EnvPresenter` passes the storage serializer directly to the
existing environment dialog boundary.

| Metric | Audit era (PYPOST-40) | Baseline | Cap |
| --- | ---: | ---: | ---: |
| `main_window.py` file LOC | 1040 | 445 | 477 |
| `MainWindow` class LOC | 1040 | 398 | 426 |

Authoritative generated snapshot (all module caps):
[baseline-metrics.md](../../ai-tasks/PYPOST-376/baseline-metrics.md).

### Usage

**Regenerate snapshot:**

```bash
.venv/bin/python scripts/audit_baseline_metrics.py \
  --markdown ai-tasks/PYPOST-376/baseline-metrics.md
```

**Verify caps (local or CI):**

```bash
.venv/bin/python scripts/audit_baseline_metrics.py --check
make test PYTEST_ARGS='tests/test_solid_audit_baseline.py -v'
```

Use `--json PATH` when a machine-readable measurement report is needed. With no output flag,
the command prints the canonical Markdown to stdout.

### Configuration and maintenance

- `FILE_CAPS` defines monitored file limits; `MAIN_WINDOW_CLASS_CAP` separately guards the
  `MainWindow` class span.
- `AUDIT_ERA_LOC` provides historical comparisons. A dash in the generated table means that
  the module was added after the audit-era inventory.
- `BASELINE_DATE` is the policy provenance date, not the latest regeneration timestamp.
- Prefer behavior-preserving extraction before raising a cap. If growth is intentional,
  document the rationale beside the cap, normally retain about 10% headroom, regenerate the
  snapshot, and update summary values in this document.
- Commit the generator or cap change and regenerated snapshot together.

### Troubleshooting

- **`--check` prints `lines exceeds cap`:** reduce the module, or justify and update its cap,
  then regenerate the snapshot.
- **Caps pass but snapshot equality fails:** regenerate the snapshot and inspect its diff;
  do not hand-edit generated values.
- **Snapshot changes unexpectedly:** check the listed source-module diffs before accepting
  the regenerated measurements.
- **Summary values disagree:** copy current values from the generated snapshot into this
  document.
- **A monitored file was renamed or removed:** update `FILE_CAPS` and, when applicable,
  `AUDIT_ERA_LOC` in the same change.

Always run both `--check` and the pytest module after reconciliation. A green cap check alone
does not prove that the committed snapshot is fresh.

**PYPOST-1082 (2026-08-19):** Retired the four temporary delegating shims on `EnvPresenter`
(`mcp_status_text`, `mcp_tools_button_text`, `mcp_activity_button_text`, `refresh_mcp_tools`),
updated its class docstring, exposed the `mcp_controls` property seam on `EnvPresenter` and
`MainWindow`, and re-routed `main_window_signals.py` directly to `window.mcp_controls.refresh_tools`.
See [`presenter_architecture.md`](presenter_architecture.md).

**PYPOST-1071 (2026-08-16):** Gave each of the five measured violations an explicit
disposition instead of a blanket cap raise. Extracted PYPOST-1044's misplaced
responsibilities first: multi-server persistence and lifecycle control moved from
`MainWindow` to [`pypost/ui/mcp_server_controller.py`](../../pypost/ui/mcp_server_controller.py)
and MCP status controls, dialogs and scoped refresh routing moved from `EnvPresenter` to
[`mcp_controls_presenter.py`](../../pypost/ui/presenters/mcp_controls_presenter.py).
`EnvPresenter` keeps its four public `mcp_*` methods as delegating shims because
`main_window_signals.py` connects `refresh_mcp_tools` to three Qt signals. Both modules were
brought back inside their existing caps (`main_window.py` 433/435, `MainWindow` class 387/390,
`env_presenter.py` 392/470) *before* recalibration, then re-derived at about 10% headroom:
`main_window.py` 477, `MainWindow` class 426, `env_presenter.py` 432. The remaining two
violations were accepted transparently rather than decomposed — `http_client.py` 380 → cap 418
(PYPOST-1037 template-conversion and failure translation are cohesive with outbound transport)
and `collections_presenter.py` 366 → cap 403 (thin delegation only; import/export/tree
algorithms stay in their action objects). Both new extraction targets were added to
`FILE_CAPS` on creation so the relocated lines stay measured — `mcp_server_controller.py`
269 → cap 296 and `mcp_controls_presenter.py` 329 → cap 362, the same ~10% headroom policy.
Snapshot regenerated from the generator.

**PYPOST-1025 (2026-08-02):** Reconciled baseline drift without raising caps — extracted
collection panel assembly (`collections_presenter.py` 328/330) and simplified environment
serializer wiring (`env_presenter.py` 470/470). Regenerated the canonical snapshot and added
an exact snapshot-freshness regression guard.

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
