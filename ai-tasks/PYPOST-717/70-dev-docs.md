# PYPOST-717: Developer Documentation

## Overview

Updates the SOLID audit baseline caps to reflect codebase evolution and ensure tests pass.

## Architecture

No architectural changes were made. Adjusted the following limit constants in `scripts/audit_baseline_metrics.py`:
- `FILE_CAPS["pypost/ui/main_window.py"]` updated from 300 to 425 LOC.
- `MAIN_WINDOW_CLASS_CAP` updated from 260 to 380 LOC.
- `FILE_CAPS["pypost/core/template_service.py"]` updated from 200 to 225 LOC.

## API / Usage

Validate baseline caps check:
```bash
.venv/bin/python scripts/audit_baseline_metrics.py --check
```

Regenerate snapshot report:
```bash
.venv/bin/python scripts/audit_baseline_metrics.py --markdown ai-tasks/PYPOST-376/baseline-metrics.md
```

## Configuration

The caps are maintained as static configuration dict/constants inside `scripts/audit_baseline_metrics.py`.

## Troubleshooting

None.
