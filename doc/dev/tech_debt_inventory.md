# Technical Debt Inventory

## Overview

Top-down workflow steps 6 record technical debt in per-task markdown files. PYPOST-57
consolidates linked Jira follow-ups into a single inventory for sprint planning and audits.

**Master file:** [`ai-tasks/00-tech-debt-consolidated.md`](../../ai-tasks/00-tech-debt-consolidated.md)

## Regenerating the Inventory

```bash
python3 scripts/consolidate_tech_debt.py
```

The script scans:

- `ai-tasks/**/60-review.md`
- `ai-tasks/**/40-tech-debt.md`
- `ai-tasks/**/60-tech-debt.md`

It extracts `[PYPOST-N](https://pypost.atlassian.net/browse/PYPOST-N)` links, groups them by
source task folder, and rewrites the consolidated markdown with summary counts.

Run after closing a task that adds or updates tech-debt artifacts.

## Source Artifacts vs Inventory

| Artifact | Purpose |
| --- | --- |
| `ai-tasks/PYPOST-*/60-tech-debt.md` | Step 6 output for a single task |
| `ai-tasks/PYPOST-*/60-review.md` | Detailed review (older naming) |
| `ai-tasks/00-tech-debt-consolidated.md` | Cross-task index of Jira-linked debt |
| `doc/dev/tech-debt/PYPOST-*.md` | Developer-facing summaries for major audits |

The inventory does **not** replace per-task debt files; it indexes their Jira links.

## Markdown and Jira Hygiene

See [`tech-debt-diff.md`](../../tech-debt-diff.md) for conventions:

- Complete sentences before em-dash Jira links
- Readable Jira summaries (not mid-sentence fragments)
- Consistent linking style (prefer table format for dense items)

### Follow-up table format (PYPOST-582)

Use a three-column table for follow-ups — **no** `Jira:` prefix column, **no** stray
`PYPOST-N` text column:

```markdown
## Follow-up Tasks

| Priority | Description | Jira |
| --- | --- | --- |
| Medium | Refine expected/suspicious tags after worker/presenter audit | [PYPOST-665](https://pypost.atlassian.net/browse/PYPOST-665) |
```

Alternate layout (`Priority | Jira | Item`) is fine when the Jira key is the second column.

Normalize legacy files:

```bash
python3 scripts/standardize_debt_markdown.py
python3 scripts/consolidate_tech_debt.py
```

Export inventory JSON for tooling:

```bash
python3 scripts/consolidate_tech_debt.py --json scripts/debt_inventory.json
```

## Related

- Sprint 502 executes linked UI polish and cleanup debt items.
- Follow-ups: PYPOST-581 (bulk Jira summary cleanup), PYPOST-582 (markdown standardization).
