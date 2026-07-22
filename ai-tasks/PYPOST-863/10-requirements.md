# PYPOST-863: Optional drive-then-snapshot / base_url resolve proof

## Goals

Agent e2e seed (PYPOST-857) already proves inventory presence after ready via
identity and model/item enumeration. Maintainers still lack soft coverage that
**selecting** the seeded environment and/or **opening** a seeded request yields
observable product-facing state (active env, method, `{{base_url}}`
resolution) via drive-then-snapshot or an equivalent agent observation path.
Closing this gap strengthens FR2/FR3 confidence without replacing the baseline
presence proof.

## Programming Language

Python 3.10+ (pytest agent e2e tests and helpers). Developer docs in English
Markdown under `doc/dev/`.

## User Stories

- As a **scenario author / AI agent**, I want an automated proof that after the
  session is ready I can drive the UI (select seeded env and/or open a seeded
  request) and observe method / URL / active-env state, so I trust seed beyond
  sidebar presence.
- As a **maintainer**, I want that proof to document **present vs active**
  environment behavior so tests do not confuse “env is listed” with “env is
  selected.”
- As a **quality gate**, I want the check to use agent UI actions after ready
  and not rely on blank-ready `ui_snapshot` name scanning.
- As a **desktop user** (indirect), I want this debt work not to change product
  UX—only to lock soft coverage for seed consumers.

## Definition of Done

- An automated agent e2e check, after ready, uses agent UI actions to select
  the seeded environment and/or open a seeded request.
- The check asserts product-facing state (e.g. method and/or `{{base_url}}`
  resolution / URL inventory match) via drive-then-snapshot or equivalent.
- The check does **not** rely on blank-ready `ui_snapshot` name scan as the
  presence proof.
- Present vs active environment behavior is documented (in the test and/or
  developer seed docs).
- Explicit pytest timeout marker is present (module/class/function).
- Steps 1–8 artifacts exist for PYPOST-863.
- No intentional change to seed inventory contents or end-user product UX
  beyond locking this soft proof.

## Task Description

**Problem:** PYPOST-857 FR8 used identity + model/item enumeration only.
Drive-then-snapshot and active-env / open-request resolve depth were deferred
as optional Low debt.

**Business need:** Soft FR2/FR3 coverage so env-pack scenarios can rely on
active-env and opened-request guarantees when needed.

Source: [PYPOST-863](https://pypost.atlassian.net/browse/PYPOST-863), from
[PYPOST-857](https://pypost.atlassian.net/browse/PYPOST-857)
`ai-tasks/PYPOST-857/60-tech-debt.md`. Related tree: `ai-tasks/PYPOST-857/`.

### In Scope

- Extend seed product-facing tests with drive-then-snapshot (or equivalent)
  after ready.
- Use agent UI actions for select env and/or open seeded request.
- Document present vs active env behavior.
- Task artifacts Steps 1–8.

### Out of Scope

- Changing seed inventory builders or ids/names.
- Replacing the identity + model/item baseline presence proof.
- Sibling packaging (858), HTTP determinism (859), failure artifacts (860),
  make/CI pack entry (861), caplog failure path (862), inventory drift (864).
- New end-user product features.

## Functional Requirements

- FR1: After ready, the check drives the UI with agent UI actions (not
  hand-built disk-only asserts).
- FR2: The check selects the seeded environment and/or opens a seeded sample
  request.
- FR3: The check asserts product-facing state such as method and/or
  `{{base_url}}` resolution / URL inventory match via snapshot or equivalent
  observation.
- FR4: The check must not use blank-ready `ui_snapshot` name scan as the sole
  proof of seed presence.
- FR5: Present vs active environment behavior is explicitly documented.
- FR6: The check lives with the existing seed test surface so maintainers
  discover it alongside PYPOST-857 coverage.
- FR7: Explicit timeout marker applies (do-testing).

## Non-functional Requirements

- **Determinism:** Prefer offscreen agent lifecycle session and seeded
  fixture; no live external hosts required for this soft proof.
- **Clarity:** Failure messages should name missing inventory / active-state
  expectations.
- **Minimalism:** One focused scenario is enough; do not expand into a full
  Send/HTTP matrix (PYPOST-859 owns HTTP).
- **Non-fork:** Consume PYPOST-832 lifecycle / actions / snapshot / wait; do
  not redesign those APIs.

## Constraints and Assumptions

- Parent seed story: PYPOST-857; epic PYPOST-855.
- Labels: `agent`, `e2e`, `testing`, `tech-debt`.
- Step reviews treated as pre-approved under sprint-task-runner autonomy.
- “Agent UI actions” means the project’s in-process agent action API used
  after ready (today: `AgentAppSession.ui_*`).

## Main Entities and Interactions

| Entity | Role |
| --- | --- |
| Seeded workspace | Known collection / env / sample requests after bootstrap |
| Agent lifecycle session | Isolated ready session consuming seed |
| Agent UI actions | Select env / drive open after ready |
| Snapshot / observe | Product-facing assert of method, URL, active env |
| Present env | Seeded env listed but not necessarily selected |
| Active env | Seeded env selected so variables apply |

Interaction: ready → (document present ≠ active) → select and/or open →
snapshot/observe → assert method / resolve / active name.

## Q&A

- Q: Why not only blank-ready snapshot?
  A: Snapshot extractors are selection-scoped; blank-ready does not list
  unselected tree rows or non-current combo items.
- Q: Does this replace PYPOST-857 identity proof?
  A: No. Soft extension only.
- Q: Must Send / HTTP stub be exercised?
  A: No. Soft FR2/FR3; HTTP Send remains PYPOST-859.
- Q: Approval for Step 1?
  A: Pre-approved under autonomous sprint-task-runner.
