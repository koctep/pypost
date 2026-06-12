# PYPOST-57: Consolidate unresolved technical debt from ai-tasks

## Goals

Engineering leads need a single, trustworthy view of technical debt captured in top-down
workflow artifacts (`60-review.md`, `40-tech-debt.md`, `60-tech-debt.md`) and the Jira
backlog items created from them. Today debt is scattered across hundreds of files; summaries
in Jira are often truncated mid-sentence, and a few review findings lack Jira links.

## User Stories

- As a **tech lead**, I want a consolidated inventory so I can prioritize sprint work
  without opening every `ai-tasks/PYPOST-*` folder.
- As a **developer**, I want markdown debt bullets to read as complete sentences with
  Jira links on coherent lines.
- As a **sprint planner**, I want every review finding that should be tracked to have a
  corresponding Jira Debt issue.

## Definition of Done

- [x] `ai-tasks/00-tech-debt-consolidated.md` lists all linked Jira issues by source task.
- [x] Reproducible generator script committed (`scripts/consolidate_tech_debt.py`).
- [x] Known broken markdown wraps from `tech-debt-diff.md` remediated in source files.
- [x] Previously unlinked PYPOST-52 INFO finding has a Jira follow-up.
- [x] Developer documentation describes how to regenerate and use the inventory.
- [x] Sprint 502 backlog summaries readable without opening descriptions (spot-check).

## Task Description

Aggregate debt from `ai-tasks/**/60-review.md` and `ai-tasks/**/*tech-debt.md`, produce the
master inventory referenced in the PYPOST-57 Jira description, and apply hygiene fixes
identified in `tech-debt-diff.md`. No production code changes beyond the inventory script.

## Q&A

| Question | Answer |
| --- | --- |
| Which files are in scope? | All `60-review.md`, `40-tech-debt.md`, `60-tech-debt.md` under `ai-tasks/`. |
| Fix every Jira summary? | Fix sprint 502 debt items; full backlog cleanup is follow-up. |
| Programming language | Python (inventory script); Markdown (artifacts). |
