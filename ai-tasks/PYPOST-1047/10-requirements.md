# PYPOST-1047: Expand jira_mcp — delete sprint and remove from sprint

## Programming language

JSON for the curated jira-mcp example collection under `examples/`, English
Markdown for companion documentation (`.cursor/lsr/do-markdown.md`), and
Python only where existing fixture contract, smoke, or regression tests must
change (`.cursor/lsr/do-python.md`). No new product features in application
code. No changes to the external Atlassian MCP server.

## Goals

PyPost already ships a curated **jira-mcp** example collection that local AI
agents can use via PyPost MCP to work with Jira boards and sprints: they can
list, create, and update sprints, add issues to a sprint, and move issues to
the backlog. That surface is still incomplete for real sprint hygiene work.

Today, agents that rely on PyPost MCP **cannot delete a sprint** (for example
an unclosed or mistakenly created sprint that should not remain on the
board). The external Atlassian MCP also does not provide delete-sprint, so
there is no MCP path for this action at all. Separately, agents need a
**clear, discoverable way to remove issues from sprint membership**, with the
same practical parity they already have for adding issues to a sprint and
moving issues to the backlog — whether that means documenting and locking an
existing backlog-move capability as the supported path, or filling a gap if
that path is not enough for agents to complete the job.

**Business goal:** Let PyPost MCP agents **delete sprints** and **remove
issues from sprints** through the curated jira-mcp example collection, so
sprint lifecycle and membership management are complete enough for agent
workflows without depending on the external Atlassian MCP for these actions.

## User Stories

- As an **AI agent using PyPost MCP**, I want to delete a sprint that should
  not remain on the board (for example an unclosed or mistakenly created
  sprint), so that I can clean up sprint planning without leaving the MCP
  session or asking a human to delete it in the Jira UI.
- As an **AI agent using PyPost MCP**, I want a clear way to remove one or
  more issues from a sprint’s membership, so that I can replan work with the
  same confidence I already have when adding issues to a sprint or moving
  them to the backlog.
- As a **contributor working with project agent skills**, I want delete-
  sprint and remove-from-sprint capabilities available via the curated
  jira-mcp collection, so agent sprint workflows are not blocked by gaps in
  the external Atlassian MCP.
- As a **reader of examples and MCP docs**, I want delete-sprint and
  remove-from-sprint (or the documented equivalent for removing membership)
  listed wherever the jira-mcp tool surface is described, so I know agents
  can perform these actions and which tool to use.
- As an **operator / contributor**, I want fixture contract and
  smoke/regression expectations updated for the expanded jira-mcp surface,
  so CI continues to prove the collection is importable, MCP-exposed where
  intended, and free of real credentials.
- As a **product steward**, I want this story limited to the PyPost jira-mcp
  collection and its companion docs/tests — not a change to the external
  Atlassian MCP, and not a new in-app product feature beyond curated
  examples.

## Definition of Done

- [x] An agent using the curated jira-mcp collection via PyPost MCP can
      **delete a sprint** (including an unclosed sprint that should not remain
      on the board), with an agent-facing description and parameters consistent
      with the rest of the collection.
- [x] An agent using the curated jira-mcp collection via PyPost MCP can
      **remove issues from sprint membership** in a clear, discoverable way
      that is on parity with adding issues to a sprint and moving issues to
      the backlog (reuse an existing backlog-move path if it fully satisfies
      that need; otherwise fill the gap).
- [x] Wherever user or developer docs list jira-mcp MCP tools (or coverage of
      that collection), delete-sprint and the supported remove-from-sprint
      path are reflected accurately.
- [x] Fixture / contract expectations for the jira-mcp collection (counts,
      MCP exposure, placeholder hygiene) are updated and green.
- [x] Smoke / regression coverage for the jira-mcp collection stays
      consistent with existing patterns and covers the new or clarified
      capabilities.
- [x] Fixtures remain secret-safe (placeholders only; no real credentials).
- [x] The external Atlassian MCP is unchanged; this story is PyPost
      collection, docs, and tests only.

## Task Description

**Problem:** Agents that use PyPost MCP (and those that would otherwise fall
back to the external Atlassian MCP) have no MCP way to **delete a sprint**.
Sprint membership removal is also incomplete or unclear relative to add-to-
sprint and move-to-backlog, so agents cannot fully manage sprint planning
through MCP alone.

**Goal:** Extend the curated jira-mcp example collection (and companion docs
and tests as needed) so agents can delete sprints and remove issues from
sprints via PyPost MCP, with documentation and contract coverage that keep
the expanded surface trustworthy.

**Scope (in):**

- Curated jira-mcp collection updates so agents can delete a sprint with
  clear agent-facing guidance and parameters, matching existing collection
  conventions for auth, templating, and MCP exposure.
