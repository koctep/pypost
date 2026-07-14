# PYPOST-776: Architecture — Regenerate baseline snapshot

## Research

### PYPOST-690 finding D-004

| Metric | Stale snapshot | Live (pre-refresh) | Cap |
| --- | ---: | ---: | ---: |
| `main_window.py` file LOC | 393 | 416 | 425 |
| `MainWindow` class LOC | 353 | 375 | 380 |

Additional module baseline drift (e.g. `tabs_presenter.py` 736→606, `template_service.py`
204→132) confirmed snapshot staleness without cap breaches.

### Option analysis

| Option | Verdict |
| --- | --- |
| Manually edit `baseline-metrics.md` | Rejected — bypasses `audit_baseline_metrics.py`; risks inconsistency with `--check` |
| Regenerate via `--markdown` | **Chosen** — project-standard procedure per PYPOST-376 and `doc/dev/solid_audit.md` |
| Raise caps for modules near limits | Out of scope — no breaches; `worker.py` at cap only |

## Implementation Plan

1. Run `.venv/bin/python scripts/audit_baseline_metrics.py --markdown ai-tasks/PYPOST-376/baseline-metrics.md`.
2. Run `audit_baseline_metrics.py --check` to confirm caps hold.
3. Update `doc/dev/solid_audit.md` regression table and add PYPOST-776 closure note.
4. Run `make check`.

No changes to `FILE_CAPS`, production modules, or tests.
