# PYPOST-747 — Architecture

## Approach

Documentation-only deliverable. No code modules or runtime behavior changes.

## Document Structure

```text
doc/dev/logging.md
├── Overview and log format (stdlib basicConfig)
├── Naming convention rules (snake_case event + key=value)
├── Domain event catalog (tables by functional area)
├── Legacy migration guide (3 patterns + checklist)
├── Sensitive data cross-ref
└── Inventory maintenance commands
```

## Cross-Links

| File | Change |
| --- | --- |
| `doc/dev/observability_audit.md` | Link to `logging.md` as canonical naming reference |
| `doc/dev/README.md` | Add TOC entry under Audits |

## Source Material

- [PYPOST-688/30-audit-report.md](../PYPOST-688/30-audit-report.md) — O-002 event naming
- Ripgrep inventory of `pypost/` logger calls (2026-07-14)
