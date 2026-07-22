# PYPOST-874: Optional CI upload of agent e2e failure artifacts

## Goals

When the dedicated agent e2e CI job fails, maintainers and contributors need
failure dumps (masked UI snapshot + diagnostics under `artifacts/agent_e2e/`)
downloadable from the GitHub Actions UI without SSH into the runner.

This debt comes from [PYPOST-860](https://pypost.atlassian.net/browse/PYPOST-860)
tech-debt: on-disk dumps are delivered; remote upload was documented as
optional and left as follow-up.

## Programming Language

CI workflow (YAML) and Python pytest contract/doc guards
(`.cursor/lsr/do-python.md`, `.cursor/lsr/do-testing.md`). Developer
documentation in English Markdown (`.cursor/lsr/do-markdown.md`).

## User Stories

- As a **CI maintainer**, I want a recorded **ENABLE upload vs DEFER**
  decision so we either ship failure-artifact upload for job `agent-e2e` or
  explicitly keep docs-only guidance with revisit criteria.
- As a **contributor**, I want failed agent-e2e runs to expose dumps in the
  Actions artifacts UI (if ENABLE), so I can triage UI state without runner
  access.
- As a **future maintainer**, I want docs and an automated lock that state
  whether upload is wired, so the contract does not silently drift.

## Definition of Done

- An explicit decision is recorded: **ENABLE** CI upload **or** **DEFER**
  with documentation — with rationale.
- Acceptance behavior of the chosen approach is locked by automated checks
  and/or updated developer docs as appropriate.
- Contributors can read one place that states whether `artifacts/agent_e2e/`
  is uploaded on `agent-e2e` failure and how to find it.
- Unticketed follow-ups (if any) live only in this task’s `60-tech-debt.md`
  (no Jira ticket creation in this run).

## Task Description

**Problem:** PYPOST-860 dumps failure artifacts to `artifacts/agent_e2e/` on
fixture assert fail. Job `agent-e2e` does not upload that directory, so CI
failures leave dumps only on the ephemeral runner workspace. Docs already
mention optional `actions/upload-artifact`.

**Business need:** Faster triage of agent e2e CI failures using existing
masked dumps, without expanding product scope beyond CI ergonomics.

### In Scope

- Research `.github/workflows` for `agent-e2e` and existing upload patterns.
- Decide ENABLE upload vs DEFER with rationale.
- Implement the chosen path (workflow change and/or docs + locks).
- Align related mentions in `doc/dev` with the decision.

### Out of Scope

- Changing dump helper / makereport hook behavior (PYPOST-860).
- Uploading unrelated CI outputs from other jobs unless ENABLE requires it.
- Creating Jira Debt tickets (unticketed items only in `60-tech-debt.md`).
- Commit or Jira status transitions (orchestrator owns those).

## Functional Requirements

- FR1: Record ENABLE vs DEFER decision with rationale in architecture.
- FR2: After delivery, docs state whether failure dumps are uploaded from
  job `agent-e2e` and how to download them (or why DEFER).
- FR3: Automated checks encode the chosen contract (workflow and/or docs).
- FR4: Secrets policy from PYPOST-860 remains: dumps stay masked; upload must
  not introduce cleartext secret packaging.

## Non-Functional Requirements

- NFR1: Prefer actionable triage over docs-only when upload cost/risk is low.
- NFR2: Upload only on failure when ENABLE (avoid storing dumps on green runs).
- NFR3: Docs stay in English; line length ≤ 100 where practical.
- NFR4: Reuse existing pinned `actions/upload-artifact` pattern from the
  main test job when ENABLE.

## Constraints and Assumptions

- Parent debt: PYPOST-860 `60-tech-debt.md` — optional CI upload follow-up
  → this ticket.
- Dumps already land under `artifacts/agent_e2e/` (gitignored) when hooked
  fixtures fail.
- Main `test` job already uploads junit/coverage; `agent-e2e` has no upload.
- No commit / no Jira writes in this execution run.

## Main Entities (business)

| Entity | Role |
| --- | --- |
| Job `agent-e2e` | Make-gate for agent e2e / env pack |
| Failure artifact dump | Masked UI snapshot + diagnostics on disk |
| CI artifact upload | Actions UI downloadable bundle on failure |
| Upload decision | ENABLE wiring vs DEFER docs-only |
| Contributor triage | Download dumps after a red CI run |

## Q&A

| Q | A |
| --- | --- |
| Why not always DEFER? | Parent left upload as optional debt; triage value is high and cost is low if upload runs only on failure. |
| Why not upload from the main matrix too? | Ticket scope is the dedicated `agent-e2e` job; matrix upload can be a follow-up. |
| Jira / commit in this run? | No — user directed; worklog block only for parent. |
