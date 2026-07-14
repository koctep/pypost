# PYPOST-728: Developer Documentation

## Overview

Closed PYPOST-687 R-P1-001 by verifying SOLID regression caps pass for `main_window.py` and
`template_service.py`. Remediation path: justified cap refresh (PYPOST-376), not LOC refactor.

## Cap Status (2026-07-14)

| Module | LOC | Cap | Status |
| --- | ---: | ---: | --- |
| `main_window.py` | 393 | 425 | PASS |
| `MainWindow` class | 353 | 380 | PASS |
| `template_service.py` | 204 | 225 | PASS |

## Verification Commands

```bash
python3 scripts/audit_baseline_metrics.py --check
pytest tests/test_solid_audit_baseline.py -v
```

## Documentation

See `doc/dev/solid_audit.md` § Regression baseline metrics (PYPOST-376).
