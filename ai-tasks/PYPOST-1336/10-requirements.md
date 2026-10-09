# PYPOST-1336: Decompose epic PYPOST-1335 into child tasks

## Goals

Epic [PYPOST-1335](https://pypost.atlassian.net/browse/PYPOST-1335) ("Built-in collections
source for MCP server creation") describes a user-visible capability that is too large and too
cross-cutting to deliver as one ticket. Today a user who wants an MCP endpoint for Jira, GitLab
or GitHub must either import the example collection into the workspace or connect the examples
library; both paths leave the user maintaining a copy that never receives fixes or new tools
shipped with later PyPost versions.

The epic's business goal is that a user can create an MCP server directly from a curated,
PyPost-maintained collection that is always up to date with the installed application, while
still being able to take a private, editable copy when they need to customize it.

This story's business goal is to turn that epic into a **plannable, trackable backlog**: a set of
small, estimated, independently deliverable Jira child tasks linked to the epic and placed in the
current sprint, plus written decomposition notes that explain how the epic scope maps onto those
tasks. Without this, the sprint cannot run the epic through the Top-Down workflow task by task,
progress on the epic cannot be measured, and scope items risk being dropped or duplicated.

**The product of this task is the decomposition itself** (notes and Jira issues), not
production code. The epic's own business requirements (below) are the **input** that the
decomposition must cover.

## Input: Epic PYPOST-1335 Business Scope

The decomposition must cover every item of the epic scope:

- **E1 — Built-in source**: a new "Built-in" source option in the MCP server creation/editing
  dialog, offered next to the existing Collection (workspace) and Library sources.
- **E2 — Bundled collections**: read-only curated collections shipped with the application:
  GitLab MCP, Jira MCP and GitHub MCP.
- **E3 — Single source of files**: the bundled collections are shipped as a resource of the
  application package and are the same files the official examples library uses; there must be
  one copy of each collection, not two diverging copies.
- **E4 — Read-only marker**: built-in collections are visibly marked as read-only to the user.
- **E5 — Copy for editing**: the user can create an editable copy of a built-in collection.
- **E6 — Paired environment**: the environment that belongs to a built-in collection is copied
  as an editable environment for the user (credentials and per-user values are never edited in
  the shipped resource).
- **E7 — Reference by identifier and auto-update**: an MCP server created from the Built-in
  source refers to the collection by a stable identifier and uses the newest shipped version of
  that collection after the application starts (an upgraded PyPost brings updated tools without
  user action).
- **E8 — Out of scope**: no migration of existing MCP servers that already point at the examples
  library or at workspace copies; those keep working unchanged.

Dependency context: [PYPOST-1334](https://pypost.atlassian.net/browse/PYPOST-1334) (GitHub MCP
collection and environment) is **done** (commit `31f2b25a`); GitHub, GitLab and Jira MCP fixtures
and their environments already exist in the examples library. PYPOST-1334 must still be linked to
the epic as a child so the epic reflects all contributing work.

## User Stories

- **US1 (planner / sprint runner)**: As the sprint runner, I want the epic split into child tasks
  that each fit one Top-Down workflow run, so that I can execute and close them one by one inside
  the sprint.
- **US2 (product owner)**: As the product owner, I want each child task to state its business
  outcome, acceptance criteria and story points, so that I can judge progress and remaining effort
  of the epic.
- **US3 (product owner)**: As the product owner, I want every epic scope item (E1–E8) traceable to
  at least one child task (or to an explicit out-of-scope note), so that nothing is lost or done
  twice.
- **US4 (developer executing a child task)**: As a developer, I want each child task to list the
  tasks it depends on and its boundaries, so that I can start it without reverse-engineering the
  epic and without stepping into a sibling's scope.
- **US5 (team)**: As a team member, I want the decomposition reasoning recorded in the repository
  next to other task artifacts, so that later readers understand why the epic was split this way.
- **US6 (end user, indirect)**: As a PyPost user, I want the resulting plan to deliver the
  Built-in source end to end (pick a built-in collection, see it is read-only, copy it if needed,
  get an editable environment, receive updates on upgrade), so that the epic's promise is met.

## Definition of Done

PYPOST-1336 is done when:

1. **Coverage**: each epic scope item E1–E7 is covered by at least one child task, and E8 is
   recorded as an explicit exclusion (no child task migrates existing servers). A coverage table
   in the notes maps E1–E8 to child task keys.
2. **Granularity**: each new child task is small enough for one Top-Down run (Steps 1–8 and
   commit) and is independently verifiable through `make` targets; no child task exceeds
   **8 story points**; a task that would exceed it is split further.
3. **Estimation**: every new child task has a Fibonacci story-point estimate set in Jira
   (estimated per the `jira-create-issue` procedure).
4. **Content of each child task**: summary, business goal, scope boundaries (in / out),
   acceptance criteria, and dependencies on sibling tasks (by Jira key) are present in the Jira
   description.
5. **Ordering**: dependencies between child tasks form an acyclic order; the notes give a
   recommended execution order so that each task can start once its predecessors are done.
6. **Epic linking**: every new child task is linked to epic PYPOST-1335 as its parent, and
   **PYPOST-1334** is linked to PYPOST-1335 as a child as well.
7. **Sprint rule**: every new child task is added to the same sprint as PYPOST-1336
   (**sprint 2025, "Built-in MCP Collections"**). PYPOST-1334 (already done) is not moved.
8. **Decomposition notes**: the notes are stored under `ai-tasks/PYPOST-1335/` and contain: epic
   scope summary, the coverage table, the list of child tasks with keys, story points and
   dependencies, the recommended execution order, open questions/assumptions handed to child
   tasks, and the out-of-scope statement.
9. **No production change**: the task changes no production code, tests or bundled fixtures;
   only `ai-tasks/` artifacts are added.
10. **Quality gate**: `make verify-ai-tasks` passes with the new artifacts present.

## Task Description

### Programming Language

N/A for this task: the deliverables are Markdown notes and Jira issues. The child tasks it
produces will be implemented in **Python** (PyPost desktop client and automated tests) plus
JSON/YAML bundled collection fixtures, executed exclusively through `make` targets (repo rule in
`AGENTS.md`).

### Problem

The epic mixes several kinds of change that differ in risk and in who verifies them: packaging of
shipped content, user-visible dialog changes, persisted server configuration semantics, read-only
presentation, copy-for-editing behavior for collections and environments, and update-on-start
behavior. A single ticket would be too large to estimate, review, or execute in one workflow run,
and the dependency on PYPOST-1334 must be made explicit in Jira.

### Current Product Context (scope scan only, no design)

- The MCP server dialog currently offers two collection sources for a local server: a workspace
  collection and a connected library (`pypost/ui/dialogs/mcp_servers_dialog.py`).
- A persisted MCP server configuration identifies its collection either as a workspace
  collection or as a library collection (`pypost/models/settings.py`,
  `McpServerConfiguration`); there is no built-in identity today.
- The official examples library ("PyPost Official Examples", id `pypost-examples`) is exposed as
  a read-only library read from the repository `examples/` directory, which lies outside the
  `pypost/` package; an editable copy of the whole library can already be made
  (`pypost/core/predefined_library.py`, `pypost/core/library_manager_service.py`).
- Jira, GitLab and GitHub MCP collections and their environments exist in `examples/`
  (GitHub added by PYPOST-1334).

These facts bound the scope of the decomposition; how to realize the epic is decided in the
child tasks, not here.

### Scope

In scope:

- Analysis of epic PYPOST-1335 and the existing product behavior it builds on.
- Defining child tasks (business outcome, boundaries, acceptance criteria, dependencies,
  estimate).
- Creating the child tasks in Jira, linking them and PYPOST-1334 to the epic, and adding the new
  ones to sprint 2025.
- Writing the decomposition notes in `ai-tasks/PYPOST-1335/`.

Out of scope:

- Implementing any part of the epic (code, fixtures, packaging, tests, user docs).
- Migration of existing MCP servers (epic exclusion E8).
- Changing PYPOST-1334's content or status.
- Re-planning other epics or sprints.

### Main Entities (business view)

- **Epic PYPOST-1335** — the capability to be delivered; owner of the child tasks.
- **Child task** — a Jira Story/Task under the epic: summary, business goal, boundaries,
  acceptance criteria, dependencies, story points, sprint.
- **Built-in collection** — curated, read-only MCP collection shipped with PyPost (GitLab, Jira,
  GitHub), with a stable identifier and a version that changes with the application.
- **Paired environment** — the environment shipped with a built-in collection; the user receives
  an editable copy.
- **Editable copy** — a user-owned copy of a built-in collection or environment that no longer
  receives shipped updates.
- **MCP server configuration** — the user's persisted MCP endpoint; for the Built-in source it
  refers to a built-in collection by identifier.
- **Examples library** — the official examples library that must share the same collection files
  as the built-in source.
- **Sprint 2025 "Built-in MCP Collections"** — the sprint that must contain all new child tasks.
- **Decomposition notes** — `ai-tasks/PYPOST-1335/` artifact explaining the split.

### Non-Functional Requirements

- **Traceability**: every child task links back to the epic; the notes link to every child task.
- **Consistency**: child task descriptions use the epic terminology (Built-in source, built-in
  collection, paired environment, Copy for editing) consistently.
- **Testability**: each child task's acceptance criteria are verifiable offline through `make`
  targets or an explicit GUI check described in the task.
- **Process compliance**: Jira operations go through the Jira MCP integration; if it is
  unavailable or fails, work stops and the failure is reported (hardstop rule in `AGENTS.md`).

### Constraints and Assumptions

- Child tasks must be added to sprint 2025; this is a hard rule from the PYPOST-1336 description.
- Estimates use the Fibonacci scale (1, 2, 3, 5, 8); 8 is the upper bound per child task.
- Assumption: PYPOST-1334 is already done and counts toward coverage of E2 (GitHub collection
  content); it needs only linking, not re-estimation.
- Assumption: the decomposition may also define child tasks for user documentation and tests of
  the new source if they are not naturally part of a functional task.
- Assumption: notes live in `ai-tasks/PYPOST-1335/` even though PYPOST-1335 is an epic, because
  the task description names that location explicitly.

## Q&A

- **Q**: Why decompose at all instead of implementing the epic directly?
  **A**: The epic spans packaging, persisted configuration, dialog UX, read-only presentation,
  copy flows and update-on-start; it cannot be estimated or executed in one Top-Down run, and the
  sprint runner works one Jira task at a time.
- **Q**: Is PYPOST-1334 still a blocker?
  **A**: No. It is done (commit `31f2b25a`); it is linked to the epic for traceability only.
- **Q**: Does "picks up new versions on app start" require migrating existing servers?
  **A**: No. Only servers created from the Built-in source get this behavior; existing servers
  are explicitly out of scope (E8).
- **Q (open, for Step 2)**: Should the examples library keep reading from `examples/` once the
  collections become a package resource, or should the examples library be served from the
  package resource (single source of files, E3)? The decomposition must name which child task
  owns this decision.
- **Q (open, for Step 2)**: Does "Copy for editing" produce a workspace collection or a library
  entry, and does it switch the existing server to the copy or create a new server? To be
  assigned to a child task as an explicit decision point.
- **Q (open, for Step 2)**: Which environment does a Built-in server use before the user copies
  the paired environment — is copying mandatory at server creation?
- **Q (open, for Step 2)**: Is `mcp.json` (local probing collection) also a built-in collection,
  or only GitLab, Jira and GitHub as the epic lists?
