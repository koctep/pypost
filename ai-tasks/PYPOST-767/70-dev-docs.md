# PYPOST-767: Dev Docs Summary

## Updated files

| File | Changes |
| --- | --- |
| `doc/dev/documentation_audit.md` | Hub table row for Dependencies (691); eight-audit copy; hub Related Audits |
| `doc/dev/architecture_audit.md` | Standardized Related Audits footer |
| `doc/dev/security_audit.md` | Standardized Related Audits footer |
| `doc/dev/test_audit.md` | Standardized Related Audits footer |
| `doc/dev/maintainability_audit.md` | Standardized Related Audits footer |
| `doc/dev/observability_audit.md` | Standardized Related Audits footer |
| `doc/dev/performance_audit.md` | Standardized Related Audits footer |
| `doc/dev/dependencies_audit.md` | Standardized Related Audits footer |

## Maintainer workflow

When a new Code Audit summary lands under `doc/dev/`:

1. Add a row to `documentation_audit.md` § Code Audit Hub.
2. Add the new audit link to each sibling's `## Related Audits` footer (and include all siblings
   in the new file's footer).
3. Update the eight-audit count in `documentation_audit.md` intro if the epic grows again.

## Cross-links

- Parent audit: [documentation_audit.md](../documentation_audit.md), finding D-007 / R-P2-001
- Source task: [PYPOST-690/60-tech-debt.md](../../ai-tasks/PYPOST-690/60-tech-debt.md)
