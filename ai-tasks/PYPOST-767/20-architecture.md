# PYPOST-767: Architecture

## Approach

Documentation-only change. No application code.

## Hub table

Extend `documentation_audit.md` § Code Audit Hub with:

| Dependencies (691) | `dependencies_audit.md` | `ai-tasks/PYPOST-691/30-audit-report.md` |

Update count references from seven to eight audits in the executive summary.

## Related Audits footer (standard template)

Append to each of the eight sibling `*_audit.md` files:

```markdown
## Related Audits

Sibling Code Audit summaries — hub:
[documentation_audit.md § Code Audit Hub](documentation_audit.md#code-audit-hub).

- [<title> (PYPOST-NNN)](<file>.md)
  … seven siblings, omitting self …
```

**Order:** 684 → 685 → 686 → 687 → 688 → 689 → 690 → 691 (hub table order).

**Hub page (`documentation_audit.md`):** Related Audits lists all seven siblings (self is the
hub); no self-link.

## Files touched

| File | Change |
| --- | --- |
| `doc/dev/documentation_audit.md` | Hub row, copy, hub Related Audits |
| `doc/dev/architecture_audit.md` | Related Audits footer |
| `doc/dev/security_audit.md` | Related Audits footer (keep policy `## Related`) |
| `doc/dev/test_audit.md` | Related Audits footer |
| `doc/dev/maintainability_audit.md` | Related Audits footer |
| `doc/dev/observability_audit.md` | Related Audits footer (before Related Commands) |
| `doc/dev/performance_audit.md` | Related Audits footer (before Related Commands) |
| `doc/dev/dependencies_audit.md` | Related Audits footer (after Related Work) |

## Out of scope

- `solid_audit.md` footer (legacy audit, separate from Code Audit epic 684–691)
- PYPOST-769 follow-up table standardization (inline Jira in dev summaries)
- Expanding `doc/dev/README.md` TOC (PYPOST-765)
