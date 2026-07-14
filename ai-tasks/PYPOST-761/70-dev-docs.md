# PYPOST-761 — Dev Docs

## Updated files

| File | Change |
| --- | --- |
| `doc/prometheus_monitoring.md` | Inventory 33 instruments; HTTP table row for render duration histogram |
| `doc/dev/performance_audit.md` | Template Rendering section — P3 gap closed (PYPOST-761) |

## Maintainer notes

When adding render-path labels, keep `render_path` cardinality low (`runtime`, `hover`, `curl`).
Duration is recorded in `render_with_jinja` only — do not duplicate timing in
`TemplateService.render_string`.

Verify registration count after metric changes:

```bash
rg 'Counter\(|Histogram\(|Gauge\(' pypost/core/metrics_registry.py | wc -l
```
