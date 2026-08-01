# PYPOST-931: Automate CI duration evidence capture

## Goals

Maintainers need a **repeatable way to refresh** agent-e2e overlap timing notes
from GitHub Actions without manually re-querying the API each revisit. Evidence
already lives in `doc/dev/testing.md` from
[PYPOST-907](https://pypost.atlassian.net/browse/PYPOST-907); optional
discoverability was closed under
[PYPOST-908](https://pypost.atlassian.net/browse/PYPOST-908). This Debt adds
the **automation / checklist** follow-up so future ENABLE/DEFER calls can update
numbers honestly.

**Business need:** Cheap, trustworthy refresh of CI cost evidence; avoid
invented timings; reduce duplicate manual scrape work.

**Source:** [PYPOST-907/60-tech-debt.md](../PYPOST-907/60-tech-debt.md) item 2;
related [PYPOST-908](https://pypost.atlassian.net/browse/PYPOST-908).

## Programming Language

Python script under `scripts/` (stdlib HTTP; `.cursor/lsr/do-python.md`) plus
English Markdown maintainer docs (`.cursor/lsr/do-markdown.md`). Repeatable
entry via Makefile target (workspace standard).

## User Stories

- As a **CI maintainer**, I want `make refresh-ci-duration-evidence` (or
  documented `gh` checklist) to print an updated evidence table from Actions,
  so I can paste honest numbers into `doc/dev/testing.md`.
- As a **contributor**, I want the refresh path documented next to the evidence
  section, so I do not rediscover API endpoints.
- As a **future maintainer**, I want a doc/check lock so the procedure stays
  linked from PYPOST-931 and the harness table.

## Definition of Done

- Script or documented checklist refreshes overlap evidence from the Actions
  API (workflow `Tests`, jobs `test` 3.11 + `agent-e2e`).
- Makefile target exposes the repeatable command; `make help` documents it.
- `doc/dev/testing.md` documents the refresh procedure (manual paste workflow).
- Automated lock verifies script + Makefile + doc anchors exist.
- Unit tests cover formatting/parsing without live network in default CI.
- Unticketed follow-ups (if any) listed only in `60-tech-debt.md`.
- No workflow selection change; no invented committed timings without maintainer
  paste.

## Task Description

### Problem

Evidence table in `testing.md` was captured manually (PYPOST-907). Follow-ups
listed optional automation (PYPOST-931). Maintainers still need a one-command
refresh before ENABLE threshold revisits (PYPOST-930).

### In Scope

- Python script querying GitHub Actions for recent runs with job `agent-e2e`.
- Markdown table output for maintainer paste into `doc/dev/testing.md`.
- Makefile target(s) and developer doc procedure.
- Contract tests / doc lock.

### Out of Scope

- Auto-committing refreshed numbers into git (maintainer reviews paste).
- ENABLE cost trim (PYPOST-930).
- Changing CI workflow selection.
- Creating Jira tickets, commits, transitions, or worklog writes (orchestrator).

## Functional Requirements

- FR1: Script fetches completed `Tests` workflow runs and extracts timings for
  main `test` 3.11 and job `agent-e2e` when present.
- FR2: Script prints a markdown evidence table (run number, durations, key
  steps) suitable for `testing.md`.
- FR3: Makefile exposes `refresh-ci-duration-evidence`; optional `--check`
  verifies doc procedure anchors.
- FR4: Developer docs describe refresh steps (script output → manual doc edit).
- FR5: Tests lock script/Makefile/doc wiring without requiring live API in CI.

## Non-Functional Requirements

- NFR1: Do not invent timings in committed docs during automation work.
- NFR2: Stdlib-only HTTP client; optional `GITHUB_TOKEN` for rate limits.
- NFR3: English docs; line length ≤ 100 where practical.

## Constraints and Assumptions

- Repo: `koctep/pypost`; workflow file `.github/workflows/test.yml` (`Tests`).
- Parent evidence: PYPOST-907 table remains source until maintainer refreshes.
- PYPOST-908 acceptance (discoverable notes) already met; this ticket completes
  refresh automation only.
- No commit / no Jira writes in this execution run.

## Main Entities (business)

| Entity | Role |
| --- | --- |
| CI duration evidence | Job/step timings for overlap judgment |
| Refresh script | Actions API → markdown table |
| Maintainer procedure | Run make target, paste into `testing.md` |
| Evidence docs | `doc/dev/testing.md` § Agent e2e CI double-run |

## Q&A

| Q | A |
| --- | --- |
| Why not auto-edit testing.md? | Avoid bot commits with stale/wrong numbers; maintainer reviews paste. |
| Does this close PYPOST-908? | 908 acceptance was published notes + discoverability; 931 adds refresh tooling only. |
| Jira / commit in this run? | No — orchestrator owns those. |
