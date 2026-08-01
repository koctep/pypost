# PYPOST-1016: Sync unticketed tech debt from ai-tasks to Jira

## Programming language

Markdown (primary deliverable — per-task debt artifacts and inventory updates).

Python (secondary — only to regenerate the consolidated inventory with existing
tooling if needed; no new application feature code).

## Goals

Engineering needs every actionable tech-debt follow-up captured in top-down review
artifacts to be trackable in Jira as a Debt issue, with a durable browse link written
back into the source artifact. Without that sync, sprint planning and backlog hygiene
rely on scattered markdown that may never become work items.

A partial sync already created Debt issues
[PYPOST-799](https://pypost.atlassian.net/browse/PYPOST-799) through
[PYPOST-803](https://pypost.atlassian.net/browse/PYPOST-803) and left uncommitted
link updates plus a regenerated consolidated inventory. This story completes and
formalizes that work: verify nothing actionable remains unticketed, ensure source
artifacts carry the correct links, refresh the rollup inventory when appropriate,
and commit only the legitimate documentation and debt-link changes.

Related completed work: [PYPOST-57](https://pypost.atlassian.net/browse/PYPOST-57)
(consolidated inventory). Process skill:
`.claude/skills/tech-debt-jira-sync/SKILL.md`.

## User Stories

- As a **tech lead**, I want every actionable follow-up in
  `ai-tasks/*/60-tech-debt.md` to have a Jira Debt issue, so the backlog reflects
  real debt instead of silent markdown notes.
- As a **sprint planner**, I want Debt issues to carry appropriate priority and
  story points, so planning can weigh debt alongside feature work.
- As a **developer**, I want each ticketed item's source `60-tech-debt.md` to show
  a browse link to its Debt issue, so I can navigate from artifact to Jira without
  guessing keys.
- As a **maintainer**, I want accepted, out-of-scope, resolved, and already-linked
  items left alone, so the sync does not create duplicate or noise tickets.
- As a **maintainer**, I want the consolidated debt inventory updated after source
  links change, so the rollup stays consistent with per-task artifacts.
- As a **maintainer**, I want only legitimate artifact and debt-link updates
  committed (not local agent config or secrets), so the repository stays clean.

## Definition of Done

- [ ] All `ai-tasks/*/60-tech-debt.md` files have been scanned for unticketed
      actionable TD/D (or equivalent) follow-ups.
- [ ] Accepted, out-of-scope, resolved, deferred, and already-linked items are
      skipped; no duplicate Debt tickets for the same narrative.
- [ ] Every remaining actionable unticketed item has a Jira Debt issue with
      correct priority and story points (or an explicit, documented reason it was
      not ticketed).
- [ ] Browse links for newly created (and previously created-but-unlinked) Debt
      issues appear in the corresponding source `60-tech-debt.md` files — including
      verification that PYPOST-799–PYPOST-803 are reflected where required.
- [ ] Consolidated inventory (`ai-tasks/00-tech-debt-consolidated.md`) is
      regenerated from source artifacts when link updates warrant it (derived
      rollup only; not hand-edited as the source of truth).
- [ ] Completeness check confirms no actionable unticketed items remain after the
      sync (or lists intentional skips with rationale).
- [ ] Legitimate markdown / debt-link / inventory / audit-log updates are committed;
      local agent config and secrets are excluded from the commit.

## Task Description

**Problem:** Top-down reviews leave tech-debt follow-ups in per-task
`60-tech-debt.md` files. Some items never become Jira Debt issues, so they drop out
of planning. A partial sync already ticketed five items and updated several
artifacts locally, but that work is incomplete and uncommitted.

**Goal:** Finish the tech-debt → Jira sync so actionable follow-ups are ticketed,
source artifacts carry browse links, the optional consolidated inventory matches
those links, and the repository records the legitimate documentation updates.

**Scope (in):**

- Discover unticketed actionable follow-ups under `ai-tasks/*/60-tech-debt.md`.
- Skip items that are accepted, out of scope, resolved, deferred to an existing
  ticket, or already linked.
- Create missing Jira Debt issues with priority and story points aligned to the
  artifact.
- Write browse links back into each affected source `60-tech-debt.md`.
- Verify and finish link-back for the partial sync (PYPOST-799–PYPOST-803) and any
  other already-created keys that still lack source links.
- Optionally regenerate the consolidated debt inventory from sources.
- Retain or refresh an audit log of created tickets if useful for the run report.
- Commit only legitimate artifact / debt-link / inventory / audit updates.

**Scope (out):**

- Implementing or closing the underlying debt items themselves.
- Changing application runtime behavior or product features.
- Hand-editing the consolidated inventory as the place to add new ticket links
  (per-task `60-tech-debt.md` remains the source of truth).
- Committing local agent configuration, credentials, or unrelated working-tree
  changes.
- Expanding scan scope beyond `ai-tasks/*/60-tech-debt.md` unless a later decision
  widens it.

## Main Entities and Interactions

- **Debt follow-up** — an actionable item recorded in a task's tech-debt artifact
  (typically TD/D-style rows or explicit "no Jira yet" markers).
- **Source debt artifact** — `ai-tasks/<parent-task>/60-tech-debt.md`; authoritative
  place for the item text and its Jira browse link.
- **Debt issue** — a Jira issue of type Debt that tracks one (or a deduped set of)
  follow-ups for planning.
- **Browse link** — markdown link from the source artifact to the Debt issue's
  browse URL.
- **Consolidated inventory** — derived rollup of linked debt across tasks; rebuilt
  from sources, not the place new links are authored.
- **Audit log** — optional record of which Debt issues were created in a sync run
  and which source lines they map to.
- **Partial sync residue** — already-created keys PYPOST-799–PYPOST-803 plus
  uncommitted link and inventory updates that this story must verify and finish.

Interaction flow: scan source artifacts → classify each follow-up (ticket / skip /
already linked) → create missing Debt issues → write browse links into sources →
verify completeness (including partial-sync residue) → refresh derived inventory →
commit legitimate updates.

## Non-Functional Requirements

- **Traceability:** every newly ticketed item remains navigable from its source
  artifact via a browse link.
- **No duplicates:** identical debt narratives across files share one Debt issue
  with links from each relevant source line.
- **Conservative skips:** when classification is unclear, prefer skip (with
  documented rationale) over creating a questionable ticket.
- **Priority fidelity:** Debt issue priority matches the priority stated on the
  source item when present; otherwise a documented default applies.
- **Commit hygiene:** only documentation, debt-link, inventory, and audit artifacts
  related to this sync are committed; secrets and local agent config stay out.
- **Idempotence of outcome:** re-running the sync after completion finds no new
  actionable unticketed items (aside from newly written debt in future tasks).

## Q&A

**What is the business reason?**

Make review-captured debt plannable in Jira and keep source artifacts as the
linked source of truth.

**Is app feature work in scope?**

No — process and documentation sync only.

**What about the partial sync?**

Treat PYPOST-799–PYPOST-803 as already created; verify links, finish any missing
link-backs, then confirm no further actionable items remain.

**Source of truth for links?**

Each task's `60-tech-debt.md`. The consolidated file is a derived rollup.

**Must the inventory be regenerated?**

Yes when source links changed; optional only if a run produced no source-link
changes.

**What must not be committed?**

Local agent config, secrets, and unrelated working-tree changes.

**Related historical work?**

[PYPOST-57](https://pypost.atlassian.net/browse/PYPOST-57) delivered the
consolidated inventory; this story syncs unticketed items into Jira and keeps
artifacts linked.

**Open questions?**

None blocking Step 1; classification edge cases during the sync should prefer
skip with rationale.
