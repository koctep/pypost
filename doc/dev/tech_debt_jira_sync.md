# Tech Debt → Jira Sync

## Overview

Top-down reviews record follow-ups in per-task `ai-tasks/*/60-tech-debt.md`.
Actionable items need a Jira **Debt** issue and a browse link written back into
that source file so sprint planning sees real backlog work instead of silent
markdown notes.

The authoritative procedure is the agent skill
[`.claude/skills/tech-debt-jira-sync/SKILL.md`](../../.claude/skills/tech-debt-jira-sync/SKILL.md).
This page is a short developer map; do not duplicate the skill's classification
tables or create-issue field lists here.

Related: [Tech Debt Inventory](tech_debt_inventory.md) (derived rollup),
[PYPOST-1016](https://pypost.atlassian.net/browse/PYPOST-1016).

## Source of truth

| Artifact | Role |
| --- | --- |
| `ai-tasks/<TASK>/60-tech-debt.md` | **Source of truth** — scan / write links |
| `ai-tasks/00-tech-debt-consolidated.md` | Derived rollup — do not hand-edit tickets |
| `scripts/untracked_debt_tickets_created.json` | Optional audit log of a sync run |

Never treat the consolidated inventory as input for discovering unticketed debt
or as the place to record new Jira links.

## Architecture (high level)

1. **Discover** — scan `ai-tasks/*/60-tech-debt.md` for unticketed actionable
   rows (TD/D tables, `Jira: _none_`, "no Jira yet", and similar markers).
2. **Classify** — ticket, skip (accepted / out of scope / resolved /
   already-tracked), or already linked. Prefer skip when unsure.
3. **Create** — Debt issues via the `jira-create-issue` skill (estimate → create
   with story points). Do not call raw `jira_create_issue` or blind batch create.
4. **Link back** — write a browse link such as
   `` `[PYPOST-N](https://pypost.atlassian.net/browse/PYPOST-N)` `` into the
   matching source `60-tech-debt.md` line.
5. **Roll up (optional)** — regenerate the consolidated inventory when links
   changed.

Single-task close flows can use Phase D of
[sprint-task-runner](../../.claude/skills/sprint-task-runner/SKILL.md) instead
of a full backlog scan.

## Usage / how to re-run

Ask an agent (or run the skill yourself) with a prompt such as:

> Sync unticketed tech debt from `ai-tasks/*/60-tech-debt.md` to Jira using
> `tech-debt-jira-sync`.

Checklist (details in the skill):

1. Read Atlassian MCP tool schemas before calling.
2. Scan all `ai-tasks/*/60-tech-debt.md`; dedupe identical narratives.
3. Create Debt issues via `jira-create-issue`; verify at least one new key with
   `jira_get_issue` before editing markdown.
4. Update each source `60-tech-debt.md` in place with browse links.
5. Optionally regenerate the rollup and refresh the audit JSON.
6. Report counts: scanned, created, skipped, files updated, key range, SP sum.

### Consolidate script

After source link-backs change:

```bash
python3 scripts/consolidate_tech_debt.py
```

Rebuilds `ai-tasks/00-tech-debt-consolidated.md` from artifacts. See
[Tech Debt Inventory](tech_debt_inventory.md) for scan paths and `--json`.

### Audit JSON

Optional run log (not a substitute for markdown link-backs):

```text
scripts/untracked_debt_tickets_created.json
```

Typical entries: `key`, `file`, `line`, `parent`, `summary`, `story_points`.

## Configuration

Uses the same Atlassian MCP / Jira project placeholders as other Jira skills
(see [jira-sprint-planning](../../.claude/skills/jira-sprint-planning/SKILL.md)):
project key, Debt issue type, and base browse URL. No application env vars.

## Troubleshooting

| Symptom                         | What to do                                              |
| ------------------------------- | ------------------------------------------------------- |
| Duplicate Debt tickets          | Check browse link / "tracked under PYPOST-N"; dedupe    |
| Rollup missing new keys         | Confirm links in `60-tech-debt.md`, then consolidate    |
| Noise tickets for waived items  | Skip accepted / out-of-scope / resolved / deferred rows |
| Markdown updated, issue missing | Call `jira_get_issue` before link-back                  |
| Wrong file edited               | Never add tickets only in consolidated inventory        |

## Related

- Skill: [tech-debt-jira-sync](../../.claude/skills/tech-debt-jira-sync/SKILL.md)
- Create with estimate: [jira-create-issue](../../.claude/skills/jira-create-issue/SKILL.md)
- Inventory / consolidate: [tech_debt_inventory.md](tech_debt_inventory.md)
- Markdown hygiene: [`tech-debt-diff.md`](../../tech-debt-diff.md)
