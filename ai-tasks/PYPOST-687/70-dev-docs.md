# PYPOST-687: Dev Docs

## Updates

| File | Change |
| --- | --- |
| `doc/dev/maintainability_audit.md` | **Created** — code quality and maintainability audit summary |
| `doc/dev/README.md` | Added table-of-contents entry for maintainability audit |

## Key Points for Maintainers

- Full audit report: [30-audit-report.md](30-audit-report.md)
- Developer summary: [doc/dev/maintainability_audit.md](../../doc/dev/maintainability_audit.md)
- Scale: 141 modules, ~16,425 LOC; PYPOST-40 era was ~4,100 LOC
- **`make lint` fails** (4 flake8 issues); **`audit_baseline_metrics.py --check` fails** (3 caps)
- Complexity hotspots: `tabs_presenter.py` (715), `encryption_migration.py` (656, 225-LOC function)
- PYPOST-40 wins: MainWindow decomposed, metrics/template injection resolved
- P1/P2/P3 follow-ups in [60-tech-debt.md](60-tech-debt.md) (orchestrator tickets separately)

## Related Docs

- [solid_audit.md](../../doc/dev/solid_audit.md) — SOLID audit and cap commands
- [test_audit.md](../../doc/dev/test_audit.md) — test suite health (PYPOST-686)
- [architecture_audit.md](../../doc/dev/architecture_audit.md) — package boundaries (PYPOST-684)
- [testability.md](../../doc/dev/testability.md) — injection seams (PYPOST-382)
