# PYPOST-856: Spec — agent e2e environment contract

## Goals

The agent UI stack from epic
[PYPOST-832](https://pypost.atlassian.net/browse/PYPOST-832) (lifecycle,
identity, actions, snapshot, wait, golden) lets agents drive and observe
PyPost. Epic
[PYPOST-855](https://pypost.atlassian.net/browse/PYPOST-855) adds a reusable
**agent e2e environment** on top of that stack: seeded workspace, shared
fixtures and markers, deterministic HTTP, failure artifacts, and a make/CI
entry.

Without a single written **environment contract**, agents and humans disagree
on what is seeded, how tests stay isolated, what offscreen/CI assumes, and
how scenarios consume the env. Sibling stories (PYPOST-857–861) would then
implement fixtures against conflicting mental models.

This story’s business goal is to **describe before implement**: one shared
definition of the agent e2e environment so later fixture work has a clear
inventory and clear boundaries versus PYPOST-832 primitives.

## Programming Language

Markdown (`.cursor/lsr/do-markdown.md`) for the contract developer doc under
`doc/dev/` (new page and/or extension of
[agent_e2e.md](../../doc/dev/agent_e2e.md)). No application or test code in
this story; siblings implement in Python.

## User Stories

- As a **maintainer / AI agent**, I want one environment contract that states
  what is seeded, isolation rules, offscreen/CI assumptions, and how
  scenarios consume the env so I do not invent a private bootstrap path.
- As a **fixture story owner** (PYPOST-857–861), I want the contract to list
  required fixture areas — workspace seed, HTTP determinism, markers,
  failure artifacts, make/CI entry — so each sibling knows its slice of the
  shared model.
- As a **consumer of PYPOST-832 primitives**, I want explicit boundaries:
  the env pack builds on lifecycle/identity/actions/snapshot/wait/golden; it
  does not replace those primitives or redefine their APIs.
- As a **scenario author**, I want to know how a scenario is expected to
  obtain a ready environment (session + seed + HTTP determinism + markers)
  without hand-building UI state or one-off HTTP patches as the primary path.
- As a **CI / local runner**, I want the contract to state that the env pack
  is runnable via project-standard make/CI entry under offscreen Qt, not via
  undocumented shell-only recipes.

## Definition of Done

- A developer document exists under `doc/dev/` (dedicated page and/or clear
  extension of `agent_e2e.md`) that describes the agent e2e **environment
  model**.
- The doc states explicit **boundaries versus PYPOST-832 primitives**
  (lifecycle, identity, actions, snapshot, wait, golden): what the env pack
  owns vs what it only consumes.
- The doc lists required fixture areas and their business purpose:
  - workspace seed (collections / environments / sample requests)
  - HTTP determinism for agent flows
  - shared markers / session fixture consumption
  - failure artifacts (e.g. snapshot dump on assert fail)
  - make / CI entry for the env pack
- The doc describes isolation rules and offscreen/CI assumptions at a
  business level sufficient for siblings to implement against.
- The doc describes how scenarios are expected to **consume** the
  environment (bootstrap → ready env → act/observe → tear down), without
  prescribing concrete APIs beyond naming the fixture areas.
- This story delivers **documentation only**; no fixture, marker, HTTP layer,
  artifact hook, or make/CI wiring is implemented here (siblings PYPOST-857–861).

## Task Description

**Problem:** PYPOST-832 delivered drive/observe primitives and packaging
(`agent_e2e.md`, `make test-agent-e2e`). PYPOST-855 needs a reusable env on
top of that, but there is no shared written model of seed, isolation,
offscreen/CI assumptions, or scenario consumption. Ad-hoc golden setup
(blank tab, one-off HTTP mock) does not scale to a documented env pack.

**Business need:** One environment contract so agents, humans, and sibling
implementers share the same definition before code lands.

### In Scope

- Environment contract developer documentation under `doc/dev/`.
- Env model content: what is seeded; isolation expectations; offscreen and
  CI assumptions; how scenarios consume the env.
- Explicit boundary section versus PYPOST-832 primitives.
- Inventory of required fixture areas aligned with sibling stories:
  workspace seed, HTTP determinism, markers/session fixture, failure
  artifacts, make/CI entry.
- Cross-links from the existing agent e2e umbrella so the env contract is
  discoverable (link updates only as needed for this story’s doc).

### Out of Scope

- Implementing workspace seed fixtures (PYPOST-857).
- Implementing shared pytest session fixture or `agent_e2e` marker
  (PYPOST-858).
- Implementing deterministic HTTP fixture layer (PYPOST-859).
- Implementing failure artifact dumps (PYPOST-860).
- Wiring make/CI for the env pack (PYPOST-861).
- Replacing or redesigning PYPOST-832 primitives (lifecycle, identity,
  actions, snapshot, wait, golden).
- Live MCP verification against a running PyPost (separate testing path).
- User-facing product docs (`doc/user/`).
- Network MCP packaging beyond what the env pack narrative needs to mention
  as out of scope for the epic.

## Functional Requirements

- FR1: Publish a developer-facing environment contract under `doc/dev/` that
  describes the agent e2e environment model.
- FR2: The contract states what a seeded workspace is expected to provide at
  a business level (known collections, environments, and sample requests
  available after bootstrap) so scenarios need not hand-build that UI state.
- FR3: The contract states isolation rules so one scenario’s data and session
  do not bleed into another’s (temp/scoped config and data expectations at
  business level).
- FR4: The contract states offscreen and CI assumptions (headless Qt path,
  project-standard run entry, determinism expectations) so local and CI
  runners share one mental model.
- FR5: The contract describes how scenarios consume the env: obtain a ready
  environment (session + seed + HTTP determinism as applicable), drive and
  observe via existing agent UI capabilities, then release the environment.
- FR6: The contract explicitly separates env-pack ownership from PYPOST-832
  primitive ownership (consume, do not replace).
- FR7: The contract lists the required fixture areas named in acceptance
  criteria (workspace seed, HTTP determinism, markers, failure artifacts,
  make/CI entry) and maps each to its sibling story for implementation.
- FR8: Deliverable is documentation only; implementation of listed fixtures
  remains with siblings.

## Non-functional Requirements

- **Shared vocabulary:** Terms (seed, isolation, offscreen/CI assumptions,
  env consumption, fixture areas) are unambiguous for agents and humans.
- **Discoverability:** The contract is reachable from the existing agent e2e
  umbrella documentation.
- **Boundary clarity:** Readers can tell env-pack concerns from PYPOST-832
  drive/observe concerns without reading sibling tickets.
- **Implementability:** Fixture inventory is specific enough that PYPOST-857–861
  can implement without re-specifying the env model.
- **Minimalism:** Spec only what the env pack must agree on; no product
  feature design and no premature API prescriptions.
- **Secret safety (narrative):** Failure-artifact expectations note that
  dumps must not expose secrets contrary to existing snapshot/masking
  policy (detail owned by PYPOST-860).

## Constraints and Assumptions

- Parent epic: [PYPOST-855](https://pypost.atlassian.net/browse/PYPOST-855).
- Foundation epic (primitives): [PYPOST-832](https://pypost.atlassian.net/browse/PYPOST-832).
- Existing umbrella: [doc/dev/agent_e2e.md](../../doc/dev/agent_e2e.md);
  golden flow and ad-hoc HTTP mock today are not the full env pack.
- Documentation language: English Markdown under `doc/dev/`.
- Siblings implement: PYPOST-857 (seed), PYPOST-858 (fixture + marker),
  PYPOST-859 (HTTP determinism), PYPOST-860 (failure artifacts),
  PYPOST-861 (make/CI).
- “Environment contract” means a shared description of seed, isolation,
  assumptions, consumption, and fixture inventory — not a runtime product
  “Environments” feature redesign.
- Step 1 review is treated as pre-approved under sprint-task-runner
  autonomy.

## Main Entities and Interactions

| Entity | Role |
| --- | --- |
| Agent e2e environment | Shared model: seed + isolation + assumptions + consumption path |
| Environment contract | Developer doc that defines that model for agents and humans |
| Seeded workspace | Known collections, environments, and sample requests after bootstrap |
| Isolation rule | Expectation that scenarios do not share mutable data/session state |
| Offscreen / CI assumption | Headless Qt and project-standard run/determinism expectations |
| Scenario | Automated agent/harness flow that consumes the env then asserts |
| PYPOST-832 primitives | Lifecycle, identity, actions, snapshot, wait, golden — consumed, not replaced |
| Fixture area | Named capability slice (seed, HTTP, markers, artifacts, make/CI) for siblings |

Interaction overview:

1. Reader opens the environment contract (via `doc/dev/` / agent e2e umbrella).
2. Contract defines seed inventory expectations, isolation, and offscreen/CI
   assumptions.
3. Contract lists fixture areas; siblings implement them later.
4. Scenario authors consume a ready env, then use PYPOST-832 capabilities to
   drive and observe; they do not redefine those primitives.
5. On failure, artifact expectations (sibling) make diagnosis possible without
   weakening secret-handling policy.

## Q&A

- Q: Why write a contract before fixtures?
  A: So PYPOST-857–861 implement one shared env definition instead of five
  private bootstraps. Describe before implement is the epic’s stated why.
- Q: Does this story implement any fixtures?
  A: No. Documentation only. Siblings implement seed, markers, HTTP,
  artifacts, and make/CI.
- Q: How does this differ from PYPOST-832 / `agent_e2e.md`?
  A: PYPOST-832 owns drive/observe primitives and their packaging umbrella.
  This contract owns the **environment pack** model on top: seed, isolation,
  determinism, artifacts, make/CI for that pack — with explicit non-overlap.
- Q: Is the golden blank-tab + one-off HTTP mock the environment?
  A: No. That proves composition of primitives. The env pack adds reusable
  seed and shared fixture layers; the contract must say how scenarios should
  consume those instead of hand-building state as the primary path.
- Q: Must the doc invent concrete pytest fixture names or module paths?
  A: No at requirements level. Name the fixture **areas** and consumption
  expectations; concrete wiring is architecture/sibling implementation.
- Q: New page vs extend `agent_e2e.md`?
  A: Either is acceptable per Jira AC; architecture/docs step chooses the
  shape as long as the env model is complete and discoverable.
- Q: Why list make/CI in a docs-only story?
  A: The contract must inventory that the env pack is incomplete without a
  first-class run entry; PYPOST-861 implements it against this inventory.
