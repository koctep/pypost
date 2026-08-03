# PYPOST-1027: Lock stretch Jira MCP request IDs in fixture contract tests

## Programming Language

Python for the existing offline fixture-contract tests. The delivered Jira
MCP example collection remains JSON; this task protects its already-shipped
contract rather than changing its feature surface.

## Goals

The curated Jira MCP example collection includes three useful “stretch”
capabilities beyond the original required skill/workflow set: reading an
issue’s worklogs, removing issues from sprint membership by moving them to
the backlog, and finding users assignable to an issue. They are available to
agents today, but the current regression contract can still pass if one is
silently removed or changed while the minimum collection-size check remains
satisfied.

**Business goal:** Preserve reliable access to those three agent workflows by
making their presence and intended Jira operation part of the fixture
contract, so contributors receive a fast, local regression signal before a
curated Jira MCP capability drifts or disappears.

## User Stories

- As an **AI agent using the curated Jira MCP collection**, I want the
  worklog-reading capability to remain available, so I can inspect recorded
  work on an issue without discovering a removed tool at runtime.
- As an **AI agent replanning a sprint**, I want the supported
  remove-from-sprint capability to remain available, so I can move selected
  issues back to the backlog through the curated MCP surface.
- As an **AI agent assigning Jira work**, I want the assignable-user search
  capability to remain available, so I can find an eligible assignee before
  assigning an issue.
- As a **contributor**, I want the fixture contract to identify these three
  protected capabilities and their intended Jira operations, so accidental
  removal, replacement, or route/method drift fails offline CI clearly.
- As a **product steward**, I want this follow-up to stay narrowly focused on
  regression protection, so it does not expand or redesign the curated
  collection merely to increase coverage.

## Definition of Done

- [ ] The offline Jira MCP fixture-contract suite explicitly protects all
      three established stretch capabilities: `jira-get-worklog`,
      `jira-move-issues-to-backlog`, and `jira-search-assignable-users`.
- [ ] The contract verifies each protected capability still represents its
      intended Jira operation, including the relevant HTTP method and Jira
      route marker, rather than asserting its identifier alone.
- [ ] Removing any protected capability, changing its identity, or changing
      its intended operation makes the focused offline contract fail with a
      diagnostic that identifies the broken capability.
- [ ] The existing required Jira MCP capability checks and their regression
      guarantees remain intact.
- [ ] Fixture contract coverage remains offline, deterministic, and safe to
      run without Jira credentials, a running MCP endpoint, or network
      access.
- [ ] The task does not add, remove, rename, or alter the behaviour of the
      Jira MCP collection’s requests; it protects the already-delivered
      surface.
- [ ] Committed fixture examples remain secret-safe and use placeholders
      only.

## Task Description

**Problem:** PYPOST-1026 delivered 21 MCP-exposed Jira requests, including
three stretch capabilities, while its contract protected only a minimum
request count and the original required capability set. The collection can
therefore retain its size and still lose one of those useful agent workflows
without an immediate focused failure.

**Goal:** Strengthen the offline fixture contract so the three accepted
stretch capabilities are explicitly covered as stable, agent-relevant Jira
MCP operations.

**Scope (in):**

- Regression-contract coverage for the three existing stretch Jira MCP
  capabilities and their intended Jira operations.
- Clear failure feedback for accidental capability or operation drift.
- Focused test changes and the task artifacts needed to document and verify
  this contract.

**Scope (out):**

- Adding new Jira MCP tools or filling other Jira capability gaps.
- Changing the collection’s request behaviour, parameters, authentication,
  environment format, or MCP exposure model.
- Exact inventory freezing or broad full-collection parity guarantees unless
  later design review establishes it is necessary to meet this narrow goal.
- Live Jira, browser, UI-import, or network-dependent testing.
- Core PyPost application changes, external Atlassian MCP changes, and
  user-facing documentation expansion.

**Constraints and assumptions:**

- The curated collection is an intentionally partial, skill-oriented Jira
  analog, not a promise of every Atlassian Jira capability.
- The three protected capabilities already exist in the shipped collection;
  this task is a regression-hardening follow-up, not feature delivery.
- Existing native-loader fixture checks are the source of truth for the
  collection contract and should remain the primary validation boundary.
- The existing minimum collection-size check is retained, but is not by
  itself enough to prove the three protected workflows remain available.
- The backlog-move capability is the established supported path for removing
  issues from sprint membership.
- Estimate: 2 story points.

## Main Entities and Interactions

- **Curated Jira MCP collection** — the shipped agent-facing set of Jira
  operations whose established capabilities must not regress silently.
- **Protected stretch capability** — one of worklog lookup, sprint-membership
  removal through backlog movement, or assignable-user search.
- **Fixture contract** — the automated, offline agreement that the collection
  continues to provide the protected capabilities with their intended Jira
  operations.
- **Contributor** — changes fixtures or contract coverage and receives a
  targeted failure when a protected workflow is broken.
- **AI agent** — relies on the protected capabilities during issue tracking,
  sprint replanning, and assignment workflows.

Interaction flow: a contributor changes the curated Jira MCP fixture or its
contract → offline validation checks each protected capability and its
intended operation → a compliant collection remains green → a missing or
drifted protected workflow produces a diagnostic failure before merge →
agents continue to discover the expected Jira action.

## Non-Functional Requirements

- **Regression safety:** coverage must specifically prevent the
  count-floor-only escape hatch for the three protected workflows.
- **Determinism:** validation remains static and offline; it must not require
  a Jira tenant, real credentials, or a live MCP server.
- **Diagnostic quality:** a failure should make it straightforward to tell
  which protected capability or intended operation no longer matches.
- **Secret safety:** no real Jira host, account, token, password, or other
  credential enters fixtures, tests, artifacts, or logs.
- **Scope discipline:** retain the current curated feature surface and avoid
  turning this small debt item into a full inventory snapshot or broad API
  conformance project.

## Q&A

**Q: Why is a minimum request count not enough?**

**A:** A collection can meet the same count after losing a particular stretch
capability or substituting an unrelated request. The three agent workflows
need direct protection.

**Q: Why protect the Jira operation as well as the capability name?**

**A:** An unchanged name can still point to the wrong action. The user value
is reliable worklog lookup, backlog movement for sprint removal, and
assignable-user search — not merely the presence of labels.

**Q: Does this make the collection a complete Jira API mirror?**

**A:** No. The collection deliberately remains a curated, skill-first analog.
This task locks only three already-shipped workflows identified as useful but
previously under-protected.

**Q: Does this require live Jira verification?**

**A:** No. The goal is a deterministic fixture contract. Endpoint freshness
and live credentials are separate concerns and are outside this task.
