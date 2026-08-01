# PYPOST-933: Capture live Artifacts UI proof when red run exists

## Goals

When a failing CI run publishes `agent-e2e-failure-artifacts*`, maintainers
should record honest proof (notes and optional screenshot path) in the
PYPOST-911 notes stub and flip documentation status from DEFER to CAPTURED.
When no qualifying red run exists, continued DEFER with an updated scan record
is the correct delivery — not invented screenshots.

Source: [PYPOST-911](https://pypost.atlassian.net/browse/PYPOST-911)
`60-tech-debt.md` follow-up item 1.

## Programming Language

Python pytest contract/doc guards (`.cursor/lsr/do-python.md`,
`.cursor/lsr/do-testing.md`). Developer documentation in English
Markdown (`.cursor/lsr/do-markdown.md`).

## User Stories

- As a **CI maintainer**, when a red run uploads agent e2e failure dumps, I
  want structured notes (and optional screenshot path) recorded so triage docs
  match observed Actions UX.
- As a **maintainer**, when no qualifying red run exists yet, I want the
  re-check scan documented so DEFER remains honest and the checklist stays
  current.
- As a **future maintainer**, I want an automated lock that the PYPOST-933
  re-scan was performed and recorded.

## Definition of Done

- Public Actions re-scanned for failed runs with `agent-e2e-failure-artifacts*`.
- Either: **CAPTURED** proof in `ai-tasks/PYPOST-911/live-proof-notes.md` and
  docs status updated — **or** continued **DEFER** with documented scan
  evidence and checklist intact.
- No invented / fake screenshots or run URLs.
- Automated check encodes the re-scan record.
- Parent PYPOST-911 lock and sibling upload locks remain green.

## Task Description

**Problem:** PYPOST-911 deferred live Artifacts UI proof because no qualifying
public artifact existed. This follow-up attempts capture when a red run exists.

**Business need:** Close the optional proof loop honestly — capture when
possible; otherwise document why DEFER continues.

### In Scope

- Re-check public Actions runs (GitHub REST API; `gh` if available).
- If qualifying artifact found: fill capture record, mark CAPTURED, update docs.
- If not found: update scan notes, keep DEFER, lock re-scan record.
- Align `doc/dev` scan date / PYPOST-933 reference.

### Out of Scope

- Forcing a deliberate CI failure to generate artifacts.
- Inventing fake screenshots or claiming proof that does not exist.
- Changing dump helper, upload gating, artifact names, or retention.
- Git commit or Jira transitions (orchestrator handles separately).

## Functional Requirements

- FR1: Re-scan public Actions for qualifying failure artifacts.
- FR2: CAPTURED or continued DEFER recorded in `live-proof-notes.md`.
- FR3: Docs reflect current proof status (DEFER or CAPTURED).
- FR4: Automated lock encodes PYPOST-933 re-scan anchors.
- FR5: Existing PYPOST-911 / 874 / 909 / 910 locks remain green.

## Non-Functional Requirements

- NFR1: Do not invent screenshots or fabricate run URLs.
- NFR2: Prefer public Actions evidence; otherwise honest DEFER.
- NFR3: Docs stay in English; line length ≤ 100 where practical.
- NFR4: No application runtime change.

## Constraints and Assumptions

- Parent: PYPOST-911 deferred proof with checklist in place.
- Qualifying red run may still not exist on the public repo.
- `gh` CLI may be unavailable; GitHub REST API is acceptable evidence.

## Main Entities (business)

| Entity | Role |
| --- | --- |
| Qualifying red run | Failed CI run that uploaded agent e2e failure artifact |
| Capture record | Structured notes in `live-proof-notes.md` |
| Re-scan evidence | Documented API scan showing artifact presence/absence |
| Continued DEFER | Honest status when no qualifying run exists |

## Q&A

| Q | A |
| --- | --- |
| What if still no artifact? | Continued DEFER + updated scan notes; SAFE TO CLOSE. |
| Fake screenshot OK? | No — same policy as PYPOST-911. |
| Force a CI fail? | Out of scope. |
