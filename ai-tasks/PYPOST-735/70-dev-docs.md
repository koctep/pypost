# PYPOST-735: Developer Documentation

## Overview

Extended SOLID regression caps for `metrics.py` and added `mixins.py` to the baseline inventory
(PYPOST-687 R-P2-006).

## Cap changes

| Module | LOC | Cap (before) | Cap (after) |
| --- | ---: | ---: | ---: |
| `pypost/core/qt/metrics.py` | 164 | 165 | 181 |
| `pypost/ui/widgets/mixins.py` | 373 | — | 411 |

Headroom policy: ~10% above measured LOC (PYPOST-376, PYPOST-717).

## Verification

```bash
.venv/bin/python scripts/audit_baseline_metrics.py --check
make test
```

Regenerate snapshot:

```bash
.venv/bin/python scripts/audit_baseline_metrics.py \
  --markdown ai-tasks/PYPOST-376/baseline-metrics.md
```

See also [solid_audit.md](../../doc/dev/solid_audit.md).
