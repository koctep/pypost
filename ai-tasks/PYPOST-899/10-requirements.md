# PYPOST-899: Optional live-session ready-log smoke

## Goals

Maintainers need end-to-end confidence that packaging session fixtures emit
`agent_e2e_fixture_ready` through a real offscreen Qt session — not only via
mocked unit proofs (PYPOST-867). Closing this optional gap locks the ready log
contract on the live fixture path exercised by agent e2e harness tests.

## Programming Language

Python 3.10+

## User Stories

- As a **maintainer**, I want a thin marked agent e2e test that asserts
  `agent_e2e_fixture_ready` under caplog without mocking the session boundary,
  so packaging ready logs are verified on the live offscreen path.
- As a **contributor**, I want that smoke to follow existing timeout and caplog
  patterns, so it stays consistent with the suite.
- As a **desktop user** (indirect), I want this debt work not to change product
  UX — only to lock existing packaging ready observability on the live path.

## Definition of Done

- A thin `@pytest.mark.agent_e2e` test (or seeded variant) asserts blank
  and/or seeded `agent_e2e_fixture_ready` under caplog without mocking
  `AgentAppSession` or `seeded_agent_dirs`.
- The check declares an explicit pytest timeout marker.
- The module appears in the agent e2e harness table when marked.
- Steps 1–8 task artifacts exist for PYPOST-899.
- No intentional change to product UX or packaging behavior beyond locking the
  ready-event contract on the live path.

## Task Description

**Problem:** PYPOST-867 added mocked caplog proofs for packaging ready events.
Step 7 noted optional missing coverage: no live offscreen session re-assert of
the same events. Source:
[PYPOST-899](https://pypost.atlassian.net/browse/PYPOST-899), from
[PYPOST-867](https://pypost.atlassian.net/browse/PYPOST-867)
`ai-tasks/PYPOST-867/60-tech-debt.md` — Optional live-session ready-log smoke.

**Business need:** Close this lowest-priority testing debt so packaging ready
logs remain verified end-to-end without relying solely on mocked unit proofs.

### In Scope

- Adding focused live-session caplog smoke for blank and/or seeded ready events.
- Using real `agent_e2e_session` / `seeded_agent_e2e_session` fixtures (no
  session-boundary mocks).
- Completing Steps 1–8 workflow artifacts.
- Updating developer docs (harness table, logging cross-links).

### Out of Scope

- Changing packaging fixture behavior, seed inventory, HTTP stubs, or failure
  artifacts.
- Replacing or removing PYPOST-867 mocked unit proofs.
- New product features or UI changes.

## Functional Requirements

- FR1: The automated check records that `agent_e2e_fixture_ready` is emitted
  for at least one of blank or seeded packaging ready on the live fixture path
  (preferably both when cheap).
- FR2: The check includes documented mode tokens (`mode=blank` and/or
  `mode=seeded`).
- FR3: The check does **not** mock `AgentAppSession` or `seeded_agent_dirs`.
- FR4: Maintainers can discover the check in the agent e2e harness table
  (`@pytest.mark.agent_e2e`).

## Non-Functional Requirements

- NFR1: Explicit per-module or per-test `pytest.mark.timeout` (GUI tier: 60s).
- NFR2: Runs under offscreen Qt via `make test-agent-e2e` / project defaults.
- NFR3: Thin smoke — caplog assert + minimal session-ready sanity only.

## Q&A

| Question | Answer |
| --- | --- |
| Source of the debt item? | [PYPOST-867 tech debt](../PYPOST-867/60-tech-debt.md) → PYPOST-899. |
| Replace PYPOST-867 unit tests? | No — complementary live-path smoke. |
| Mark `agent_e2e`? | Yes — live offscreen session; belongs in harness table. |
