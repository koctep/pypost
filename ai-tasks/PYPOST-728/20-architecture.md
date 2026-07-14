# PYPOST-728: Architecture — SOLID cap compliance

## Research

### PYPOST-687 finding

R-P1-001 flagged three cap violations at audit time using pre-PYPOST-376 cap values:

| Module | Audit LOC | Audit cap | Status |
| --- | ---: | ---: | --- |
| `main_window.py` file | 383 | 300 | Exceeded |
| `MainWindow` class | 343 | 260 | Exceeded |
| `template_service.py` | 204 | 200 | Exceeded |

### PYPOST-376 remediation (already applied)

Baseline remeasured 2026-06-11 after presenter split (PYPOST-43). Caps set with ~10% headroom:

| Module | Baseline LOC | Cap | Current LOC (2026-07-14) |
| --- | ---: | ---: | ---: |
| `main_window.py` file | 383 | 425 | 393 |
| `MainWindow` class | 343 | 380 | 353 |
| `template_service.py` | 204 | 225 | 204 |

### Option analysis

| Option | Verdict |
| --- | --- |
| **Refactor to old caps (300/260/200)** | Rejected — would require extracting ~90 LOC from main_window with no user benefit; caps already refreshed with justification |
| **Verify refreshed caps pass** | **Chosen** — minimal correct closure for R-P1-001 |
| **Further refactor below baseline** | Out of scope — tracked as PYPOST-731 (tabs_presenter) and similar P2 items |

## Implementation Plan

1. Run `audit_baseline_metrics.py --check` — expect exit 0.
2. Run `test_solid_audit_baseline.py` — expect 3 passed.
3. Add cap-status note to `doc/dev/solid_audit.md` referencing PYPOST-728 closure.
4. No production code changes required.

## Architecture

Cap enforcement remains in:

- `scripts/audit_baseline_metrics.py` — `FILE_CAPS`, `MAIN_WINDOW_CLASS_CAP`
- `tests/test_solid_audit_baseline.py` — CI guardrail
- `doc/dev/solid_audit.md` — human-readable justification

Dependency direction unchanged. No module moves required.
