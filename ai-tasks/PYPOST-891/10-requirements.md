# PYPOST-891: Triage agent e2e audit findings and file fix Bugs

## Goals

Epic [PYPOST-888](https://pypost.atlassian.net/browse/PYPOST-888) needs a
clear handoff from discovery
([PYPOST-890](https://pypost.atlassian.net/browse/PYPOST-890) presentation
matrix) to product fix work: each distinct Send → response presentation
failure must become a focused Bug linked to the epic, or the epic must
explicitly record that the matrix found no product defects.

This story’s business goal is to **triage** the durable findings artifact
from PYPOST-890, **file Bugs only for distinct product failures**, link
those Bugs to the epic, and **comment on the epic** with the triage
outcome — including an explicit “no defects / won’t file” note when the
findings table is empty.

## Programming Language

Markdown / ticketing process (`.cursor/lsr/do-markdown.md`). No product
Python changes. Findings input and triage artifacts live under `ai-tasks/`.

## User Stories

- As an **epic owner (PYPOST-888)**, I want a triage summary that states
  whether the presentation matrix found product defects, so the audit
  epic can close discovery cleanly.
- As a **bug assignee**, I want one Bug per distinct failure (when any
  exist), linked to the epic, so fix work is scoped and trackable.
- As a **maintainer**, I want “won’t file” documented when findings are
  empty and HEAD is green, so empty backlog is intentional — not an
  oversight.
- As a **consumer of PYPOST-890**, I want triage to use
  `ai-tasks/PYPOST-890/findings.md` without re-running discovery by hand.

## Definition of Done

- Findings artifact from PYPOST-890 reviewed end-to-end.
- Distinct product failures mapped to Bug candidates (or zero candidates
  when the findings table is empty).
- Triage summary artifact written under `ai-tasks/PYPOST-891/` (e.g.
  `triage-summary.md`).
- When failures exist: Bugs created, linked to epic PYPOST-888, and
  referenced from the triage summary / findings triage column.
- When findings are empty: no Bugs filed; triage summary states **no
  product defects found / won’t file**.
- Epic PYPOST-888 receives a comment with the triage outcome (orchestrator
  Jira action if this run cannot call Jira MCP).
- No product / production code changes in this story.
- Brief `doc/dev/` note updated so maintainers can find the triage
  outcome from the matrix docs.

## Task Description

**Problem:** The presentation matrix may surface many failing cells.
Without triage, the epic has discovery but no clear fix backlog — or
worse, silence when there is nothing to fix.

**Business need:** Review matrix findings, create Bugs only for distinct
failures, link them to PYPOST-888, and comment on the epic. If findings
are empty (HEAD green), document that explicitly and do not invent Bugs.

### In Scope

- Review `ai-tasks/PYPOST-890/findings.md` (and related HEAD scan notes).
- Deduplicate / group distinct failure modes when rows exist.
- Produce `ai-tasks/PYPOST-891/triage-summary.md`.
- Create Bugs for distinct failures (when any); link to epic PYPOST-888.
- Epic comment with triage outcome.
- Dev-doc pointer to triage outcome.
- Orchestrator instructions when Jira MCP is unavailable in this run.

### Out of Scope

- Product Send / response presentation fixes (owned by resulting Bugs).
- Changing the presentation matrix or agent e2e harness (PYPOST-890).
- Replacing the PYPOST-889 lock or PYPOST-887 fix work.
- User-facing product docs (`doc/user/`).
- Inventing Bugs when findings are empty.

## Functional Requirements

- FR1: Read and triage `ai-tasks/PYPOST-890/findings.md`.
- FR2: Produce a durable triage summary under `ai-tasks/PYPOST-891/`.
- FR3: If findings rows exist, create one Bug per distinct failure mode
  (not one Bug per redundant cell unless modes differ), link each Bug to
  epic PYPOST-888, and record keys in the triage summary.
- FR4: If findings are empty (no product defects recorded), file **zero**
  Bugs and state **no product defects found / won’t file** in the triage
  summary.
- FR5: Epic PYPOST-888 must receive a comment summarizing triage
  (orchestrator executes if this agent cannot call Jira).
- FR6: No product code changes.
- FR7: Update brief `doc/dev/` discoverability for the triage outcome.

## Non-functional Requirements

- **Traceability:** Triage outcome must cite findings path and HEAD scan
  context from PYPOST-890.
- **Honesty on empty findings:** Empty table must not be treated as
  “still open” — document won’t-file explicitly.
- **Minimal noise:** Do not create placeholder or speculative Bugs.
- **Docs-only hygiene:** Markdown under `ai-tasks/` and `doc/dev/` only.

## Constraints and Assumptions

- Parent epic: [PYPOST-888](https://pypost.atlassian.net/browse/PYPOST-888).
- Findings source: [PYPOST-890](https://pypost.atlassian.net/browse/PYPOST-890)
  → `ai-tasks/PYPOST-890/findings.md`.
- **Critical context for this run:** Findings table is **empty**; PYPOST-890
  Step 3 HEAD scan reported **25/25 passed**. Triage outcome is therefore
  zero Bugs + explicit won’t-file note.
- This run may not call Jira MCP; leave epic comment (and any Bug creates
  if somehow needed) as orchestrator instructions.
- Commit / Jira Done transition are orchestrator Phase F duties.
- Sprint-task-runner autonomy: step user-approval gates are pre-approved.

## Main Entities and Interactions

| Entity | Role |
| --- | --- |
| Findings artifact | Durable failing-cell list from PYPOST-890 |
| Triage summary | Decision record: Bugs filed or won’t-file |
| Distinct failure | Group of cells sharing one product defect mode |
| Fix Bug | Trackable product work item under epic PYPOST-888 |
| Epic comment | Audit trail on PYPOST-888 for triage outcome |
| Presentation matrix | Discovery suite (unchanged by this story) |

Interaction overview:

1. Triage owner reads findings (and HEAD scan notes).
2. If rows exist → group distinct failures → file Bugs → link epic →
   update summary.
3. If empty → write won’t-file summary → skip Bug creates → epic comment.
4. Maintainers discover outcome via `doc/dev/` + triage artifact.

## Q&A

- Q: Why triage if findings are empty?
  A: The epic still needs an explicit close-out that discovery found no
  product defects — silence would look like unfinished triage.
- Q: Should we file a tracking Bug for “matrix is green”?
  A: No. Empty findings → won’t file. Do not invent work.
- Q: Does green matrix prove all presentation bugs forever?
  A: No. It proves the current 25-cell cartesian on HEAD. Future defects
  still go into findings + new Bugs under the epic process.
- Q: Can this story change product code to fix presentation?
  A: No. Out of scope; owned by Bugs created from non-empty findings.
- Q: Is Step 1 user approval required?
  A: Under sprint-task-runner autonomy, treated as pre-approved.
