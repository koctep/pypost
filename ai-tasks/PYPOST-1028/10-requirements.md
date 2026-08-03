# PYPOST-1028: Strengthen Jira MCP fixture contracts for environment, auth, and MCP parameters

## Programming Language

Python for the existing offline fixture-contract tests. The shipped Jira MCP
collection and companion environment remain JSON inputs; this task verifies
their established agreement rather than changing their feature surface.

## Goals

The curated Jira MCP example is meant to be safe for agents to import and use
as a dependable starting point. Its existing fixture checks prove that the
files load, but they do not fully protect the agreement between the collection,
its companion environment, request authentication, and the inputs exposed to
agents. A contributor could accidentally break one of those agreements while
the fixture still imports.

**Business goal:** give contributors a fast, local, and clear regression
signal when a Jira MCP request can no longer receive the configuration,
authentication, or agent input it needs, so agents retain a reliable curated
Jira workflow without discovering fixture drift at runtime.

## User Stories

- As an **AI agent using the Jira MCP example**, I want all required shared
  configuration values to be available from the companion environment, so a
  request does not fail because its declared template value is missing.
- As an **AI agent**, I want every Jira request to use the published Jira
  credential convention, so the imported collection consistently authenticates
  in the intended way without exposing a real credential in the fixture.
- As an **AI agent invoking a request**, I want each agent-provided value used
  by a request to be declared as an available tool input, so I can discover
  and supply the required value rather than encountering an implicit missing
  parameter.
- As a **contributor**, I want focused offline checks to identify the affected
  request and agreement when a fixture changes, so I can correct drift before
  merge without a Jira tenant, network access, or live secrets.
- As a **product steward**, I want this follow-up to stay limited to contract
  hardening, so it does not expand the curated Jira capability set or turn
  into a full Jira API parity project.

## Definition of Done

- [x] The companion Jira environment supplies every shared configuration value
      referenced by the curated Jira MCP collection, including the base URL and
      credential values already used by the shipped example.
- [x] Non-secret shared configuration stays agent-usable, while secrets stay
      marked sensitive.
- [x] Every shipped Jira MCP request is checked to follow the published
      credential convention.
- [x] The contract detects any request that refers to an agent-provided value
      without declaring the corresponding MCP input.
- [x] Agent-driven query or body values must be declared as agent-facing
      inputs, or the request is an explicit fixed-input exception rather than
      silently escaping the check.
- [x] A relevant configuration, authentication, or MCP-input regression fails
      a focused offline test with a diagnostic that identifies the affected
      request or missing agreement.
- [x] Existing capability, import, placeholder-hygiene, and secret-safety
      guarantees remain intact.
- [x] The validation is deterministic and needs no Jira credentials, network
      endpoint, running MCP server, browser, or UI import.
- [x] The task does not add, remove, rename, or alter the behavior of Jira MCP
      collection requests, redesign authentication, or add live integration
      testing.

## Task Description

**Problem:** Current fixture checks establish that the Jira MCP collection and
its environment import successfully, but they leave gaps in the agreements
that make the collection usable by agents: whether every shared template value
is available from the companion environment, whether each request retains the
standard credential usage, and whether agent-facing inputs are declared when
a request needs them.

**Scope (in):**

- Offline regression coverage for collection-to-environment shared
  configuration agreement.
- Offline regression coverage for the established request authentication
  convention.
- Offline regression coverage that relates values requested from an agent to
  the inputs published for that request.
- Explicit, documented treatment of intentionally fixed-input requests.
- Focused test and task-artifact changes needed to protect these agreements.

**Scope (out):**

- Adding, removing, renaming, or changing the behavior of Jira MCP requests.
- New Jira workflows, broad inventory freezing, or complete Jira/MCP API
  parity.
- Changing the existing credential format, creating real credentials, or
  adding secrets to any fixture, test, artifact, or log.
- Live Jira, browser, UI-import, or network-dependent validation.
- Parameterizing pagination or other separate agent-ergonomics work already
  tracked outside this debt item.
- Core PyPost runtime, import/export redesign, and user-facing documentation
  expansion unless a later step identifies a genuine requirement gap.

**Constraints and assumptions:**

- The Jira MCP example is a curated, skill-oriented collection, not a promise
  of complete Atlassian Jira coverage.
- The existing collection, companion environment, and authentication
  convention are the accepted starting point; this is regression hardening,
  not a feature change.
- The existing offline fixture-contract agreement protects these behaviors;
  this task does not mandate a particular loader, suite layout, or
  architecture.
- A deliberately fixed-input request may be retained only when its exception
  is explicit and reviewable; it must not make missing agent inputs invisible.
- Committed examples use placeholders only and must remain secret-safe.
- Estimate: 3 story points.

## Main Entities and Interactions

- **Curated Jira MCP collection** — the shipped set of agent-facing Jira
  workflows whose usability agreement must remain intact.
- **Companion Jira environment** — the example configuration that provides
  shared values and identifies which values are sensitive.
- **Jira request** — one agent-callable workflow that relies on shared
  configuration, the published authentication convention, and possibly agent
  input.
- **MCP input contract** — the discoverable agreement between a request and
  the values an AI agent is expected to provide.
- **Fixture contract** — the automated offline agreement that protects the
  collection and environment from silent drift.
- **Contributor** — changes a fixture or test and receives a focused failure
  before merge when the agreement is broken.

Interaction flow: a contributor changes the collection, environment, or
fixture contract → offline validation checks the shared configuration,
authentication, and agent-input agreements → compliant fixtures remain green
→ a missing or inconsistent agreement produces a diagnostic before merge →
agents continue to import and invoke the intended Jira workflows reliably.

## Non-Functional Requirements

- **Determinism:** checks remain static and offline, without a Jira tenant,
  live MCP service, browser, or network access.
- **Secret safety:** no real Jira host, account, token, password, or other
  credential is introduced in source, fixtures, test output, or task
  artifacts.
- **Diagnostic quality:** a failed contract identifies the missing shared
  value, the affected request, or the undeclared agent input clearly enough to
  repair the fixture.
- **Regression safety:** current import, required-capability, placeholder, and
  secret-handling checks remain protected.
- **Scope discipline:** avoid redesigning the curated collection or expanding
  into pagination and broad feature coverage work that belongs to other
  backlog items.
- **Maintainability:** intended fixed-input exceptions are visible and small,
  so reviewers can distinguish an intentional constraint from accidental
  missing input metadata.

## Q&A

**Q: Why is successful fixture import not enough?**

**A:** Import proves the JSON is readable, but not that every request still
has the configuration, authentication convention, and agent-visible inputs it
needs to work as a curated workflow.

**Q: Does this task change the Jira collection or add capabilities?**

**A:** No. It protects the existing collection against silent drift. New
features and pagination ergonomics are separate backlog work.

**Q: Why are fixed-input requests treated explicitly?**

**A:** Some requests intentionally do not need an agent-supplied value. Making
that decision visible preserves a useful safety check while avoiding false
positives for the accepted exception.

**Q: Does this require real Jira credentials or a live Jira tenant?**

**A:** No. The value of this task is a deterministic offline contract that
continues to use placeholders and never calls a live service.
