# PYPOST-857: Seeded workspace fixtures (collections/envs)

## Goals

Epic [PYPOST-855](https://pypost.atlassian.net/browse/PYPOST-855) needs a
reusable agent e2e environment. The environment contract
([PYPOST-856](https://pypost.atlassian.net/browse/PYPOST-856) /
[agent_e2e_env.md](../../doc/dev/agent_e2e_env.md)) already requires a
**seeded workspace**: known collections, environments, and sample requests
after bootstrap so scenarios do not hand-build that UI state.

Today, agent flows that need meaningful product state either start from a
blank workspace or assemble collections/envs/requests ad hoc per test. That
is slow, brittle, and diverges from the shared env model.

This story’s business goal is to **provide a shared, documented seed** that
loads into an isolated agent lifecycle session so scenario authors and agents
start from a known workspace instead of inventing private bootstrap paths.

## Programming Language

Python (`.cursor/lsr/do-python.md`) for the fixture pack and tests that prove
seed presence after ready. Seed inventory developer documentation under
`doc/dev/` in English Markdown (`.cursor/lsr/do-markdown.md`).

## User Stories

- As a **scenario author / AI agent**, I want a known collection, environment,
  and sample request set present after bootstrap so I do not hand-build that
  UI state before exercising product flows.
- As a **consumer of the agent lifecycle session**, I want seed to land in the
  same isolated temp config/data workspace as the session so my run does not
  touch developer home data or bleed into other scenarios.
- As a **maintainer**, I want a documented seed inventory (what exists after
  bootstrap) so agents and humans share one source of truth for what is
  seeded.
- As a **quality gate**, I want automated proof that seed is present after the
  session is ready (via identity/snapshot observation or an equivalent
  product-facing check) so regressions in seeding are caught early.
- As a **sibling story owner** (PYPOST-858+), I want seed to be a reusable
  fixture area that markers/session packaging can consume later, without this
  story owning markers, HTTP determinism, failure artifacts, or make/CI entry.

## Definition of Done

- A fixture pack (files and/or builders) creates a known collection +
  environment + sample request set aligned with the env contract’s seeded
  workspace expectations.
- Seed integrates with the agent lifecycle session’s isolated temp config/data
  dirs (same isolation mental model as
  [agent_e2e_env.md](../../doc/dev/agent_e2e_env.md) /
  [agent_lifecycle.md](../../doc/dev/agent_lifecycle.md)).
- A documented seed inventory states what exists after bootstrap (at least
  known collections, environments, and sample requests scenarios may assume).
- Automated tests prove seed is present after the session is ready, using
  identity/snapshot observation or an equivalent product-facing check — not
  only an internal “files were written” assertion.
- Scope stays on workspace seed; shared markers/session packaging
  (PYPOST-858), HTTP determinism (PYPOST-859), failure artifacts (PYPOST-860),
  and make/CI env-pack entry (PYPOST-861) remain sibling stories.
- PYPOST-832 drive/observe primitives (lifecycle, identity, actions, snapshot,
  wait, golden) are consumed, not replaced or forked.

## Task Description

**Problem:** Agent e2e scenarios that need collections, environments, or sample
requests either hand-build UI state or rely on ad-hoc setup. The env contract
names a seeded workspace area but does not yet deliver the shared seed or its
inventory.

**Business need:** One reusable seed pack so every env-pack scenario starts from
the same documented workspace contents inside an isolated lifecycle session.

### In Scope

- Fixture pack that produces a known collection + environment + sample request
  set for agent e2e.
- Integration with agent lifecycle session isolation (temp/scoped config and
  data dirs).
- Documented seed inventory: what exists after bootstrap.
- Tests that prove seed is visible/usable after ready (identity/snapshot or
  equivalent product-facing verification).
- Updates to developer docs as needed so the inventory is discoverable from
  the env contract / agent e2e umbrella.

### Out of Scope

- Shared pytest session fixture packaging or `agent_e2e` marker (PYPOST-858).
- Deterministic HTTP fixture layer (PYPOST-859).
- Failure artifact dumps on assert fail (PYPOST-860).
- Make / CI entry for the full env pack (PYPOST-861).
- Replacing or redesigning PYPOST-832 primitives (lifecycle, identity,
  actions, snapshot, wait, golden).
- Redesigning product Collections or Environments features for end users.
- User-facing product docs (`doc/user/`) beyond what seed inventory needs as
  developer-facing reference.
- Live MCP verification against a running PyPost as the primary acceptance
  path for this story.
- Requiring every existing golden/blank-tab scenario to migrate onto seed in
  this story (env contract allows golden as composition proof; seed is the
  preferred path when seeded state is needed).

## Functional Requirements

- FR1: Provide a fixture pack that creates a known workspace seed: at least
  one collection, one environment, and one sample request set scenarios can
  rely on.
- FR2: After bootstrap into an agent lifecycle session, the seeded collections
  are present and selectable in the product UI (or equivalently observable
  via the agent observation path).
- FR3: After bootstrap, the seeded environments are available for variable
  resolution / selection as product environments normally are.
- FR4: After bootstrap, seeded sample requests exist so authors need not
  assemble URL/method/body solely to reach a meaningful product state.
- FR5: Seed must load into the lifecycle session’s isolated temporary
  config/data dirs; it must not depend on the developer’s home workspace or
  leftover data from a prior run.
- FR6: One scenario’s seeded (and subsequently mutated) workspace state must
  not bleed into another scenario’s session.
- FR7: Publish a documented seed inventory describing what exists after
  bootstrap, consistent with the env contract’s seeded-workspace expectations.
- FR8: Automated tests prove seed is present after the session is ready, via
  identity/snapshot (or equivalent product-facing check), not solely by
  asserting internal write success.
- FR9: Seed remains a reusable fixture area consumable by later env-pack
  packaging (PYPOST-858+); this story does not own markers, HTTP stubs,
  failure dumps, or make/CI wiring.

## Non-functional Requirements

- **Shared vocabulary:** “Seed,” “inventory,” and “isolated session workspace”
  match the env contract so agents and humans do not invent private terms.
- **Deterministic contents:** The same documented inventory appears after every
  successful bootstrap (modulo intentional scenario mutation after ready).
- **Isolation:** Seeded data lives only in the session’s scoped dirs; no
  reliance on developer home collections/envs.
- **Observability:** Failure to seed must be detectable by the ready-after
  verification tests (clear fail, not silent empty sidebar).
- **Minimalism:** Smallest shared seed that unblocks env-pack scenarios; not a
  large demo catalog or product sample gallery for end users.
- **Secret safety:** Seed must not introduce real secrets; any sensitive-looking
  placeholders remain test-safe and compatible with existing snapshot/masking
  policy expectations.
- **Non-fork of primitives:** Consume lifecycle/identity/snapshot (as needed for
  proof); do not redefine their contracts.

## Constraints and Assumptions

- Parent epic: [PYPOST-855](https://pypost.atlassian.net/browse/PYPOST-855).
- Depends on environment contract:
  [PYPOST-856](https://pypost.atlassian.net/browse/PYPOST-856) /
  [doc/dev/agent_e2e_env.md](../../doc/dev/agent_e2e_env.md) for inventory
  shape and isolation expectations.
- Foundation primitives: [PYPOST-832](https://pypost.atlassian.net/browse/PYPOST-832)
  (lifecycle session, identity, snapshot, etc.).
- Programming language: Python for fixtures/tests; Markdown for inventory docs.
- “Agent lifecycle session” means the project-supported launch → ready →
  shutdown path used by agent e2e (documented as `AgentAppSession` today),
  including offscreen-capable runs.
- Exact display names and variable keys in the seed are chosen during
  architecture/implementation, but must be fixed in the published inventory
  once delivered.
- Labels: `agent`, `e2e`, `testing`.
- Step 1 review is treated as pre-approved under sprint-task-runner autonomy.

## Main Entities and Interactions

| Entity | Role |
| --- | --- |
| Seeded workspace | Known collections, environments, and sample requests after bootstrap |
| Fixture pack | Reusable producer of that known seed for agent e2e |
| Seed inventory | Documented list of what exists after bootstrap |
| Agent lifecycle session | Isolated launch → ready → shutdown with temp config/data dirs |
| Collection | Group of related saved requests visible in the product sidebar |
| Environment | Named variable set available for selection / resolution |
| Sample request | Seeded request (method/URL/body as applicable) scenarios may open or use |
| Scenario | Automated agent/harness flow that consumes seed then asserts |
| Env contract | Shared model (PYPOST-856) this seed implements for the seed area |
| PYPOST-832 primitives | Lifecycle / identity / snapshot etc. — consumed for session and proof |

Interaction overview:

1. Scenario (or later shared packaging) obtains an isolated agent lifecycle
   session.
2. Fixture pack seeds the session workspace with the documented inventory.
3. Session becomes ready; seeded collections, environments, and sample
   requests are available.
4. Verification (tests) observes seed via identity/snapshot or equivalent
   product-facing check.
5. Scenario drives and observes using PYPOST-832 capabilities; tear-down
   releases scoped dirs so seed does not leak to the next run.
6. Later siblings (858+) may package seed into a shared marker/session entry
   without redefining the inventory owned here.

## Q&A

- Q: Why seed instead of hand-building UI state in each scenario?
  A: Hand-building is slow, brittle, and conflicts with the env contract’s
  requirement for a shared, documented workspace after bootstrap.
- Q: Why does this depend on PYPOST-856?
  A: The contract defines inventory shape, isolation, and how scenarios
  consume a ready env. This story implements the seed fixture area against
  that model.
- Q: Does this story own the shared `agent_e2e` marker / session fixture?
  A: No. PYPOST-858 owns packaging/markers. This story delivers seed that
  packaging can consume.
- Q: Must seed use real network hosts?
  A: No. Seed provides known product state; HTTP determinism for outbound
  calls is PYPOST-859. Seed values should be test-safe placeholders.
- Q: How is “seed is present” proven?
  A: After ready, automated checks must observe seed via identity/snapshot
  (or equivalent product-facing path), not only assert that seed files were
  written internally.
- Q: Is golden blank-tab setup deprecated by this story?
  A: No. Golden remains a valid composition proof. Env scenarios that need
  seeded workspace state should prefer this seed once available.
- Q: Does “AgentAppSession” in the Jira text lock a specific API forever?
  A: Requirements bind to the project-supported lifecycle session with temp
  isolation. Today that is `AgentAppSession`; architecture must integrate
  with that session (or its documented equivalent) without forking lifecycle.
- Q: How large must the seed catalog be?
  A: Minimal but complete for the contract: known collection(s),
  environment(s), and sample request(s). Not a full product demo library.
