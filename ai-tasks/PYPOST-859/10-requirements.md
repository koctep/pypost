# PYPOST-859: Deterministic HTTP fixture layer for agent flows

## Goals

Epic [PYPOST-855](https://pypost.atlassian.net/browse/PYPOST-855) needs
agent UI flows that prove Send → response without depending on live
external HTTP. The environment contract
([PYPOST-856](https://pypost.atlassian.net/browse/PYPOST-856) /
[agent_e2e_env.md](../../doc/dev/agent_e2e_env.md)) already names a
**deterministic HTTP** fixture area so scenarios share one canned-response
path instead of each test hand-rolling transport stubs.

Today, the golden agent e2e scenario privately patches the HTTP send
boundary with a one-off canned result. Env-pack scenarios that need Send
have no shared canned catalog. That duplicates stub setup, drifts from the
contract’s “shared HTTP layer” path, and makes “how do I add a new canned
response?” tribal knowledge.

This story’s business goal is to **provide one documented deterministic
HTTP fixture/helper** — shared canned responses and a single stubbing
entry for agent e2e — so golden and env scenarios consume that layer, stay
CI-deterministic under offscreen Qt, and keep the real UI → worker path
while mocking only at the HTTP boundary.

## Programming Language

Python (`.cursor/lsr/do-python.md`) for the shared helper/fixture and
tests. Developer documentation under `doc/dev/` in English Markdown
(`.cursor/lsr/do-markdown.md`).

## User Stories

- As a **scenario author / AI agent**, I want one shared way to stub or
  serve canned HTTP outcomes for agent e2e so I do not invent a private
  patch in every Send scenario.
- As a **golden / env scenario owner**, I want my flows to use that shared
  layer (not one-off patches) so HTTP determinism stays consistent across
  the pack.
- As a **maintainer**, I want clear docs for adding a new canned response
  so the catalog grows without copy-paste drift.
- As a **CI gate**, I want agent flows to remain deterministic under
  offscreen Qt with no live external HTTP as the primary path.
- As a **product-path owner**, I want the real RequestWorker / UI send path
  to stay exercised, with mocking only at the HTTP transport boundary.

## Definition of Done

- A shared helper and/or pytest fixture exists to stub or serve canned
  responses for agent e2e scenarios.
- Golden and env scenarios that perform Send use the shared layer (not
  private one-off `send_request` patches as the primary path).
- Developer docs explain how to add a new canned response.
- Agent e2e Send flows remain CI-deterministic under offscreen Qt (no live
  network as the default path).
- The UI → RequestWorker → response panel path stays real; mocking is at
  the HTTP client send boundary.
- Scope stays on HTTP determinism; session packaging (858), seed inventory
  (857), failure artifacts (860), and full env-pack make/CI (861) remain
  sibling stories.

## Task Description

**Problem:** Agent e2e Send scenarios stub HTTP privately (golden’s
one-off patch). There is no shared, documented canned-response layer for
the env pack.

**Business need:** One documented HTTP fixture/helper so every agent flow
that needs a deterministic response uses the same boundary and catalog.

### In Scope

- Shared helper/fixture for stubbing or serving canned HTTP responses in
  agent e2e.
- Migrate golden (and env Send scenarios as applicable) onto that layer.
- Document how to add new canned responses.
- Preserve CI determinism under offscreen Qt.
- Prefer real UI / RequestWorker path; mock at HTTP send boundary.

### Out of Scope

- Replacing or redesigning session fixtures / `agent_e2e` marker
  (PYPOST-858).
- Redefining seed inventory (PYPOST-857).
- Failure artifact dumps on assert fail (PYPOST-860).
- Full env-pack make/CI productization (PYPOST-861).
- Mocking `RequestWorker` wholesale or replacing the product send path.
- Live external HTTP as the primary acceptance path.
- User-facing product docs (`doc/user/`).

## Functional Requirements

- FR1: Provide a shared helper and/or pytest fixture that installs a
  deterministic HTTP stub (or equivalent canned serve) for agent e2e.
- FR2: Provide a documented canned-response catalog (or equivalent named
  builders) covering at least the golden OK outcome and seed-oriented
  responses needed by env Send scenarios.
- FR3: Golden agent e2e uses the shared layer instead of a private
  one-off patch as its primary HTTP stub.
- FR4: Env agent e2e scenarios that Send use the shared layer (same
  helper/fixture path as golden).
- FR5: Docs describe how to add a new canned response (where to define
  it, how to select it in a scenario).
- FR6: Stubbing targets the HTTP client send boundary used by the product
  request path so UI → worker remains real.
- FR7: Default agent-flow path does not require live external network;
  outcomes remain deterministic in offscreen CI.
- FR8: Layer composes with PYPOST-858 session fixtures and PYPOST-857
  seed without owning those areas.

## Non-functional Requirements

- **Shared vocabulary:** Align with env contract terms (“HTTP
  determinism,” canned responses, HTTP boundary).
- **Discoverability:** Catalog + docs findable from agent e2e / env
  umbrella pages.
- **Minimalism:** Smallest shared layer that removes one-off patches;
  do not redesign transport or worker architecture.
- **Isolation:** Stub install/teardown must not leak across tests.
- **Timeouts:** New/changed pytest tests declare explicit
  `pytest.mark.timeout` per `.cursor/lsr/do-testing.md`.
- **Make consistency:** Prefer existing `make test-agent-e2e` / offscreen
  Qt paths; do not invent undocumented shell-only recipes as primary.

## Constraints and Assumptions

- Parent epic: [PYPOST-855](https://pypost.atlassian.net/browse/PYPOST-855).
- Env contract: [PYPOST-856](https://pypost.atlassian.net/browse/PYPOST-856) /
  [doc/dev/agent_e2e_env.md](../../doc/dev/agent_e2e_env.md) — this story
  implements the “deterministic HTTP” fixture area.
- Session packaging: [PYPOST-858](https://pypost.atlassian.net/browse/PYPOST-858).
- Seed: [PYPOST-857](https://pypost.atlassian.net/browse/PYPOST-857).
- Golden today: `tests/test_agent_golden_e2e.py` private patch at
  `HTTPClient.send_request` (via RequestService import site).
- Jira note: prefer real RequestWorker UI path; mock at HTTP boundary
  (`HTTPClient.send_request`).
- Programming language: Python for fixtures/tests; Markdown for docs.
- Labels: `agent`, `e2e`, `testing`.
- Step 1 review is treated as pre-approved under sprint-task-runner
  autonomy.

## Main Entities and Interactions

| Entity | Role |
| --- | --- |
| Shared HTTP fixture/helper | Installs deterministic stub for agent e2e |
| Canned response catalog | Named outcomes authors reuse or extend |
| HTTP send boundary | Product transport seam stubbed for determinism |
| UI → RequestWorker path | Remains real; exercises product Send |
| Golden scenario | Migrates onto shared layer |
| Env Send scenario | Uses shared layer with seed-oriented canned data |
| Session / seed fixtures | Composed inputs (858 / 857); not owned here |
| Env contract | Shared model (856) this layer implements |

Interaction overview:

1. Author obtains a ready agent session (blank or seeded) via 858.
2. Author selects a canned response from the shared catalog (or adds one).
3. Shared helper/fixture installs the HTTP-boundary stub for the test.
4. Scenario drives Send through the real UI / worker path.
5. Response panel / assertions see the canned outcome deterministically.
6. Tear-down removes the stub so later tests are unaffected.

## Q&A

- Q: Why mock at the HTTP boundary instead of RequestWorker?
  A: Keeps the product UI → worker → response path real while removing
  live network nondeterminism (Jira note / env contract).
- Q: Why a shared layer instead of leaving golden’s private patch?
  A: One-off patches duplicate setup, hide how to add responses, and
  diverge from the env contract’s shared HTTP area.
- Q: Must every agent test stub HTTP?
  A: No. Only scenarios that Send (or otherwise hit transport) need the
  layer. Lifecycle / identity / seed-presence proofs stay as they are.
- Q: Does this story own seed URLs or session fixtures?
  A: No. Consume 857 / 858; provide canned outcomes and stubbing for
  scenarios that Send.
- Q: Is live HTTP allowed as a secondary proof?
  A: Not as the primary agent-flow path. Determinism under offscreen CI
  is mandatory for this pack.
- Q: Who owns failure dumps and full make/CI env-pack productization?
  A: PYPOST-860 and PYPOST-861.
