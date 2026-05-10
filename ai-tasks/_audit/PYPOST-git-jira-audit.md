# PYPOST keys in git vs Jira status (Done)

Date: 2026-03-26

## Scope

- **Git:** unique `PYPOST-[0-9]+` from full history: commit subjects/bodies **and** patches
  (`git log --all -p`).
- **Jira:** MCP server `project-0-src-jira`, tool `jira_search`, JQL `key in (...)`, fields
  `key,status`, chunks of up to 50 keys.

## Counts

| Source | Count |
|--------|------:|
| Unique keys (messages only) | 80 |
| Unique keys (messages + `-p`) | 434 |

## Reconciliation (MCP `jira_search`, 2026-03-26)

For every git-derived key **except** `PYPOST-0`, Jira returned exactly one issue. Totals over
those **433** keys:

| Jira status | Count |
|-------------|------:|
| Done | 88 |
| To Do | 342 |
| In Progress | 3 |
| **Not Done** (To Do + In Progress) | **345** |

So **345 / 433** keys that exist in Jira are **not** Done (about **80%**).

## Keys not in Jira

| Key | Note |
|-----|------|
| `PYPOST-0` | Matches regex in diffs/text; `jira_search` with `key = PYPOST-0` returns **0**
  issues. |

## Done vs not Done

**Conclusion:** It is **not** true that every `PYPOST-*` seen in git history is **Done** in Jira.

Representative cases:

- **In Progress** in Jira, present in git: `PYPOST-418`, `PYPOST-419`, `PYPOST-420` (e.g.
  `950e0be`, `63df8e0` with `--grep='PYPOST-418'`).
- **Done** in Jira with implementation commits: `PYPOST-434` (e.g. `54f24b0` with
  `--grep='PYPOST-434'`).
- **To Do** in Jira, git mention via tech-debt / docs only: `PYPOST-281` — use
  `git log -S'PYPOST-281'` (e.g. `defc2a3`), not necessarily a subject-line `--grep` match.

So: keys appear in git for **implementation work**, **roadmaps/docs**, and **tech-debt
references** — not only for “closed” work. **Presence in git does not imply Done in Jira.**

## Tech-debt and “mention only” caveats

- **`git log --grep=KEY`** only finds the key in commit **subject/body**. Patches and inline
  references may require **`git log -S'KEY'`** (pickaxe).
- A key can appear in **planning or debt lists** while Jira stays **To Do** or **In Progress**.

## Pagination note

Some `jira_search` responses include `nextPageToken` / `isLast: false` even when the first page
already lists every issue for a bounded `key in (...)` chunk (≤50 keys). For open-ended JQL such
as `project = PYPOST AND status != Done`, use the API’s token-based pagination for a full list.

## References

- Key list (full): `/tmp/keys-from-git-all.txt`
- Key list (messages only): `/tmp/keys-from-git-messages.txt`
- JQL chunks used for MCP: `/tmp/jira_chunk_0.jql` … `/tmp/jira_chunk_8.jql`
