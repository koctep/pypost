# PYPOST-907: ENABLE CI cost trim when pain evidenced

## Goals

Maintainers previously **DEFER**red excluding agent e2e from the main CI
matrix ([PYPOST-873](https://pypost.atlassian.net/browse/PYPOST-873)) until
double-run cost hurt. This Debt revisits that decision with **documented CI
duration evidence**: either **ENABLE** a cost trim that removes painful
overlap without losing multi-version coverage, or **DEFER** again with a
clearer evidence-backed threshold so a future ENABLE is not guesswork.

**Business need:** Spend CI minutes only where they protect quality; avoid
premature exclusion that drops coverage; avoid endless dual-run if overlap is
already proven painful.

**Source:** [PYPOST-907](https://pypost.atlassian.net/browse/PYPOST-907)
(follow-up from PYPOST-873). Related evidence ticket:
[PYPOST-908](https://pypost.atlassian.net/browse/PYPOST-908).

## Programming Language

CI workflow (YAML) and Python pytest contract/doc guards
(`.cursor/lsr/do-python.md`, `.cursor/lsr/do-testing.md`). Developer
documentation in English Markdown (`.cursor/lsr/do-markdown.md`).

## User Stories

- As a **CI maintainer**, I want an ENABLE-or-DEFER decision grounded in
  real Actions (or honest local) timing evidence, so we do not trim or keep
  overlap on gut feel alone.
- As a **contributor**, I want docs to say whether agent e2e still runs in
  the main matrix and why, so I know where failures appear after this
  revisit.
- As a **future maintainer**, I want a numeric or qualitative ENABLE
  threshold recorded if we DEFER again, so the next revisit is cheap.
- As a **quality owner**, I want any ENABLE path to keep 3.13 agent e2e
  coverage (matrix or expanded dedicated job), so multi-version confidence
  does not silently shrink.

## Definition of Done

- Documented CI duration / overlap evidence is recorded (honest numbers;
  no invented timings).
- An explicit **ENABLE** or **DEFER** decision is recorded with rationale
  tied to that evidence.
- If **ENABLE**: workflow removes the painful overlap; 3.13 coverage remains
  via an explicit plan; PYPOST-873 lock/docs updated for the new contract.
- If **DEFER**: workflow dual-coverage stays; docs and lock encode the
  evidence review, continued DEFER, and ENABLE threshold / scaffolding for
  a later trim.
- Automated checks encode the chosen contract.
- Unticketed follow-ups (if any) live only in this task’s `60-tech-debt.md`
  (no Jira ticket creation in this run).

## Task Description

### Problem

Job `agent-e2e` and the main `test` matrix both exercise the agent e2e pack
on Python 3.11. PYPOST-873 kept that intentional double-run. PYPOST-907 asks
whether pain is now evidenced enough to ENABLE a trim (exclude `agent_e2e`
from the main matrix only with a 3.13 coverage plan) and update the lock and
docs.

### In Scope

- Gather or cite honest CI / local duration evidence for the overlap.
- Decide ENABLE vs DEFER with rationale.
- Implement the chosen path (workflow and/or docs + lock updates).
- Align `doc/dev` mentions with the decision.
- Note relationship to PYPOST-908 (duration evidence).

### Out of Scope

- Redesigning the agent e2e harness or marker selection.
- Creating Jira Debt tickets (list unticketed items for orchestrator).
- Commit or Jira status / worklog writes (orchestrator owns those).

## Functional Requirements

- FR1: Record ENABLE vs DEFER with rationale tied to documented evidence.
- FR2: Publish evidence notes contributors can find (docs and/or task
  artifacts).
- FR3: Automated checks encode the chosen CI/docs contract.
- FR4: If ENABLE, 3.13 agent e2e coverage remains via an explicit plan; if
  DEFER, dual coverage and revisit threshold remain explicit.
- FR5: PYPOST-873-era lock/docs language is updated to match this revisit.

## Non-Functional Requirements

- NFR1: Do not invent timing numbers; cite Actions history and/or measured
  local runs only.
- NFR2: Prefer clarity over premature optimization when evidence is thin or
  wall-clock unaffected.
- NFR3: Docs stay in English; line length ≤ 100 where practical.

## Constraints and Assumptions

- Parent: PYPOST-873 DEFER + dual-run lock.
- Related: PYPOST-908 (optional duration evidence) may be partially
  satisfied by evidence captured here.
- Dedicated `agent-e2e` job today is Python 3.11 only; main matrix is
  3.11 + 3.13.
- No commit / no Jira writes in this execution run.

## Main Entities (business)

| Entity | Role |
| --- | --- |
| Main CI test matrix | Fast suite on multiple Python versions |
| Dedicated agent-e2e CI job | Make-gate for env pack / agent UI e2e |
| CI duration evidence | Measured job/step timings for overlap judgment |
| Cost-trim decision | ENABLE exclusion vs DEFER dual coverage |
| ENABLE threshold | When DEFER should become ENABLE next |

## Q&A

| Q | A |
| --- | --- |
| Why not always ENABLE? | Parent kept dual coverage until pain is real; trim without a 3.13 plan drops multi-version confidence. |
| Why not always DEFER forever? | If evidence shows painful overlap, ENABLE saves minutes without waiting for another ticket cycle. |
| What if evidence is thin? | Document DEFER + threshold; still satisfy DoD via evidence scaffolding and lock/docs update. |
| Jira / commit in this run? | No — orchestrator owns transitions, worklog, and commit. |
