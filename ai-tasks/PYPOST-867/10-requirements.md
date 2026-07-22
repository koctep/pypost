# PYPOST-867: Optional caplog proof for agent_e2e_fixture_ready

## Goals

Maintainers need automated proof that packaging session fixtures emit the
documented ready log event `agent_e2e_fixture_ready` for blank and/or seeded
modes. Today the event is produced and catalogued, but no test asserts it.
Closing this optional logging-catalog gap makes regressions in packaging ready
signals detectable in CI without relying on manual log inspection.

## Programming Language

Python 3.10+

## User Stories

- As a **maintainer**, I want an automated check that blank and/or seeded
  packaging fixtures emit `agent_e2e_fixture_ready`, so logging-catalog
  regressions are caught early.
- As a **contributor**, I want that check to follow the same timeout and
  caplog patterns as other agent e2e packaging tests, so new proofs stay
  consistent with the suite.
- As a **desktop user** (indirect), I want this debt work not to change product
  UX — only to lock in existing packaging ready observability.

## Definition of Done

- An automated check covers blank and/or seeded fixture ready log emission for
  `agent_e2e_fixture_ready` (acceptance: blank and/or seeded).
- The check uses caplog (or equivalent project-allowed capture) scoped to the
  packaging fixture logger.
- The check declares an explicit pytest timeout marker (module, class, or
  function scope).
- Steps 1–8 task artifacts exist for PYPOST-867.
- No intentional change to product UX or successful packaging behavior beyond
  locking the ready-event contract.

## Task Description

**Problem:** PYPOST-858 delivered packaging fixtures that log
`agent_e2e_fixture_ready mode=blank|seeded`, but Step 7 noted optional missing
coverage: no automated assert of that event. Source:
[PYPOST-867](https://pypost.atlassian.net/browse/PYPOST-867), from
[PYPOST-858](https://pypost.atlassian.net/browse/PYPOST-858)
`ai-tasks/PYPOST-858/60-tech-debt.md` — Optional caplog proof for packaging
ready event.

**Business need:** Close this low-priority testing/observability debt so
packaging ready logs remain part of the verified contract.

### In Scope

- Adding focused automated check(s) for blank and/or seeded
  `agent_e2e_fixture_ready` emission.
- Using isolation (mocks) where practical so the check does not require a full
  live GUI path beyond what packaging already needs.
- Completing Steps 1–8 workflow artifacts.
- Updating developer docs that describe packaging logging proofs if needed.

### Out of Scope

- Changing packaging fixture behavior, seed inventory, HTTP stubs, or failure
  artifacts.
- Sibling hygiene (harness table sync, seed inventory drift, make/CI packs).
- New product features or UI changes.

## Functional Requirements

- FR1: The automated check records that `agent_e2e_fixture_ready` is emitted
  for at least one of blank or seeded packaging ready (preferably both when
  cheap).
- FR2: The check distinguishes or includes the documented mode token
  (`mode=blank` and/or `mode=seeded`) so catalog regressions are meaningful.
- FR3: The check isolates fixture ready logging without requiring live network
  or external services.
- FR4: Maintainers can discover the check alongside other agent e2e packaging
  coverage (same module family or clearly named packaging-log module).

## Non-Functional Requirements

- NFR1: Explicit pytest timeout marker on the new check (or inherited module
  marker).
- NFR2: Caplog assertion scoped to the packaging fixture logger
  (`tests._pytest_plugins.agent_e2e` or equivalent).
- NFR3: Prefer fast, deterministic unit/integration style (mocked session
  boundary when sufficient).
- NFR4: No secrets or live host dependency in the proof scenario.

## Constraints and Assumptions

- Packaging fixtures and the ready event already exist from PYPOST-858; this
  task primarily adds verification.
- Acceptance allows blank and/or seeded; covering both is preferred when cost
  is low.
- Autonomous batch run: user approval gates are pre-approved for Steps 1–8;
  Jira updates and git commit are out of band for this execution.

## Main Entities (business)

| Entity | Role |
| --- | --- |
| Packaging session fixture | Blank or seeded agent e2e session setup |
| Fixture ready event | Named log signal that the fixture is ready |
| Mode token | Distinguishes blank vs seeded ready |
| Caplog proof | Automated assert of the ready event |

## Q&A

| Q | A |
| --- | --- |
| Why assert logs if fixtures already work? | Catalog/event regressions are invisible without a proof; optional debt from PYPOST-858. |
| Must both modes be covered? | Acceptance is blank and/or seeded; prefer both if cheap. |
| Product impact? | None — test/docs hygiene only. |
| Source of the debt item? | [PYPOST-858 tech debt](../PYPOST-858/60-tech-debt.md) → [PYPOST-867](https://pypost.atlassian.net/browse/PYPOST-867). |
