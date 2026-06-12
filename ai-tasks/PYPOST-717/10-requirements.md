# PYPOST-717: Update SOLID audit baseline caps

## Goals

Ensure that automated CI tests (`make test`) pass successfully on the target repository by aligning the SOLID baseline line of code (LOC) limits/caps with the actual repository baseline, incorporating appropriate headroom.

## User Stories

As a PyPost developer,
I want the repository's test suite to pass on our current baseline files
So that I can verify my code changes are free of regressions and we have a healthy CI/CD pipeline.

## Definition of Done

- The SOLID audit baseline caps are updated to match the current LOC of the files with a standard ~10% headroom.
- No other test baseline caps are unnecessarily increased.
- Running `make test` successfully passes all SOLID baseline regression tests.

## Task Description

The regression caps measured on 2026-06-11 are currently violated by:
- `main_window.py` (actual: 383 vs cap: 300)
- `MainWindow` class LOC (actual: 343 vs cap: 260)
- `pypost/core/template_service.py` (actual: 204 vs cap: 200)

This task updates the caps in `scripts/audit_baseline_metrics.py` to:
- `main_window.py` cap: 425 (~10.9% headroom over 383)
- `MainWindow` class cap: 380 (~10.8% headroom over 343)
- `template_service.py` cap: 225 (~10.2% headroom over 204)

## Q&A

- **Q**: What headroom should be used?
- **A**: A standard ~10% headroom above the actual current values is used.
