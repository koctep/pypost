# PYPOST-909: Optional upload from main test matrix on failure

## Goals

When agent e2e scenarios fail inside the main GitHub Actions `test` matrix
(Python 3.11 / 3.13, `-m "not slow"`), maintainers need the same masked
failure dumps under `artifacts/agent_e2e/` downloadable from the Actions
UI — not only from the dedicated `agent-e2e` job (PYPOST-874).

This debt comes from [PYPOST-874](https://pypost.atlassian.net/browse/PYPOST-874)
tech-debt: matrix failures (especially 3.13) left dumps only on the
ephemeral runner.

## Programming Language

CI workflow (YAML) and Python pytest contract/doc guards
(`.cursor/lsr/do-python.md`, `.cursor/lsr/do-testing.md`). Developer
documentation in English Markdown (`.cursor/lsr/do-markdown.md`).

## User Stories

- As a **CI maintainer**, I want the main `test` matrix to upload
  `artifacts/agent_e2e/` on job failure when dumps exist, so 3.11/3.13
  matrix reds are triagable without runner SSH.
- As a **contributor**, I want a distinct per-matrix-version Actions
  artifact name so I can download the right Python version’s dumps.
- As a **future maintainer**, I want docs and an automated lock that
  state matrix upload is wired, so the contract does not silently drift.

## Definition of Done

- Main matrix job uploads `artifacts/agent_e2e/` on failure when dumps
  exist (`if: failure()`, missing path ignored).
- Docs state that both `agent-e2e` and the main `test` matrix upload
  failure dumps, including artifact naming for the matrix.
- Automated checks encode the matrix upload contract (workflow and/or
  docs).
- Unticketed follow-ups (if any) live only in this task’s
  `60-tech-debt.md` (no Jira ticket creation in this run).

## Task Description

**Problem:** PYPOST-874 ENABLE’d failure upload only on job `agent-e2e`.
The main `test` matrix still runs the same agent e2e pack via
`-m "not slow"` (intentional double-run, PYPOST-873) but does not upload
`artifacts/agent_e2e/`. Matrix-only failures (e.g. 3.13) leave dumps on
the runner only.

**Business need:** Faster triage of agent e2e failures on every matrix
cell that can produce dumps, without expanding product scope beyond CI
ergonomics.

### In Scope

- Add failure-only upload of `artifacts/agent_e2e/` to the main `test`
  job in `.github/workflows/test.yml`.
- Align related mentions in `doc/dev` with matrix upload.
- Lock the contract with an automated check.

### Out of Scope

- Changing dump helper / makereport hook behavior (PYPOST-860).
- Changing the dedicated `agent-e2e` job upload (already ENABLE’d).
- Creating Jira Debt tickets (unticketed items only in `60-tech-debt.md`).
- Commit or Jira status transitions (orchestrator owns those).

## Functional Requirements

- FR1: On main `test` job failure, upload `artifacts/agent_e2e/` when
  the path exists; ignore when missing.
- FR2: Artifact name must distinguish matrix Python versions.
- FR3: Docs state matrix upload behavior and how to download dumps.
- FR4: Automated checks encode the matrix upload contract.
- FR5: Secrets policy from PYPOST-860 remains: dumps stay masked;
  upload must not introduce cleartext secret packaging.

## Non-Functional Requirements

- NFR1: Upload only on failure (avoid storing dumps on green runs).
- NFR2: Reuse the existing pinned `actions/upload-artifact` pattern.
- NFR3: Docs stay in English; line length ≤ 100 where practical.
- NFR4: Do not break existing `agent-e2e` upload (PYPOST-874).

## Constraints and Assumptions

- Parent debt: PYPOST-874 `60-tech-debt.md` item 1 → this ticket.
- Dumps already land under `artifacts/agent_e2e/` when hooked fixtures
  fail during the matrix pytest run.
- Main `test` job already uploads junit/coverage with
  `if: always()`; failure dumps should use `if: failure()`.
- No commit / no Jira writes in this execution run.

## Main Entities (business)

| Entity | Role |
| --- | --- |
| Job `test` (matrix) | Main pytest gate including agent e2e via `-m "not slow"` |
| Job `agent-e2e` | Dedicated make gate (upload already ENABLE’d) |
| Failure artifact dump | Masked UI snapshot + diagnostics on disk |
| Matrix CI artifact | Per-Python-version Actions downloadable bundle on failure |
| Contributor triage | Download dumps after a red matrix run |

## Q&A

| Q | A |
| --- | --- |
| Why matrix upload if `agent-e2e` already uploads? | Matrix covers 3.13 and can fail independently; double-run is intentional. |
| Why failure-only? | Green runs have no dumps worth storing; matches PYPOST-874 NFR. |
| Jira / commit in this run? | No — user directed; worklog block only for parent. |
