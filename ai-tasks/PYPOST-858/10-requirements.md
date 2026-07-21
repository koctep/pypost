# PYPOST-858: Shared pytest session fixture + agent_e2e mark

## Goals

Epic [PYPOST-855](https://pypost.atlassian.net/browse/PYPOST-855) needs a
reusable agent e2e environment. The environment contract
([PYPOST-856](https://pypost.atlassian.net/browse/PYPOST-856) /
[agent_e2e_env.md](../../doc/dev/agent_e2e_env.md)) already names a **shared
marker / session fixture packaging** area so scenarios share one env bootstrap
path instead of each test hand-rolling lifecycle launch, dirs, and optional
seed.

Today, agent UI e2e tests each construct an agent lifecycle session (and,
where needed, seed) privately. Selection for `make test-agent-e2e` is a
hard-coded file list only. That duplicates bootstrap, drifts from the env
contract’s “obtain ready env through the shared pack” path, and leaves the
`agent_e2e` marker unfinished (also called out under
[PYPOST-854](https://pypost.atlassian.net/browse/PYPOST-854) docs/make
follow-ups).

This story’s business goal is to **package one shared pytest entry** —
registered `agent_e2e` mark plus a fixture that yields a ready agent lifecycle
session (and seed when available) — so scenario authors migrate onto one
bootstrap path and maintainers can select the pack via marker and/or the
documented file list.

## Programming Language

Python (`.cursor/lsr/do-python.md`) for fixture packaging, marker registration,
and tests. Developer documentation under `doc/dev/` in English Markdown
(`.cursor/lsr/do-markdown.md`).

## User Stories

- As a **scenario author / AI agent**, I want one shared way to obtain a ready
  agent lifecycle session (with seed when I need seeded workspace state) so I
  do not reinvent bootstrap in every test.
- As a **maintainer**, I want `@pytest.mark.agent_e2e` registered and
  documented so the pack is selectable and discoverable without mistyped,
  unregistered marks.
- As a **quality gate**, I want `make test-agent-e2e` to select the pack via
  the marker and/or a documented file list so the make entry stays reliable
  while the pack grows.
- As an **owner of existing agent tests**, I want to migrate onto the shared
  fixture without losing coverage so bootstrap consolidation does not regress
  lifecycle, identity, actions, snapshot, wait, golden, or seed proofs.
- As a **sibling story owner** (PYPOST-859+), I want markers/session packaging
  to leave HTTP determinism, failure artifacts, and full env-pack make/CI
  ownership to their stories, while absorbing overlapping marker/make
  improvements called out in PYPOST-854 where this story already owns them.

## Definition of Done

- `agent_e2e` marker is registered in project pytest config and documented for
  humans and agents.
- A shared pytest fixture yields a ready agent lifecycle session
  (`AgentAppSession` or the project-supported equivalent), and yields or
  composes seed when available (consume PYPOST-857; do not re-own seed
  inventory).
- Existing agent e2e tests can migrate onto the fixture without losing
  coverage of the current harness modules under `make test-agent-e2e`.
- `make test-agent-e2e` can select via the marker and/or a documented file
  list (both paths remain valid for authors).
- Marker/make improvements overlapping PYPOST-854 for `agent_e2e` are absorbed
  here rather than left as a second bootstrap path.
- Scope stays on shared packaging/selection; HTTP determinism (PYPOST-859),
  failure artifacts (PYPOST-860), and full env-pack make/CI entry (PYPOST-861)
  remain sibling stories.
- PYPOST-832 drive/observe primitives and PYPOST-857 seed APIs are consumed,
  not replaced or forked.

## Task Description

**Problem:** Agent e2e scenarios each bootstrap privately; there is no
registered `agent_e2e` mark or shared fixture that yields a ready session
(and seed). Selection is file-list-only, which diverges from the env
contract’s shared packaging area.

**Business need:** One documented bootstrap and selection path so every env-pack
scenario (and migratable existing agent tests) obtains a ready session the
same way.

### In Scope

- Register and document the `agent_e2e` pytest marker.
- Shared pytest fixture that yields a ready agent lifecycle session.
- Compose with available seed (PYPOST-857) so seeded scenarios use the same
  packaging path.
- Enable existing agent harness tests to migrate onto the fixture without
  coverage loss.
- Make `test-agent-e2e` selectable via marker and/or documented file list;
  document both.
- Absorb PYPOST-854 overlap that is specifically about the `agent_e2e` marker
  / related make selection for this packaging story.

### Out of Scope

- Redefining seed inventory or `write_agent_e2e_seed` ownership (PYPOST-857).
- Deterministic HTTP fixture layer (PYPOST-859).
- Failure artifact dumps on assert fail (PYPOST-860).
- Full env-pack make/CI entry as a separate product (PYPOST-861), beyond what
  this story needs so `test-agent-e2e` can use marker and/or file list.
- Replacing or redesigning PYPOST-832 primitives (lifecycle, identity,
  actions, snapshot, wait, golden).
- Requiring every non-agent or blank-tab-only proof to become seeded.
- Live MCP verification against a running PyPost as the primary acceptance
  path.
- User-facing product docs (`doc/user/`).

## Functional Requirements

- FR1: Register an `agent_e2e` pytest marker in project configuration so it is
  official (no unregistered-mark warnings) and listed in pytest marker help.
- FR2: Document the marker (what it means, who applies it, how to select with
  `-m`) in developer docs tied to the env contract / agent e2e umbrella.
- FR3: Provide a shared pytest fixture that yields a ready agent lifecycle
  session suitable for agent e2e scenarios (offscreen-capable, isolated
  temp/scoped config and data dirs per the env contract).
- FR4: When seed is available, the packaging path can yield a session whose
  workspace includes the documented PYPOST-857 seed (or an equivalent
  composition that scenarios can rely on without hand-building UI state).
- FR5: Existing agent tests under the current `make test-agent-e2e` file list
  can migrate onto the shared fixture without losing the coverage those
  modules provide today.
- FR6: `make test-agent-e2e` can select the pack via the `agent_e2e` marker
  and/or continue to support a documented explicit file list (authors may use
  either).
- FR7: Isolation: one scenario’s mutable session/workspace state must not
  bleed into another’s (same mental model as the env contract and lifecycle
  isolation).
- FR8: Packaging remains consumable by later siblings (HTTP, artifacts,
  make/CI) without owning their fixture areas.
- FR9: Absorb overlapping PYPOST-854 marker/`agent_e2e` selection concerns into
  this delivery so a second conflicting bootstrap path is not required for the
  marker alone.

## Non-functional Requirements

- **Shared vocabulary:** “agent_e2e,” “ready session,” “seed,” and “env pack”
  match the env contract and umbrella docs.
- **Discoverability:** Marker registration + docs make the pack findable via
  `pytest --markers` and `doc/dev/` without tribal knowledge.
- **Isolation:** Fixture packaging must not rely on developer home data or
  leave mutable state for the next scenario.
- **Migration safety:** Moving existing tests onto the fixture must preserve
  observable coverage (ready gate, identity, actions, snapshot, wait, golden,
  seed proofs as applicable).
- **Minimalism:** Smallest shared packaging that unblocks the env-pack
  bootstrap path; do not redesign the whole harness.
- **Non-fork of primitives:** Consume `AgentAppSession` / seed writer /
  observation APIs; do not redefine lifecycle or seed inventory contracts.
- **Make consistency:** Prefer Makefile targets with offscreen Qt; do not
  introduce undocumented shell-only recipes as the primary path.

## Constraints and Assumptions

- Parent epic: [PYPOST-855](https://pypost.atlassian.net/browse/PYPOST-855).
- Env contract: [PYPOST-856](https://pypost.atlassian.net/browse/PYPOST-856) /
  [doc/dev/agent_e2e_env.md](../../doc/dev/agent_e2e_env.md) — this story
  implements the “session + agent_e2e marker” fixture area.
- Seed available from: [PYPOST-857](https://pypost.atlassian.net/browse/PYPOST-857)
  (`write_agent_e2e_seed` / inventory docs).
- Foundation: [PYPOST-832](https://pypost.atlassian.net/browse/PYPOST-832)
  lifecycle and related primitives.
- Overlap: [PYPOST-854](https://pypost.atlassian.net/browse/PYPOST-854) —
  absorb marker/make selection improvements here when they coincide with AC.
- Programming language: Python for fixtures/tests; Markdown for docs.
- “Agent lifecycle session” means the project-supported launch → ready →
  shutdown path (documented as `AgentAppSession` today), including
  offscreen-capable runs.
- Jira wording “session fixture” means packaging for the agent lifecycle
  session, not a requirement to share one mutable app instance across all
  tests if that would violate isolation.
- Labels: `agent`, `e2e`, `testing`.
- Step 1 review is treated as pre-approved under sprint-task-runner autonomy.

## Main Entities and Interactions

| Entity | Role |
| --- | --- |
| `agent_e2e` marker | Tag selecting env-pack / agent e2e scenarios |
| Shared session fixture | Yields a ready agent lifecycle session for scenarios |
| Seed composition | Optional/known workspace seed from PYPOST-857 |
| Agent lifecycle session | Isolated launch → ready → shutdown |
| Scenario / agent test | Consumes fixture; drives/observes via 832 primitives |
| `make test-agent-e2e` | Make entry selecting via marker and/or file list |
| Env contract | Shared model (PYPOST-856) this packaging implements |
| Existing harness modules | Migratable coverage onto the shared fixture |
| PYPOST-854 overlap | Marker/make follow-ups absorbed when they match AC |

Interaction overview:

1. Author marks a scenario `agent_e2e` (and/or places it on the documented
   file list).
2. Scenario requests the shared fixture.
3. Fixture bootstraps an isolated ready agent lifecycle session; when seed is
   required/available, seed is composed into that session’s workspace.
4. Scenario drives and observes using PYPOST-832 capabilities.
5. Tear-down releases scoped dirs so state does not leak.
6. Maintainers run `make test-agent-e2e` via marker selection and/or the
   documented file list.

## Q&A

- Q: Why a shared fixture instead of leaving each test to construct
  `AgentAppSession`?
  A: Private bootstrap duplicates env setup, drifts from the contract, and
  blocks later siblings from composing on one path.
- Q: Why register a marker if a file list already works?
  A: Markers make the pack selectable and discoverable as it grows; the AC
  requires both marker and/or documented file list.
- Q: Does “session fixture” require one shared app for the whole pytest
  process?
  A: No. Requirements require a ready lifecycle session per packaging use
  with isolation. Architecture may choose fixture scope that preserves
  isolation for mutating scenarios.
- Q: Does this story own seed contents?
  A: No. PYPOST-857 owns inventory and `write_agent_e2e_seed`. This story
  packages seed when available.
- Q: What about PYPOST-854?
  A: Absorb overlapping `agent_e2e` marker / make selection work here so the
  marker is not left as a separate unfinished bootstrap path.
- Q: Must every existing golden/blank-tab test become seeded?
  A: No. Fixture packaging must support ready sessions; seed composition is
  for scenarios that need seeded workspace state. Migration must not lose
  coverage of blank or golden proofs that intentionally differ.
- Q: Who owns HTTP stubs and failure dumps?
  A: PYPOST-859 and PYPOST-860. This story leaves hooks/composition points
  possible but does not implement those areas.
- Q: Is live MCP the acceptance path?
  A: No. Automated pytest + make selection and documented marker/fixture
  behavior are the acceptance path.
