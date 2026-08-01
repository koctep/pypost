# PYPOST-930: ENABLE CI cost trim when ENABLE threshold met

## Goals

[PYPOST-907](https://pypost.atlassian.net/browse/PYPOST-907) published CI duration
evidence and an ENABLE threshold but chose **DEFER after evidence**. This Debt
revisits that threshold: if criteria are met, **ENABLE** the cost trim (exclude
`agent_e2e` from the main matrix with a 3.13 coverage plan); if not, record
**continued DEFER** with an explicit checklist so docs and locks stay aligned
until a future ENABLE.

**Business need:** Trim CI billable overlap only when the documented bar is
crossed; avoid premature exclusion that drops multi-version coverage.

**Source:** [PYPOST-907/60-tech-debt.md](../PYPOST-907/60-tech-debt.md) follow-up.

## Programming Language

Python pytest contract guards, GitHub Actions YAML (only if ENABLE), English
Markdown in `doc/dev/`.

## User Stories

- As a **CI maintainer**, I want an evidence-backed ENABLE-or-DEFER decision
  against the published threshold, not guesswork.
- As a **contributor**, I want docs to state whether the double-run still
  applies and why after this revisit.
- As a **future maintainer**, I want a checklist showing which threshold
  triggers fired or did not, so the next revisit is cheap.

## Definition of Done

- Each ENABLE threshold trigger assessed against honest evidence (no invented
  timings).
- Explicit **ENABLE** or **continued DEFER** with rationale.
- If **ENABLE**: workflow excludes `agent_e2e` from main matrix; 3.13 plan;
  lock flipped. If **DEFER**: dual coverage unchanged; lock + docs encode
  checklist and continued DEFER.
- Automated lock tests encode the chosen contract.
- Unticketed follow-ups listed in `60-tech-debt.md` only.

## Task Description

### Problem

Agent e2e runs twice on Python 3.11 (main matrix + `agent-e2e` job). PYPOST-907
defined when to ENABLE a trim. This task executes that revisit.

### In Scope

- Assess ENABLE threshold (≥6m pack step × ≥3 green runs; maintainer pain;
  pack ≥120 + domination).
- Implement ENABLE or document continued DEFER + checklist.
- Update lock and `doc/dev` accordingly.

### Out of Scope

- Harness redesign; Jira ticket creation in execution; git commit.

## Functional Requirements

- FR1: Threshold checklist with met/not-met per trigger.
- FR2: ENABLE-or-DEFER decision tied to checklist.
- FR3: Lock + docs match decision (dual-run if DEFER).
- FR4: If ENABLE, 3.13 agent e2e coverage via expanded job/matrix.

## Non-Functional Requirements

- NFR1: Do not invent CI timings; cite published PYPOST-907 evidence and
  local collect counts only unless fresh Actions data is fetched.
- NFR2: Do not exclude `agent_e2e` from matrix unless ENABLE criteria met.

## Constraints and Assumptions

- Parent evidence: PYPOST-907 (n=2 Actions runs, ~172s max pack step).
- Dedicated `agent-e2e` job is 3.11-only today.
- No commit in this run.

## Q&A

| Q | A |
| --- | --- |
| What if only one trigger is close? | All three primary triggers must be assessed; ENABLE requires meeting the documented bar, not proximity. |
| What if pack grew since 907? | Re-measure local collect; still DEFER unless ≥120 sustained and domination evidenced. |
