# PYPOST-911: Optional live CI proof of Artifacts UI download

## Goals

Maintainers should know whether the GitHub Actions Artifacts UI actually
exposes a downloadable agent e2e failure dump after a red run — or, when
no live failing run is available, exactly how to capture that one-time
proof later without inventing screenshots.

This optional debt comes from
[PYPOST-874](https://pypost.atlassian.net/browse/PYPOST-874)
tech-debt item 3 (live CI proof of Artifacts UI download).

## Programming Language

Python pytest contract/doc guards (`.cursor/lsr/do-python.md`,
`.cursor/lsr/do-testing.md`). Developer documentation in English
Markdown (`.cursor/lsr/do-markdown.md`).

## User Stories

- As a **CI maintainer**, I want a recorded screenshot or structured
  notes from a real failing Actions run showing a downloadable
  `agent-e2e-failure-artifacts` (or matrix twin) zip, so triage docs
  match observed UX.
- As a **contributor**, when live proof is not yet available, I want a
  clear DEFER how-to and checklist (what to capture, where to store
  notes) so I can complete the proof honestly later.
- As a **future maintainer**, I want an automated lock that the
  procedure stays documented and does not drift out of `doc/dev`.

## Definition of Done

- Either: real proof (screenshot and/or notes) from a failing Actions
  run showing a downloadable agent e2e failure artifact — **or**
- Documented honest **DEFER** with maintainer how-to + capture
  checklist, procedure locked in docs, and optional ticket marked safe
  to close with deferred proof.
- No invented / fake screenshots.
- Automated check encodes the documented procedure/contract.
- Unticketed follow-ups (if any) live only in this task’s
  `60-tech-debt.md` (no Jira ticket creation in this run).

## Task Description

**Problem:** PYPOST-874 / PYPOST-909 ENABLE’d failure-only upload of
`artifacts/agent_e2e/`, but nobody has yet recorded a one-time live
proof that the Actions Artifacts UI lists a downloadable dump after a
real red run.

**Business need:** Confidence that the documented download path matches
UI reality; if proof cannot be captured now, leave a reliable procedure
for the next maintainer who sees a qualifying red run.

### In Scope

- Attempt to obtain proof from existing public Actions runs (API / UI).
- If unavailable: document DEFER + how-to + checklist; place notes stub.
- Align related mentions in `doc/dev`.
- Lock the procedure/contract with an automated check.

### Out of Scope

- Changing dump helper / makereport hook behavior (PYPOST-860).
- Changing upload gating, artifact names, or retention (874/909/910).
- Forcing a deliberate CI failure solely to generate artifacts.
- Inventing fake screenshots or claiming proof that does not exist.
- Creating Jira Debt tickets (unticketed items only in `60-tech-debt.md`).
- Commit or Jira status transitions / worklog MCP writes (orchestrator).

## Functional Requirements

- FR1: Live proof is captured from a real failing run **or** DEFER is
  documented with how-to and checklist.
- FR2: Docs state what to capture and where to put notes/screenshots.
- FR3: Automated checks encode the procedure/contract anchors.
- FR4: Existing failure-upload behavior and artifact names remain.
- FR5: Secrets policy from PYPOST-860 remains unchanged.

## Non-Functional Requirements

- NFR1: Do not invent screenshots or fabricate run URLs.
- NFR2: Prefer public Actions evidence when available; otherwise DEFER.
- NFR3: Docs stay in English; line length ≤ 100 where practical.
- NFR4: Do not break existing PYPOST-874 / 909 / 910 upload locks.

## Constraints and Assumptions

- Parent debt: PYPOST-874 `60-tech-debt.md` item 3 → this ticket.
- Upload steps already exist on `agent-e2e` and main `test` matrix.
- A qualifying red run may not exist on the public repo yet.
- No commit / no Jira writes in this execution run.

## Main Entities (business)

| Entity | Role |
| --- | --- |
| Failure artifact dump | Masked UI snapshot + diagnostics on disk |
| Actions failure artifact | Downloadable zip from red CI runs |
| Artifacts UI proof | Screenshot/notes confirming download is listed |
| Maintainer checklist | What to capture and where to store it |
| Deferred proof | Honest DEFER until a qualifying red run exists |

## Q&A

| Q | A |
| --- | --- |
| Why optional? | Upload already ENABLE’d; live UI proof is confirmation only. |
| Fake screenshot OK? | No — inventing proof is forbidden. |
| Force a CI fail? | Out of scope; wait for natural red run or maintainer staged fail. |
| Jira / commit in this run? | No — user directed; worklog blocks only for parent. |
