# PYPOST-735: Architecture — Extend baseline caps

## Research

### PYPOST-687 finding R-P2-006

| Module | Measured LOC | Cap status |
| --- | ---: | --- |
| `pypost/core/qt/metrics.py` | 164 | Capped at 165 (~0.6% headroom) |
| `pypost/ui/widgets/mixins.py` | 373 | Not in `FILE_CAPS` |

### Option analysis

| Option | Verdict |
| --- | --- |
| Split `VariableHoverMixin` from editor helpers | Rejected — no user benefit; growth is stable; cap alignment matches PYPOST-717 pattern |
| Add/update caps with ~10% headroom | **Chosen** — minimal, consistent with PYPOST-376 policy |

### Target caps (164 × 1.1 → 181; 373 × 1.1 → 411)

| Module | Current LOC | New cap |
| --- | ---: | ---: |
| `pypost/core/qt/metrics.py` | 164 | 181 |
| `pypost/ui/widgets/mixins.py` | 373 | 411 |

## Implementation Plan

1. Update `FILE_CAPS` in `scripts/audit_baseline_metrics.py`.
2. Regenerate `ai-tasks/PYPOST-376/baseline-metrics.md`.
3. Run `audit_baseline_metrics.py --check` and `test_solid_audit_baseline.py`.
4. Add PYPOST-735 closure note to `doc/dev/solid_audit.md`.

No production module moves. Cap enforcement unchanged (`check_caps`, pytest guard).
