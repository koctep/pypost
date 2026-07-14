# PYPOST-776: Developer Documentation

## Overview

Refreshed the PYPOST-376 SOLID baseline snapshot to close PYPOST-690 documentation audit finding
D-004 (R-P3-004).

## Snapshot changes (MainWindow)

| Metric | Before | After | Cap |
| --- | ---: | ---: | ---: |
| `main_window.py` file LOC | 393 | 416 | 425 |
| `MainWindow` class LOC | 353 | 375 | 380 |

Full module inventory: [baseline-metrics.md](../PYPOST-376/baseline-metrics.md).

## Verification

```bash
.venv/bin/python scripts/audit_baseline_metrics.py --check
make check
```

Regenerate snapshot:

```bash
.venv/bin/python scripts/audit_baseline_metrics.py \
  --markdown ai-tasks/PYPOST-376/baseline-metrics.md
```

## Doc updates

| File | Change |
| --- | --- |
| `doc/dev/solid_audit.md` | Regression table synced; PYPOST-776 closure note added |

See also [solid_audit.md](../../doc/dev/solid_audit.md).
