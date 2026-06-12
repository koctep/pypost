# PYPOST-717: Update SOLID audit baseline caps

## Research

We analyzed `scripts/audit_baseline_metrics.py` and `tests/test_solid_audit_baseline.py`.
The caps are defined as a python dictionary `FILE_CAPS` and a constant `MAIN_WINDOW_CLASS_CAP`.
No external API or network calls are required for this task. It is a configuration update in Python.

## Implementation Plan

1. In `scripts/audit_baseline_metrics.py`, update:
   - `FILE_CAPS["pypost/ui/main_window.py"]` to `425`
   - `MAIN_WINDOW_CLASS_CAP` to `380`
   - `FILE_CAPS["pypost/core/template_service.py"]` to `225`
2. Run `make test` to verify that the SOLID baseline tests pass.

## Architecture

No new modules are introduced. We are adjusting baseline limits in an existing testing script to match the production codebase growth.

## Q&A

- **Q**: Why did the codebase grow?
- **A**: Standard evolution and enhancement of features in PyPost since the original SOLID baseline was set.
