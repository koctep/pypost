# PYPOST-1029: Parameterize pagination on Jira MCP board/sprint list tools

## Programming Language

Python for offline fixture-contract tests. The curated Jira MCP collection is
JSON; this task changes agent-facing pagination inputs on three shipped list
requests and keeps their offline contracts green.

## Goals

Agents that list boards, board sprints, or sprint issues through the curated
Jira MCP example cannot choose page size (or page offset) today: those query
values are fixed in the collection, and one list tool advertises no agent
inputs at all. Contributors also keep that list tool on a special empty-input
allowlist only because pagination is hard-coded.

**Business goal:** let agents control how many (and which page of) boards,
sprints, or sprint issues they fetch from the curated tools, so large Jira
sites remain usable without fixture edits, and the empty-input exception for
board listing can retire once pagination is agent-facing.

## User Stories

- As an **AI agent listing Jira boards**, I want to choose how many boards
  (and which page) to fetch, so I can cover large sites without relying on a
  fixed page size baked into the example.
- As an **AI agent listing sprints on a board**, I want the same page-size
  and page-offset control, so I am not stuck at the curated default when a
  board has many sprints.
- As an **AI agent listing issues in a sprint**, I want page-size (and page
  offset where the example still uses offset pagination) as declared tool
  inputs, so I can page through membership without editing the collection.
- As a **contributor**, I want offline tests to lock the pagination input
  agreement and the narrowed empty-input allowlist, so regressions fail
  locally without a Jira tenant or network.
- As a **product steward**, I want this limited to the three named list
  tools and their contracts, so the task does not expand the curated Jira
  surface or redesign MCP runtime defaults.

## Definition of Done

- [x] Agents can supply page size for `jira-list-boards`,
      `jira-list-board-sprints`, and `jira-get-sprint-issues` through declared
      MCP inputs (not only hard-coded query values).
- [x] Where this story includes page offset for those list tools, it is also
      declared as an agent-facing MCP input bound into the request query.
- [x] `jira-list-boards` no longer ships with empty MCP parameter metadata;
      its project-key binding via the companion environment remains.
- [x] The fixed empty-input allowlist no longer includes `jira-list-boards`
      once that request declares pagination inputs.
- [x] Offline fixture contracts fail clearly if pagination inputs drift or the
      allowlist is wrong, without live Jira, network, or secrets.
- [x] Existing capability, auth, env, placeholder, and numeric-identifier
      guarantees for the Jira MCP example remain intact.
- [x] Developer docs describe the new pagination inputs and the narrowed
      allowlist.

## Task Description

**Problem:** Follow-up from PYPOST-1026 TD-3. Board and sprint list requests
in the curated Jira MCP collection hard-code pagination query values.
`jira-list-boards` ships with empty MCP parameter metadata and therefore
remains on the PYPOST-1028 fixed-input allowlist. Agents cannot tune page
size (or offset) without editing fixtures.

**Scope (in):**

- Expose page size (and page offset where included by architecture) as
  agent-facing inputs on the three named list requests.
- Replace empty MCP parameter metadata on board listing with declared
  pagination inputs while keeping env-based project scoping.
- Update offline contracts and the empty-input allowlist accordingly.
- Document the change for developers.

**Scope (out):**

- New Jira capabilities beyond pagination on those three requests.
- Live Jira integration or UI import e2e as acceptance criteria.
- Redesigning template defaulting for omitted optional MCP arguments.
- Migrating Agile list endpoints to token-based pagination as a product
  change in this story (note only if research surfaces it).

## Q&A

| Question | Answer |
| -------- | ------ |
| Why expose pagination at all? | Large boards/sprints truncate at a fixed page size; agents need control without editing fixtures. |
| Why touch the empty-input allowlist? | Board listing only stayed allowlisted because `mcp_params` was empty; pagination inputs remove that escape hatch. |
| Why not change runtime defaults? | Fixture contracts already enforce agent-driven query ↔ `mcp_params`; a fixture-only change matches TD-3 and keeps scope small. |
| Related debt? | PYPOST-1026 TD-3; PYPOST-1028 allowlist notes PYPOST-1029 removes `jira-list-boards`. |
