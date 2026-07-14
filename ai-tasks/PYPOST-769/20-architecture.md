# PYPOST-769: Architecture

## Approach

Documentation-only change. No application code.

## Target pattern

Sibling audits (`observability_audit.md`, `maintainability_audit.md`, `test_audit.md`) use:

```markdown
## Follow-up Work

<priority summary> in [60-tech-debt.md](...). Jira tickets are created by the sprint orchestrator.
```

Jira links live only in the parent audit task's `60-tech-debt.md` (PYPOST-684, PYPOST-685).

## Section replacement

| File | Remove | Add |
| --- | --- | --- |
| `architecture_audit.md` | `## Prioritized Recommendations` table (Jira column) | `## Follow-up Work` → PYPOST-684 debt |
| `security_audit.md` | `## Prioritized Recommendations` table (Jira column) | `## Follow-up Work` → PYPOST-685 debt |

## Out of scope

- Key Findings tables (remediated-status Jira refs remain for traceability)
- Parent `ai-tasks/PYPOST-684/60-tech-debt.md` or `PYPOST-685/60-tech-debt.md` content
- `documentation_audit.md` executive summary (D-007 partially remediated; full closure when
  all audits align)

## Verification

- `rg 'Prioritized Recommendations' doc/dev/architecture_audit.md doc/dev/security_audit.md`
  returns no matches
- `rg 'Follow-up Work' doc/dev/architecture_audit.md doc/dev/security_audit.md` returns two
  matches
