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
- Consistent linking style (prefer PYPOST-53 table format for dense items)

## Related

- Sprint 502 executes linked UI polish and cleanup debt items.
- Follow-ups: PYPOST-581 (bulk Jira summary cleanup), PYPOST-582 (markdown standardization).
