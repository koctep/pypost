# PYPOST-901: Optional GUI multi-URL Send using Mapping router

## Goals

[PYPOST-868](https://pypost.atlassian.net/browse/PYPOST-868) delivered an
optional URL→canned-response Mapping router on the shared agent e2e HTTP stub
layer, with unit proofs for multi-URL hit, miss, and restore. No GUI Send
scenario yet drives **two different resolved URLs under one Mapping stub** in
a single test.

Maintainers and scenario authors therefore lack automated proof that the
router works through the real UI → Send → response-panel path — only through
isolated unit calls. Unit coverage satisfied PYPOST-868 acceptance; this
optional debt raises **end-to-end confidence** that multi-URL stub routing
behaves correctly when URLs are filled and Sends are triggered from the
desktop harness.

Source: [PYPOST-868](https://pypost.atlassian.net/browse/PYPOST-868)
tech debt → [PYPOST-901](https://pypost.atlassian.net/browse/PYPOST-901).

## Programming Language

Python 3.10+ for the agent e2e GUI scenario. Developer docs in English
Markdown.

## User Stories

- As a **scenario author / AI agent**, I want a small marked `agent_e2e`
  example that Sends twice to distinct resolved URLs under one Mapping stub,
  so I can copy a proven multi-URL GUI flow instead of inferring it from unit
  tests alone.
- As a **maintainer**, I want CI to prove the Mapping router works through
  the real Send path (UI fill → Send → response panel), not only at the stub
  boundary in isolation.
- As a **pack owner**, I want existing single-canned and unit router proofs
  to remain unchanged — this story adds optional GUI confidence, not a
  replacement for PYPOST-868 coverage.
- As a **desktop user** (indirect), I want no product UX change — test-harness
  hygiene only.

## Definition of Done

- A small marked `agent_e2e` scenario exists that:
  - installs a Mapping stub with at least two distinct resolved URL keys and
    matching canned outcomes;
  - performs **two Sends** to those distinct URLs within one stub scope;
  - asserts **response-panel outcomes** (status and body) match the canned
    result for each Send.
- The scenario runs under the project’s standard offscreen / `agent_e2e`
  workflow with a bounded, CI-safe wall-clock budget.
- Maintainers can discover the scenario from existing agent e2e HTTP /
  golden / seed documentation (minimal doc touch as needed).
- No intentional product UX or live-network behavior change.
- Steps 1–8 artifacts exist under `ai-tasks/PYPOST-901/`.

Acceptance (from Jira): **Small `agent_e2e` scenario that Sends twice to
distinct resolved URLs with a Mapping stub and asserts panel outcomes.**

## Task Description

**Problem:** The shared HTTP layer supports a URL→canned Mapping router
(PYPOST-868), proven by unit tests. Golden, env GET, and seed POST GUI
scenarios each use a **single** canned result per Send. No GUI scenario
exercises two different URLs routed by one Mapping install in a single test.

**Business need:** Close optional low-priority testing debt so multi-URL
Mapping stub routing is proven on the real agent Send path — raising
maintainer confidence without duplicating PYPOST-868’s unit contract.

### In Scope

- One small marked `agent_e2e` GUI scenario that:
  1. Uses a Mapping stub covering at least two distinct resolved URLs.
  2. Fills or selects each URL (and method/body if needed) via the agent UI.
  3. Sends twice and waits for each response to settle.
  4. Asserts each Send’s status and canned body appear in the response panel.
- The scenario stays small, deterministic, and discoverable for authors.
- Minimal developer-doc mention so authors can find and run the scenario.
- Completing Steps 1–8 workflow artifacts.

### Out of Scope

- Changing the Mapping router implementation or match rules (PYPOST-868).
- method+URL compound map keys (sibling [PYPOST-902](https://pypost.atlassian.net/browse/PYPOST-902)).
- Migrating all existing single-canned scenarios to Mapping stubs.
- Full multi-URL / multi-method regression matrix.
- Redesigning the product Send or HTTP client path.
- User-facing product docs (`doc/user/`).
- Creating Jira Debt tickets from this task’s Step 7 (orchestrator handles
  follow-ups separately).

## Functional Requirements

- FR1: A marked `agent_e2e` scenario installs a Mapping stub with at least
  two distinct resolved URL keys and distinct canned outcomes.
- FR2: The scenario performs two Sends within one Mapping stub scope, each
  targeting a different resolved URL.
- FR3: After each Send, the scenario waits for the response panel to settle
  before asserting outcomes.
- FR4: Each Send’s response panel shows the status and body matching the
  canned outcome mapped to that URL.
- FR5: The scenario runs deterministically under the project’s offscreen GUI /
  agent e2e path (no live external HTTP as the primary path).
- FR6: The scenario completes within a bounded, CI-safe wall-clock budget.
- FR7: Existing single-canned GUI Send scenarios and PYPOST-868 unit router
  proofs remain valid; this story adds coverage without removing them.
- FR8: Maintainers can discover how to run the scenario from developer docs
  (or an existing umbrella table).

## Non-Functional Requirements

- **Minimalism:** One small scenario is enough; not a full multi-URL suite.
- **Boundedness:** Send settle waits must not hang CI indefinitely.
- **Isolation:** Stub install/teardown must not leak across tests.
- **Discoverability:** Authors can find the scenario without reverse-engineering
  tests alone.
- **Consistency:** Behavior and author experience align with sibling Send
  scenarios where applicable.
- **No product impact:** Harness / test / docs hygiene only.

## Constraints and Assumptions

- Parent / source: [PYPOST-868](https://pypost.atlassian.net/browse/PYPOST-868);
  debt note in `ai-tasks/PYPOST-868/60-tech-debt.md`.
- Mapping router and catalog entries (e.g. seed GET / seed POST canned pairs)
  already exist; this task adds GUI proof, not new router API.
- Map keys must equal the resolved URL string the stub sees at Send time
  (typically the URL filled in the UI) — same contract as PYPOST-868 docs.
- Blank-session fill or seeded-session navigation are both acceptable starting
  points if they keep the scenario small and deterministic.
- Labels: `agent`, `e2e`, `tech-debt`, `testing`. Priority: Low.
- Autonomous batch: user approval gates pre-approved; no Jira updates or git
  commit from this execution unless orchestrator requests later steps.

## Main Entities and Interactions

| Entity | Role |
| --- | --- |
| Mapping stub | Routes each Send’s URL to a canned HTTP outcome |
| Resolved URL | URL string filled or loaded in the request editor |
| Canned outcome | Deterministic status/body expected in the panel |
| Agent e2e GUI scenario | Drives UI fill, Send, wait, and panel asserts |
| Response panel | Shows status and body after each Send |
| Maintainer / author | Runs scenario in CI or copies the pattern |

Interaction overview:

1. Scenario launches PyPost and reaches UI ready (blank or seeded).
2. Scenario installs a Mapping stub covering two distinct resolved URLs.
3. Scenario fills or selects the first URL (and method/body if needed), Sends,
   waits, and asserts panel matches the first canned outcome.
4. Scenario fills or selects the second URL, Sends again under the same stub,
   waits, and asserts panel matches the second canned outcome.
5. Stub scope ends cleanly so later tests are unaffected; harness completes
   cleanup.

## Q&A

| Q | A |
| --- | --- |
| Why add GUI coverage if unit tests already prove the router? | PYPOST-868 AC was unit-only; this optional debt raises confidence that URL resolution + UI Send + panel display work together. |
| Must both Sends use seed GET and seed POST catalog entries? | Not mandated — any two distinct resolved URLs with catalog canned pairs are fine; seed GET/POST are natural candidates already in inventory. |
| Blank session or seeded session? | Either is acceptable if the scenario stays small and deterministic (per source debt note). |
| Product impact? | None — test harness / docs only. |
| Why not ticket method+URL keys here? | Owned by sibling [PYPOST-902](https://pypost.atlassian.net/browse/PYPOST-902). |
| Source? | [PYPOST-868 tech debt](../PYPOST-868/60-tech-debt.md) → [PYPOST-901](https://pypost.atlassian.net/browse/PYPOST-901). |
