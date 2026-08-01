# PYPOST-918: Out-of-process MCP packaging for UI actions

## Goals

UI action primitives (click, fill, select, send key) exist today as an
**in-process** agent capability for harnesses and tests that already share
the application process. Product MCP, by contrast, exposes collection HTTP
requests as tools for external agents talking to a running PyPost.

Maintainers and agents need a **clear packaging answer** for whether (and
when) those UI action primitives may be offered out-of-process over a local
agent/MCP-style bridge — without ever treating that surface as the same
thing as product MCP HTTP tools. Without that clarity, people may:

- Assume UI actions are already (or should become) product MCP tools.
- Mix drive-the-UI automation into the product MCP tool catalog.
- Leave an open follow-up with no attributable packaging path or deferral.

Business value: one discoverable, documented decision — either a packaging
path for out-of-process UI-action MCP, or an explicit deferred epic link —
so contributors do not invent ad-hoc bridges or conflate agent UI drive
with product request tools.

Source: [PYPOST-851](https://pypost.atlassian.net/browse/PYPOST-851) TD-3
(originally [PYPOST-836](https://pypost.atlassian.net/browse/PYPOST-836)
follow-up item 5). Sibling packaging-clarity pattern:
[PYPOST-922](https://pypost.atlassian.net/browse/PYPOST-922).

## Programming Language

Python (`.cursor/lsr/do-python.md`) if any minimal contract locks are needed
to keep documentation from drifting. Developer docs in English Markdown
(`.cursor/lsr/do-markdown.md`). No change to the product MCP HTTP tool
surface is required for this debt.

## User Stories

- As a **maintainer**, I want a documented packaging path **or** a deferred
  epic link for out-of-process MCP of UI actions, so the follow-up is
  closed with an attributable answer rather than an unspoken “maybe later.”
- As a **contributor / AI agent**, I want docs to state clearly that UI
  action primitives are not product MCP HTTP tools, so I do not add drive
  actions to the product MCP catalog or assume they are already there.
- As a **reader of UI actions / MCP docs**, I want the separation between
  in-process agent UI drive and product MCP request tools to remain
  explicit, including how out-of-process packaging (if any) relates.
- As a **sibling story owner** (actions, select, fill, agent e2e), I want
  this debt to own packaging clarity / deferral only — not new UI
  primitives or product MCP features.
- As a **product MCP consumer**, I want collection HTTP tools to stay a
  separate surface so UI automation packaging never changes what external
  agents see as PyPost request tools.

## Definition of Done

- Either:
  - a **documented packaging path** for out-of-process MCP of UI action
    primitives exists and is discoverable from relevant agent / MCP docs,
    **or**
  - a **deferred epic link** is recorded in the appropriate developer docs
    (and attributable to this ticket) so the work is explicitly postponed
    rather than vague.
- Docs (and any packaging notes) enforce the hard constraint: **no mixing**
  UI-action out-of-process packaging with product MCP HTTP tools.
- Existing in-process UI actions docs continue to state they are not
  network MCP tools on the product MCP server.
- No requirement to ship a live out-of-process bridge in this ticket if
  deferral is the chosen acceptance path.
- Unticketed follow-ups (if any) are recorded only in this task’s
  `60-tech-debt.md` (no Jira ticket creation in this run).

Acceptance (from Jira): **Documented packaging path or deferred epic
link; no mixing with product MCP HTTP tools.**

## Task Description

**Problem:** PYPOST-836 delivered in-process UI action primitives and left
“out-of-process MCP wrapper / packaging” as follow-up, with an explicit
warning to keep product MCP HTTP tools separate. That follow-up was
ticketed as PYPOST-851 TD-3 → this debt. Docs already say actions are
not product MCP tools, but there is still no closed packaging path or
named deferral epic for out-of-process exposure.

**Business need:** Close the packaging-clarity gap so maintainers know
whether out-of-process MCP for UI actions is in scope now, documented as a
path, or deferred to a linked epic — without ever merging that story into
the product MCP request-tool surface.

### In Scope

- Documented packaging path **or** deferred epic link for out-of-process
  MCP packaging of UI action primitives (Jira acceptance).
- Explicit, durable wording that product MCP HTTP tools remain a separate
  surface (no mixing).
- Light updates to sibling agent / MCP developer docs that still leave
  out-of-process packaging as an open footnote without a closed answer.
- Minimal automated contract checks if needed so the documented answer
  (path or deferral) does not silently disappear.

### Out of Scope

- Implementing a live out-of-process agent/MCP bridge unless chosen as the
  packaging path and still limited to documentation-level packaging for
  this Lowest debt (full bridge delivery belongs to a larger epic if
  deferred).
- Changing product MCP HTTP tools, collection-as-tools behaviour, or the
  product MCP server’s tool catalog.
- New UI action primitives (click/fill/select/send key already exist
  in-process).
- Redesigning agent lifecycle, identity, snapshot, or wait APIs.
- Live MCP verification redesign or broader agent-e2e make packaging
  (owned elsewhere, e.g. PYPOST-922 / agent e2e docs).
- User-facing product documentation (`doc/user/`).
- Creating Jira Debt tickets (unticketed items only in `60-tech-debt.md`).
- Commit or Jira status transitions / worklog MCP writes (orchestrator).

## Functional Requirements

- FR1: Maintainers can find either a documented packaging path for
  out-of-process MCP of UI actions, or a deferred epic link that owns that
  work.
- FR2: Documentation states that UI action packaging must not mix with
  product MCP HTTP tools.
- FR3: In-process UI actions remain documented as not product network MCP
  tools.
- FR4: The chosen answer (path or deferral) is attributable to this ticket
  in developer docs so the debt can be closed.
- FR5: Sibling docs that previously waved at “later packaging / MCP bridge”
  point at the closed answer rather than an open, unowned footnote.
- FR6: Product MCP consumers’ view of request tools is unchanged by this
  story.

## Non-Functional Requirements

- **Discoverability:** A maintainer can answer “is out-of-process MCP for
  UI actions packaged or deferred?” from developer docs without reading
  old tech-debt tables.
- **Separation:** Product MCP and agent UI drive stay conceptually and
  documentedly distinct.
- **Minimalism:** Prefer documenting a path or linking a deferral epic over
  building a large bridge in this Lowest-priority debt.
- **Stability:** If contract locks are added, they stay fast and do not
  require a live GUI or live MCP session beyond what existing doc/packaging
  checks need.
- **No production → tests imports:** Production agent code must not import
  from `tests/`.

## Constraints and Assumptions

- Programming language: Python for optional doc/contract locks; Markdown
  for docs.
- Parent / source debt: PYPOST-851 TD-3 ← PYPOST-836 follow-up item 5.
- UI actions today are in-process only; product MCP exposes collection HTTP
  requests as tools — these remain separate business surfaces.
- Jira acceptance allows **either** packaging path **or** deferred epic
  link; both satisfy DoD if the no-mixing constraint holds.
- Agent e2e make packaging (e.g. PYPOST-839 / PYPOST-922) is related
  discoverability work but does not itself close out-of-process MCP for UI
  actions.
- Step 1 review is treated as pre-approved under sprint-task-runner
  autonomy (no approval gate / no Jira updates in this step).

## Main Entities and Interactions

| Entity | Role |
| --- | --- |
| UI action primitives | In-process agent ability to click, fill, select, send key |
| Product MCP HTTP tools | External-agent tools for collection HTTP requests |
| Out-of-process packaging | Future or documented path to expose UI actions outside the app process |
| Deferred epic | Named backlog owner if packaging is postponed |
| Packaging documentation | Discoverable answer (path or deferral) attributable to this debt |
| Maintainers / agents | Readers who must not conflate the two MCP-related surfaces |

Interaction overview:

1. Maintainer asks whether UI actions can/should be exposed out-of-process
   via MCP-style packaging.
2. Docs provide either a packaging path or a deferred epic link.
3. Docs reaffirm product MCP HTTP tools stay separate — UI drive packaging
   does not become (or merge into) that catalog.
4. In-process harnesses continue to use UI actions as today.
5. Product MCP consumers continue to see only product request tools.

## Q&A

- Q: Why is this a business requirement and not “just add an MCP tool”?
  A: The underlying need is packaging **clarity and separation**: decide
  and document how (or that we defer) out-of-process UI-action exposure
  without polluting the product MCP request-tool surface. Shipping a tool
  into product MCP would violate the acceptance constraint.

- Q: Must this ticket implement an out-of-process bridge?
  A: No. Acceptance is satisfied by a documented packaging path **or** a
  deferred epic link, plus no mixing with product MCP HTTP tools.

- Q: Are in-process UI actions already product MCP tools?
  A: No. Docs already state they are an in-process agent API, not network
  MCP tools on the product MCP server. This ticket must preserve that
  separation.

- Q: Does agent e2e `make` packaging (PYPOST-839 / PYPOST-922) close this?
  A: No. Those stories package in-process agent UI e2e. This debt is about
  out-of-process MCP packaging of UI actions (or explicit deferral).

- Q: Can UI actions be added to the product MCP tool catalog to “package”
  them?
  A: No. Acceptance forbids mixing with product MCP HTTP tools.

- Q: Why not only update consolidated debt notes?
  A: The business value is a usable, documented packaging answer
  maintainers follow — not a debt-table footnote alone.
