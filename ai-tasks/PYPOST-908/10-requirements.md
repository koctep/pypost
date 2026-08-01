# PYPOST-908: Optional CI duration evidence for double-run

## Goals

Maintainers need **discoverable, honest timing notes** for the intentional
agent-e2e CI overlap (main `test` matrix + dedicated `agent-e2e` job) so the
next ENABLE/DEFER call is grounded in evidence, not gut feel.

[PYPOST-907](https://pypost.atlassian.net/browse/PYPOST-907) already published
Actions duration evidence and deferred ENABLE. This Debt closes the optional
evidence acceptance from [PYPOST-873](https://pypost.atlassian.net/browse/PYPOST-873)
by ensuring those notes remain linked from developer docs and task artifacts —
**without inventing timings** and **without new automation** (automation may
later live under [PYPOST-931](https://pypost.atlassian.net/browse/PYPOST-931)).

**Business need:** Cheap, trustworthy evidence for CI cost decisions; avoid
duplicate scrape work when numbers already exist in docs.

**Source:** [PYPOST-908](https://pypost.atlassian.net/browse/PYPOST-908).

## Programming Language

Python pytest contract/doc guards and English Markdown developer docs
(`.cursor/lsr/do-python.md`, `.cursor/lsr/do-testing.md`,
`.cursor/lsr/do-markdown.md`).

## User Stories

- As a **CI maintainer**, I want job-duration / overlap-cost notes easy to
  find from docs (and this ticket’s artifacts), so I can re-judge ENABLE
  without rediscovering Actions history.
- As a **contributor**, I want a stable link from the double-run section to
  PYPOST-908, so the evidence ticket and published numbers stay connected.
- As a **future maintainer**, I want automation of refreshes deferred to the
  existing follow-up (PYPOST-931), so this ticket does not invent a scraper.

## Definition of Done

- Timing notes (job durations / overlap cost) are present in `doc/dev` (reuse
  PYPOST-907 numbers; no invented timings).
- PYPOST-908 is discoverable from those docs (cross-link) and from
  `ai-tasks/PYPOST-908/*` (cite the same evidence).
- Automated lock keeps PYPOST-908 linked from the double-run / evidence docs.
- No new CI selection change; no new duration-scrape automation in this task.
- Unticketed follow-ups (if any) listed only in `60-tech-debt.md` for the
  orchestrator (this run must not create Jira issues).

## Task Description

### Problem

Optional acceptance from the PYPOST-873 line: capture timing notes for
agent-e2e overlap and link them from docs or the ENABLE path. Evidence was
published under PYPOST-907, but PYPOST-908 still needs its own artifacts and
stronger discoverability so acceptance is clearly satisfied.

### In Scope

- Cite and lock existing Actions timing notes (from PYPOST-907 / `testing.md`).
- Cross-link PYPOST-908 from `doc/dev` double-run / evidence sections.
- Extend the dual-run doc lock for PYPOST-908 discoverability.
- Record evidence citation in this task’s architecture / roadmap artifacts.

### Out of Scope

- Inventing or approximating timings not already published.
- Automating Actions API scrape (PYPOST-931).
- ENABLE cost trim (PYPOST-930 / threshold in `testing.md`).
- Creating Jira tickets, commits, transitions, or worklog writes (orchestrator).

## Functional Requirements

- FR1: Evidence notes (job durations / overlap interpretation) remain in
  developer docs and are cited from this task’s artifacts.
- FR2: PYPOST-908 is cross-linked from the double-run / evidence docs path.
- FR3: Automated checks encode discoverability of PYPOST-908 from those docs.
- FR4: No workflow selection change; DEFER-after-evidence contract stays.

## Non-Functional Requirements

- NFR1: Do not invent timing numbers; only cite existing published evidence.
- NFR2: Prefer documenting/locking over new automation.
- NFR3: Docs in English; line length ≤ 100 where practical.

## Constraints and Assumptions

- Parent line: PYPOST-873 → PYPOST-907 (evidence + DEFER) → this ticket.
- Related: PYPOST-931 may absorb refresh automation; PYPOST-930 for ENABLE.
- No commit / no Jira writes in this execution run.

## Main Entities (business)

| Entity | Role |
| --- | --- |
| CI duration evidence | Published job/step timings for overlap judgment |
| Double-run docs | `testing.md` / `agent_e2e.md` maintainer entry points |
| Evidence ticket (908) | Optional capture + discoverability acceptance |
| ENABLE threshold | When DEFER should become ENABLE (owned by 907 docs) |
| Automation follow-up | PYPOST-931 — refresh scrape (out of scope here) |

## Q&A

| Q | A |
| --- | --- |
| Why not scrape Actions again? | Numbers already published; inventing/duplicating is waste; 931 owns automation. |
| Why not close as duplicate of 907? | 908 acceptance is “notes linked from docs”; lock + artifacts make that explicit. |
| Jira / commit in this run? | No — orchestrator owns those; Phase D must not create issues. |
