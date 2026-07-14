# PYPOST-773: Dev Docs Summary

## Updated files

| File | Changes |
| --- | --- |
| `doc/dev/README.md` | Added Prometheus Monitoring TOC entry under Audits (after observability audit) |

## Maintainer workflow

When adding operator-facing guides under `doc/` (not `doc/dev/`):

1. Add a cross-link in `doc/dev/README.md` so contributors find the guide from the dev hub.
2. Use `../<filename>.md` relative paths from `doc/dev/`.
3. Group observability guides near `observability_audit.md` and `logging.md`.

## Cross-links

- Parent audit: [PYPOST-690/60-tech-debt.md](../PYPOST-690/60-tech-debt.md) — R-P3-001
- Linked guide: [doc/prometheus_monitoring.md](../../doc/prometheus_monitoring.md)
- Documentation audit: [doc/dev/documentation_audit.md](../../doc/dev/documentation_audit.md)
