# PYPOST-873: Optional CI cost trim for agent-e2e double-run

## Goals

After [PYPOST-861](https://pypost.atlassian.net/browse/PYPOST-861) added a
dedicated CI job for the agent e2e env pack, the same pack also still runs
inside the main pytest matrix. Maintainers need a clear **ENABLE trim vs
DEFER** decision so CI minutes are not wasted if the overlap hurts, while
multi-version and make-gate coverage stay trustworthy until pain is real.

This debt comes from PYPOST-861 tech-debt follow-up: optional cost trim only
if the Python 3.11 double-run becomes painful.

## Programming Language

CI workflow (YAML) and Python pytest contract/doc guards
(`.cursor/lsr/do-python.md`, `.cursor/lsr/do-testing.md`). Developer
documentation in English Markdown (`.cursor/lsr/do-markdown.md`).

## User Stories

- As a **CI maintainer**, I want a recorded decision on whether to stop
  re-running agent e2e tests inside the main matrix when the dedicated
  `agent-e2e` job already exists, so we do not burn minutes without reason
  and do not drop coverage by accident.
- As a **contributor**, I want docs to explain how agent e2e is gated in CI
  (dedicated job vs main matrix), so I know where failures will show up.
- As a **future maintainer**, I want revisit criteria if DEFER is chosen, so
  we can ENABLE a trim later without re-discovering the trade-offs.

## Definition of Done

- An explicit decision is recorded: **ENABLE** CI cost trim **or** **DEFER**
  with documentation — with rationale tied to whether double-run pain is
  observed.
- Acceptance behavior of the chosen approach is locked by automated checks
  and/or updated developer docs as appropriate.
- Contributors can read one place that states whether agent e2e may run twice
  on Python 3.11 and why.
- Unticketed follow-ups (if any) live only in this task’s `60-tech-debt.md`
  (no Jira ticket creation in this run).

## Task Description

**Problem:** Job `agent-e2e` runs `make test-agent-e2e` on Python 3.11. The
main `test` matrix also runs the same marker set via `-m "not slow"` on
Python 3.11 and 3.13. That is intentional dual coverage from PYPOST-861, but
it can cost extra CI minutes on 3.11.

**Business need:** Avoid unnecessary CI spend without silently weakening the
agent e2e / env-pack quality gate or multi-version coverage.

### In Scope

- Research current `.github/workflows` layout and double-run facts.
- Decide ENABLE trim vs DEFER with docs; write rationale.
- Implement the chosen path (workflow change and/or docs + locks).
- Align related mentions in `doc/dev` with the decision.

### Out of Scope

- Redesigning the agent e2e harness or marker selection.
- Expanding `agent-e2e` to a full Python matrix unless ENABLE requires it.
- Creating Jira Debt tickets (unticketed items only in `60-tech-debt.md`).
- Commit or Jira status transitions (orchestrator owns those).

## Functional Requirements

- FR1: Record ENABLE vs DEFER decision with rationale in architecture.
- FR2: After delivery, docs state how agent e2e is covered in CI relative to
  the main matrix (including any intentional 3.11 overlap).
- FR3: Automated checks encode the chosen contract (workflow and/or docs).
- FR4: Existing agent e2e make/CI entry from PYPOST-861 remains a first-class
  gate unless ENABLE deliberately changes matrix selection.

## Non-Functional Requirements

- NFR1: Prefer clarity over premature optimization; DEFER unless double-run
  pain is evidenced.
- NFR2: Do not remove 3.13 agent e2e coverage without an explicit replacement.
- NFR3: Docs stay in English; line length ≤ 100 where practical.

## Constraints and Assumptions

- Parent debt: PYPOST-861 `60-tech-debt.md` item 3 → this ticket (“only if
  double-run minutes become painful”).
- Dedicated job today is Python 3.11 only; main matrix covers 3.11 + 3.13.
- No commit / no Jira writes in this execution run.

## Main Entities (business)

| Entity | Role |
| --- | --- |
| Main CI test matrix | Fast suite on multiple Python versions |
| Dedicated agent-e2e CI job | Make-gate for env pack / agent UI e2e |
| Agent e2e pack | Marker-selected scenarios under `agent_e2e` |
| Cost-trim decision | ENABLE exclusion vs DEFER dual coverage |
| Revisit criteria | When DEFER should become ENABLE |

## Q&A

| Q | A |
| --- | --- |
| Why not always ENABLE? | Parent debt keeps dual coverage until minutes hurt; trim can drop 3.11 matrix overlap that still validates agent e2e beside the rest of the suite. |
| Why not always DEFER forever? | If the pack grows or CI minutes become painful, ENABLE is the right follow-up with documented trade-offs. |
| Jira / commit in this run? | No — user directed; worklog block only for parent. |
