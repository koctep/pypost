# PYPOST-761 — Technical Debt

## Blockers

None — histogram wired, tested, and documented.

## Non-blockers (deferred)

| Item | Rationale |
| --- | --- |
| Custom histogram buckets tuned for sub-ms renders | Default Prometheus buckets sufficient for P3; revisit if p99 alerts misfire |
| Separate compile vs render duration | Single wall-clock matches operator need; compile cache already logged at DEBUG |
| Auto-update prometheus_monitoring count in CI | Manual `rg` verification documented in PYPOST-750 |

## Parent audit closure

Remediates [PYPOST-689 R-P3-001](../PYPOST-689/60-tech-debt.md#r-p3-001--add-template-render-duration-histogram).
