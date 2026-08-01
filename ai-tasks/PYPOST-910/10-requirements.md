# PYPOST-910: Optional retention-days on failure artifact

## Goals

Failure dumps uploaded from CI (`agent-e2e-failure-artifacts` and the
matrix-named twin) should expire on a predictable, explicit schedule so
the org does not keep triage zips for the full Actions default window
when a shorter retention is enough for debugging.

This debt comes from [PYPOST-874](https://pypost.atlassian.net/browse/PYPOST-874)
tech-debt item 2 (also noted under PYPOST-909 shortcuts).

## Programming Language

CI workflow (YAML) and Python pytest contract/doc guards
(`.cursor/lsr/do-python.md`, `.cursor/lsr/do-testing.md`). Developer
documentation in English Markdown (`.cursor/lsr/do-markdown.md`).

## User Stories

- As a **CI maintainer**, I want failure artifact uploads to declare an
  explicit retention period so storage does not silently follow a long
  org/repo default.
- As a **contributor**, I want docs to state how many days dumps remain
  downloadable so I know when an old red run’s zip may already be gone.
- As a **future maintainer**, I want an automated lock that the workflow
  and docs keep the same retention value, so the contract does not drift.

## Definition of Done

- Workflow upload step(s) for agent e2e failure artifacts set
  `retention-days` to an explicit positive integer.
- Docs note that retention value (and which jobs it applies to).
- Automated checks encode the retention contract (workflow and/or docs).
- Unticketed follow-ups (if any) live only in this task’s
  `60-tech-debt.md` (no Jira ticket creation in this run).

## Task Description

**Problem:** PYPOST-874 / PYPOST-909 ENABLE’d failure-only upload of
`artifacts/agent_e2e/` but omitted `retention-days`, so retention follows
the repository/org Actions default (commonly up to 90 days).

**Business need:** Cap how long masked failure dumps stay in Actions
storage while keeping them available long enough for typical PR triage.

### In Scope

- Set explicit `retention-days` on agent e2e failure artifact uploads in
  `.github/workflows/test.yml` (dedicated `agent-e2e` and main `test`
  matrix uploads from PYPOST-909).
- Align related mentions in `doc/dev` with the chosen value.
- Lock the contract with an automated check.

### Out of Scope

- Changing dump helper / makereport hook behavior (PYPOST-860).
- Changing upload gating (`if: failure()`) or artifact names.
- Changing retention for junit / coverage uploads (separate concern).
- Creating Jira Debt tickets (unticketed items only in `60-tech-debt.md`).
- Commit or Jira status transitions / worklog MCP writes (orchestrator).

## Functional Requirements

- FR1: Agent e2e failure artifact upload(s) set `retention-days` explicitly.
- FR2: Docs state the retention value for those failure artifacts.
- FR3: Automated checks encode the retention contract.
- FR4: Existing failure-only upload behavior and artifact names remain.
- FR5: Secrets policy from PYPOST-860 remains unchanged (masked dumps).

## Non-Functional Requirements

- NFR1: Retention must be shorter than or equal to the Actions maximum
  allowed by repo/org settings (1–90 days typical for public repos).
- NFR2: Reuse the existing pinned `actions/upload-artifact` pattern.
- NFR3: Docs stay in English; line length ≤ 100 where practical.
- NFR4: Do not break existing PYPOST-874 / PYPOST-909 upload locks.

## Constraints and Assumptions

- Parent debt: PYPOST-874 `60-tech-debt.md` item 2 → this ticket.
- Upload steps already exist on `agent-e2e` and main `test` matrix.
- Fourteen days is enough for typical PR / sprint triage of red runs.
- No commit / no Jira writes in this execution run.

## Main Entities (business)

| Entity | Role |
| --- | --- |
| Failure artifact dump | Masked UI snapshot + diagnostics on disk |
| Actions failure artifact | Downloadable zip from red CI runs |
| Retention window | Days the zip remains available for download |
| Contributor triage | Download dumps soon after a red run |

## Q&A

| Q | A |
| --- | --- |
| Why not keep the Actions default? | Defaults can be long; ticket asks for an explicit cap. |
| Why both jobs? | 874 + 909 both upload the same class of dumps; one policy. |
| Jira / commit in this run? | No — user directed; worklog blocks only for parent. |