- A clear, agent-usable capability to remove issues from sprint membership,
  keeping practical parity with add-to-sprint and move-to-backlog; prefer
  documenting and locking an existing backlog-move path if it is sufficient.
- Updates to contract / fixture expectations for the collection (counts,
  MCP exposure, related assertions).
- Updates to developer and/or user MCP docs that list or describe jira-mcp
  tools, so the new or clarified capabilities are visible.
- Smoke / regression coverage consistent with existing jira-mcp collection
  tests.

**Scope (out):**

- Any change to the external Atlassian MCP server or its configuration.
- New PyPost application product features beyond curated example collection,
  docs, and tests.
- Full coverage of every Jira Software Agile capability unrelated to sprint
  delete and sprint membership removal.
- Replacing or redesigning collection/environment import formats.

**Constraints and assumptions:**

- The jira-mcp collection already exposes list/create/update sprint and
  move-to-backlog; this story builds on that baseline rather than
  redesigning the collection.
- External Atlassian MCP lacks delete-sprint; closing that gap for agents
  is a primary driver, but delivery is via the PyPost collection only.
- Auth, templating, placeholder credentials, and MCP-exposure conventions
  already used by the collection remain the standard; this story does not
  invent a new example style.
- Estimate: 3 story points.

## Main Entities and Interactions

- **Sprint** — a time-boxed planning container on a Jira board; agents need
  to create, update, list, and (with this story) delete sprints that should
  not remain.
- **Issue** — a work item that can belong to a sprint or to the backlog;
  agents need to add issues to a sprint and remove them from sprint
  membership.
- **Backlog** — the pool of issues not currently committed to a sprint;
  moving issues here is the established way to clear sprint membership when
  that path is sufficient.
- **jira-mcp collection** — the curated set of MCP-exposed Jira requests
  agents import and use via PyPost MCP; the delivery vehicle for this story.
- **AI agent (PyPost MCP client)** — the primary actor that discovers and
  calls the tools to manage sprints and membership.
- **Human operator / contributor** — imports examples, fills placeholders,
  and relies on docs and CI contracts that the collection stays valid.

Interaction flow: an agent (or human demo) needs to clean up or replan a
sprint → discovers delete-sprint and remove-from-sprint (or documented
backlog-move) tools in the jira-mcp surface → calls them with the same
auth/templating patterns as other jira-mcp tools → the sprint is deleted or
issues leave the sprint → docs and contract tests reflect that these
capabilities exist and remain exposed.

## Non-Functional Requirements

- **Parity and discoverability**: remove-from-sprint must be as clear to an
  agent as add-to-sprint and move-to-backlog; agents should not have to
  guess which tool clears membership.
- **Consistency**: new or clarified tools follow the same collection
  conventions (auth, placeholders, MCP exposure, agent-facing descriptions)
  as the rest of jira-mcp.
- **Secret safety**: examples continue to use placeholders only; no real
  tokens or personal credentials enter the repository.
- **Regression safety**: contract and smoke/regression coverage must catch
  missing MCP exposure, broken counts, or undocumented gaps for these
  capabilities.
- **Scope discipline**: delivery stays collection/docs/tests-only; external
  Atlassian MCP and core product behavior remain untouched.

## Q&A

**Q:** Why is this needed if PyPost already has sprint list/create/update and
move-to-backlog?

**A:** Agents still cannot delete a sprint via MCP (PyPost or Atlassian), and
remove-from-sprint is not clearly on parity with add-to-sprint. Without
delete and a clear membership-removal path, agents cannot finish common
sprint hygiene and replanning work through MCP alone.

**Q:** Why not change the external Atlassian MCP instead?

**A:** The ticket scopes this to the PyPost jira-mcp collection only.
Delivering via PyPost examples closes the agent gap for users of PyPost MCP
without depending on upstream Atlassian MCP changes.

**Q:** Is “remove issues from a sprint” always a new tool?

**A:** Not necessarily. If the existing move-to-backlog capability fully
satisfies removing sprint membership for agents, this story may document and
lock that path as the supported answer. If it does not, the collection must
fill the gap so agents still have a clear, discoverable action. Architecture
decides the concrete shape; requirements only require the business outcome.

**Q:** Does this story change how collections or MCP servers work in the
product?

**A:** No. It extends curated example content and companion docs/tests. No
new product features and no Atlassian MCP changes.

**Q:** What must docs and tests guarantee?

**A:** Docs that list jira-mcp tools (or coverage) must include delete-sprint
and the supported remove-from-sprint path. Contract/fixture and
smoke/regression tests must stay aligned with the expanded surface so CI
continues to prove importability, MCP exposure, and placeholder hygiene.
