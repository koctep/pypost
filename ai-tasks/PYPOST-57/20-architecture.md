# PYPOST-57: Architecture

## Approach

1. **Scan** — Walk `ai-tasks/` for the three debt artifact filenames.
2. **Extract** — Parse `[PYPOST-N](url)` links; derive a short summary from the same line
   or preceding context.
3. **Aggregate** — Group unique Jira keys by source task (`PYPOST-*` parent folder).
4. **Emit** — Write `ai-tasks/00-tech-debt-consolidated.md` with summary metrics and tables.
5. **Hygiene** — Fix known broken wraps; create Jira for any structured review item still
   missing a link.

## Components

| Component | Role |
| --- | --- |
| `scripts/consolidate_tech_debt.py` | CLI entry point; idempotent regeneration |
| `ai-tasks/00-tech-debt-consolidated.md` | Human-readable master inventory |
| `doc/dev/tech_debt_inventory.md` | Developer guide for inventory usage |
| Jira `Debt` issues | Execution backlog (sprint 502 and beyond) |

## Data Flow

```text
ai-tasks/**/{60-review,40-tech-debt,60-tech-debt}.md
        │
        ▼
consolidate_tech_debt.py  ──►  00-tech-debt-consolidated.md
        │
        ▼
Jira backlog (linked PYPOST-* keys) ◄── sprint grooming / execution
```

## Out of Scope

- Resolving debt items (implementation belongs to linked tickets).
- Bulk-rewriting all 480+ Jira summaries (tracked as follow-up).
- De-duplicating near-identical narratives across source tasks (PO decision).
