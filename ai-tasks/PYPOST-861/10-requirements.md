# PYPOST-861: CI job + make target for agent e2e env pack

## Goals

Epic [PYPOST-855](https://pypost.atlassian.net/browse/PYPOST-855) needs the
agent e2e **environment pack** to be runnable through project-standard make
and CI — not undocumented one-off shell. Seed (857), session/marker (858),
and HTTP (859) already exist; the env contract
([agent_e2e_env.md](../../doc/dev/agent_e2e_env.md)) still marks **Make / CI
entry** as incomplete until this story lands.

Today, `make test-agent-e2e` selects the `agent_e2e` marker (858), and the
main CI fast suite includes those tests via `-m "not slow"`. What is missing
as a **first-class env-pack product**: explicit CI wiring that exercises the
make entry, makefile smoke that guards the recipe, and docs that cross-link
make ↔ CI ↔ env pack so authors know the pack is gated.

This story’s business goal is to **finish the env-pack run entry**: make
target (extend or sibling) runs env-pack tests; CI job or documented CI step
runs the same path; umbrella docs cross-link; absorb remaining relevant
[PYPOST-854](https://pypost.atlassian.net/browse/PYPOST-854) follow-ups
(makefile smoke + optional CI step; marker already delivered by 858).

## Programming Language

Python (`.cursor/lsr/do-python.md`) for makefile smoke / pytest assertions.
Makefile and GitHub Actions for the make/CI surface. Developer docs in
English Markdown (`.cursor/lsr/do-markdown.md`).

## User Stories

- As a **scenario author / AI agent**, I want one documented make command that
  runs the env pack (seed, session, HTTP Send scenarios under `agent_e2e`) so
  I do not invent shell one-liners.
- As a **CI gate owner**, I want the same make path exercised (or explicitly
  documented) in CI so regressions in the env pack fail the pipeline visibly.
- As a **maintainer**, I want makefile smoke covering the agent-e2e target so
  recipe drift (wrong marker, missing deps) is caught early.
- As a **docs reader**, I want `agent_e2e.md` / testing docs to cross-link make
  and CI so “how do I run / where is it gated?” is obvious.
- As a **debt cleaner**, I want PYPOST-854’s remaining make/CI items absorbed
  here rather than left as orphan follow-ups (marker already owned by 858).

## Definition of Done

- A make target (extended `test-agent-e2e` or a clear sibling) runs env-pack
  tests under offscreen Qt via the project Makefile.
- CI has a job **or** a documented CI step that runs that same make path (or
  an equivalent documented gate that names the make target).
- `doc/dev/agent_e2e.md` (and related testing / env-contract docs) cross-link
  make and CI for the env pack.
- Relevant PYPOST-854 items are absorbed: makefile smoke for the agent-e2e
  target; CI step/job for the make path. Marker `agent_e2e` remains 858’s
  delivery (not re-owned here).
- Env contract status for “Make / CI for env pack” can move to Delivered.

## Task Description

**Problem:** Env pack fixtures exist, but make/CI are not yet first-class for
the pack — contract still says “wire later,” and PYPOST-854 still tracks
makefile smoke + optional CI step.

**Business need:** Productize the run entry so the env pack is complete as an
operable, CI-gated pack.

### In Scope

- Make target that runs env-pack / `agent_e2e` tests (extend existing target
  or add a sibling with clear ownership).
- CI job or documented CI step for that make path.
- Makefile smoke guarding the target (absorb PYPOST-854 TD-2).
- Cross-links from `doc/dev/agent_e2e.md` and testing / env-contract docs.
- Note absorption of PYPOST-854 remaining make/CI debt.

### Out of Scope

- Re-implementing seed (857), session/marker (858), or HTTP (859).
- Failure artifact dumps on assert fail (PYPOST-860).
- Changing the product UI or RequestWorker path.
- User-facing product docs (`doc/user/`).
- Replacing the main fast suite; agent_e2e may continue to run there too.

## Functional Requirements

- FR1: Provide a first-class make entry that runs agent e2e / env-pack tests
  (marker-selected or documented file set) under offscreen Qt.
- FR2: Env-pack scenarios already marked `agent_e2e` (seed, HTTP env Send,
  golden, harness) are included when that make entry runs with defaults.
- FR3: CI runs that make path via a dedicated job **or** documents an
  equivalent CI step that names the make target.
- FR4: Makefile automation smoke asserts the agent-e2e target’s contract
  (dependencies / default selection / help discoverability as designed).
- FR5: Developer docs cross-link make ↔ CI ↔ env pack from the umbrella
  agent e2e page (and update env-contract status).
- FR6: Absorb PYPOST-854 makefile smoke + optional CI step intent; do not
  duplicate marker work already delivered by 858.

## Non-functional Requirements

- **Discoverability:** `make help` describes the agent-e2e / env-pack entry.
- **Parity:** Local make and CI use the same conceptual command (make target).
- **Minimalism:** Prefer extending `test-agent-e2e` over a redundant sibling
  unless a sibling clearly separates concerns.
- **Cost awareness:** Avoid unnecessary full double-matrix of the entire GUI
  pack when a single-version dedicated job or documented step suffices.
- **Timeouts:** New/changed pytest tests declare explicit
  `pytest.mark.timeout` per `.cursor/lsr/do-testing.md`.
- **Make consistency:** Prefer Makefile over undocumented shell-only recipes.

## Constraints and Assumptions

- Parent epic: [PYPOST-855](https://pypost.atlassian.net/browse/PYPOST-855).
- Env contract: [PYPOST-856](https://pypost.atlassian.net/browse/PYPOST-856) /
  [doc/dev/agent_e2e_env.md](../../doc/dev/agent_e2e_env.md).
- Marker + make selection: [PYPOST-858](https://pypost.atlassian.net/browse/PYPOST-858).
- Debt absorb: [PYPOST-854](https://pypost.atlassian.net/browse/PYPOST-854) —
  TD-1 marker done in 858; TD-2 makefile smoke + TD-3 optional CI step in
  scope here.
- Main CI already runs `pytest tests/ -m "not slow"`, which includes
  `agent_e2e` tests; this story still requires an explicit make-path gate or
  documented CI step naming the make target.
- Step 1 review is treated as pre-approved under sprint-task-runner autonomy.

## Main Entities and Interactions

| Entity | Role |
| --- | --- |
| Make target (`test-agent-e2e` or sibling) | Local first-class run entry for env pack |
| CI job / documented CI step | Pipeline gate for the same make path |
| `agent_e2e` marker selection | Selects env pack + harness modules (858) |
| Makefile smoke | Guards recipe deps / selection / help |
| Env contract | Declares make/CI area; status updated when done |
| Umbrella docs | Cross-link make and CI for authors |
| PYPOST-854 | Remaining make/CI debt absorbed here |

Interaction overview:

1. Author runs the documented make target locally (offscreen).
2. Marker selection includes env-pack and harness `agent_e2e` tests.
3. CI exercises the same make path (job or documented step).
4. Makefile smoke fails if the target contract drifts.
5. Docs point authors to make and CI from the umbrella / env pages.

## Q&A

- Q: Why not only rely on the main fast suite?
  A: AC requires make + CI entry for the **env pack**; authors need a named
  make target, and CI must name or run that path so the pack is first-class.
- Q: Extend `test-agent-e2e` or add a sibling?
  A: Prefer extend — 858 already wired `-m agent_e2e`; env pack rides that
  marker. Sibling only if a clear split is needed (not expected).
- Q: Does this story own the `agent_e2e` marker?
  A: No — 858 delivered it. This story consumes it for make/CI productization.
- Q: What of PYPOST-854?
  A: Absorb makefile smoke + optional CI step; marker already done; close or
  link 854 after this story as follow-up process (not a code AC here).
- Q: Who owns failure dumps?
  A: PYPOST-860.
