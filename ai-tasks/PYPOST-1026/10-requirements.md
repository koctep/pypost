# PYPOST-1026: Expand jira-mcp example collection for Atlassian MCP parity

## Programming language

JSON for expanded importable example fixtures under `examples/`, English
Markdown for import/use and coverage documentation
(`.cursor/lsr/do-markdown.md`), and Python only where existing fixture
contract tests or tiny fixture/docs fixes must change
(`.cursor/lsr/do-python.md`). No new product features in application code.

## Goals

PyPost already ships a **starter** jira-mcp example collection and companion
environment from [PYPOST-1017](https://pypost.atlassian.net/browse/PYPOST-1017):
a small set of MCP-exposed Jira Cloud requests that readers can import, fill
with placeholders, and adapt. That starter is useful, but it does **not**
cover the Jira capabilities that project agent workflows and skills actually
rely on when they talk to the external Atlassian MCP Jira server.

Those workflows need a much broader practical surface: issue lifecycle
(search, read, create, update, assign, comment, transition, worklog), field
discovery, epic linking, boards and sprints (list, create, update, assign
issues), and related project metadata — not a full dump of every Jira Cloud
capability, and not niche Service Desk / ProForma areas unless they are
cheap to include.

**Business goal:** Deliver a curated, importable **jira-mcp** PyPost example
collection that is a **practical analog** of the Atlassian MCP Jira tool
surface used by in-repo agent skills and workflows — so readers (and local
agents using PyPost MCP) can expose equivalent tools from collection
requests, with environment placeholders and no committed secrets. Expand
the PYPOST-1017 baseline rather than redesigning product import formats or
replacing the external Atlassian MCP configuration.

## User Stories

- As an **end user**, I want an expanded jira-mcp example collection so I can
  import a realistic Jira + MCP starter that matches how agents actually
  work with Jira, not only a minimal dozen-request demo.
- As an **end user**, I want a companion environment that stays aligned with
  the expanded collection (hosts, hidden credentials, MCP enablement) so I
  can fill placeholders once and run or adapt the full set safely.
- As a **contributor working with project agent skills**, I want the example
  collection to cover the Jira capabilities those skills use (issue CRUD and
  search, transitions, worklog, fields, comments, assign, epic link, boards,
  sprints, and related planning actions) so PyPost can demonstrate equivalent
  MCP-exposed tools without depending only on the external Atlassian MCP.
- As a **reader of examples docs**, I want clear import steps, secret-
  placeholder guidance, and a documented coverage map (what is included vs
  explicitly out of scope / gap-listed) so I know how complete the analog is.
- As an **operator / contributor**, I want fixture contract checks to stay
  green (and grow with the expanded surface) so the shipped examples remain
  importable and free of real credentials.
- As a **product steward**, I want this story to expand fixtures and docs
  only — not replace Cursor/agent Atlassian MCP config, not build a new
  in-process Atlassian MCP server, and not redesign collection/environment
  import formats.

## Definition of Done

- [x] The expanded (or clearly successor) jira-mcp example collection is
      tracked under `examples/` and importable via PyPost’s existing
      **Import Collection…** flow.
- [x] Companion environment remains aligned (placeholders only, credentials
      treated as hidden, MCP enablement appropriate for agent demos) and
      importable via existing **Manage Environments → Import…**.
- [x] MCP-exposed requests in the collection cover the **in-scope skill /
      workflow Jira capability set** (issue search/read/create/update,
      transitions, worklog, field discovery, comments, assign, epic link,
      boards, sprints and sprint membership, and other capabilities those
      workflows depend on), as a practical analog — not a full OpenAPI dump.
- [x] Coverage is documented: included capabilities vs explicit gaps /
      out-of-scope tools (Service Desk, ProForma, and other niche surfaces
      may remain gap-listed unless low-cost).
- [x] User-facing examples documentation (at least `examples/README.md`
      and any needed pointers) explains import order, placeholder filling,
      and secret safety for the expanded collection.
- [x] Fixtures contain **placeholder** hosts/credentials only — no real API
      tokens, passwords, or personal secrets.
- [x] Fixture contract tests pass; counts and checks are extended as needed
      for the expanded surface.
- [x] Existing import formats and product behavior are unchanged except for
      tiny fixture/docs/test fixes if unavoidable.
- [x] External Atlassian MCP remains in place; this story does not remove or
      replace it in agent config.

## Task Description

**Problem:** The PYPOST-1017 jira-mcp starter (about twelve MCP-exposed
requests) is too narrow for the Jira work project agents and skills already
perform via the external Atlassian MCP. Without a broader curated example,
PyPost cannot show a practical MCP tool analog for those workflows, and
readers lack an importable starting point that matches real usage.

**Goal:** Expand the curated jira-mcp example collection (and keep the
companion environment aligned) so MCP-exposed requests cover the mapped,
in-scope Atlassian MCP Jira capability set used by project skills —
documented, importable, secret-safe, and covered by contract tests.

**Scope (in):**

- Inventory of Atlassian MCP Jira capabilities used by project agent
  workflows/skills, expressed as a business capability map (what agents
  need to do in Jira).
- Expand the existing jira-mcp example collection (or replace/split into a
  clear jira-mcp collection) so MCP-exposed requests cover that in-scope
  map with sensible agent-facing descriptions and parameters.
- Keep the companion jira-cloud (or successor) environment aligned:
  placeholders only, hidden credentials, MCP enablement as appropriate.
- Update `examples/README.md` and related user-facing pointers for the
  expanded collection, including coverage vs gaps.
- Keep fixture contract tests green; extend them for the larger surface.
- Prefer parity with skill/workflow needs (create/search/update issues,
  transitions, worklog, sprints, boards, fields, comments, assign, epic
  link, sprint create/update/membership, and similar) over niche Service
  Desk / ProForma capabilities unless inclusion is low-cost.

**Scope (out):**

- Replacing or removing the external Atlassian MCP from Cursor/agent
  config.
- Implementing a new in-process Atlassian MCP server in application code.
- A full dump of every Jira Cloud endpoint or OpenAPI surface.
- Live CI calls against a real Jira instance.
- Application feature work beyond tiny fixture/docs/test fixes.
- Redesigning native collection/environment import formats.
- Completing unrelated User Guide or metrics work.

**Constraints and assumptions:**

- Baseline is the PYPOST-1017 starter pair
  (`examples/collections/jira_mcp.json`,
  `examples/environments/jira_cloud.json`); expand rather than greenfield
  redesign.
- Auth remains the established example pattern: site base URL plus basic
  credentials placeholders (no real secrets in git).
- “Practical analog” means skill/workflow parity for in-scope capabilities;
  an explicit gap list is acceptable for tools deliberately left out.
- Project skills under `.claude/skills/` (jira create/audit/sprint
  planning, sprint runner, tech-debt sync, top-down workflow, shared
  worklog helpers) define the priority capability set.
- Contract tests under `tests/` (for example
  `tests/test_example_fixtures.py`) remain the safety net for importability
  and placeholder/secret hygiene.
- No live Jira is required for Done; offline fixture and contract checks
  are sufficient.

## Main Entities and Interactions

- **jira-mcp example collection** — curated, importable set of named
  requests exposed as MCP tools that together form a practical analog of
  the Atlassian MCP Jira surface used by project workflows.
- **Companion environment** — variables and hidden credentials the
  collection expects (site URL, credentials placeholders, MCP enablement).
- **Capability map** — business list of Jira actions agents need (search,
  create, transition, sprint planning, etc.), derived from skill/workflow
  usage of the external Atlassian MCP.
- **Coverage documentation** — reader-facing note of what the collection
  covers and what remains explicitly out of scope or gap-listed.
- **Placeholder secret** — non-real credential value replaced locally after
  import; never a production token in git.
- **Fixture contract checks** — automated verification that examples remain
  importable, MCP-exposed as intended, and free of real secrets.
- **External Atlassian MCP** — the existing agent-side Jira tool server this
  story **analogs** in PyPost examples but does **not** replace.

Interaction flow: contributor inventories skill/workflow Jira needs →
expands the curated collection and aligns the environment → documents
coverage and gaps → reader imports environment, fills placeholders,
imports collection, and uses requests or MCP-exposed tools. Agents may use
PyPost MCP tools from the collection as a practical substitute surface for
the same in-scope actions; the external Atlassian MCP may still remain
configured elsewhere.

## Non-Functional Requirements

- **Secret safety:** committed fixtures contain only obvious placeholders;
  no real API tokens, passwords, or personal secrets.
- **Importability:** expanded fixtures import through existing UI flows
  without manual format conversion.
- **Discoverability:** readers can find import steps, placeholders, and
  coverage/gap notes from examples documentation without hunting the tree.
- **Coverage clarity:** docs state what is included vs explicitly
  out-of-scope or gap-listed so “analog” is not mistaken for full parity
  with every Atlassian MCP tool.
- **Skill-first prioritization:** in-scope skill/workflow capabilities take
  precedence over niche Service Desk / ProForma surfaces.
- **Baseline fidelity:** expand the PYPOST-1017 starter rather than redesign
  product import formats or invent a new examples layout without cause.
- **Test hygiene:** fixture contract tests remain green and reflect the
  expanded surface.
- **Scope discipline:** no new product features; no live Jira in CI; no
  replacement of external Atlassian MCP config.
- **Documentation language:** English Markdown; fixture and doc changes
  stay readable and consistent with existing examples guidance.

## Q&A

**Q:** Why expand the starter instead of leaving PYPOST-1017 as-is?

**A:** The starter proves the import + MCP + environment story. Project
agents already depend on a much larger Jira capability set via Atlassian
MCP. Without expansion, PyPost examples cannot demonstrate a practical
analog of that surface.

**Q:** What does “practical analog” mean?

**A:** Cover the Jira capabilities that in-repo skills and workflows
actually use (issue lifecycle, fields, comments, assign, epic link, boards,
sprints, worklog, and similar), with agent-facing tool descriptions. It does
not mean cloning every Atlassian MCP tool or every Jira Cloud endpoint.
Explicit gaps are OK.

**Q:** Why prefer skill/workflow tools over Service Desk / ProForma?

**A:** Current agent workflows in this repo center on software project issue
and sprint work. Niche Service Desk and ProForma tools add little value for
those flows unless they are trivial to include; they may remain on the gap
list.

**Q:** Does this replace the external Atlassian MCP in Cursor/agent config?

**A:** No. That remains out of scope. This story ships PyPost example
fixtures so equivalent tools *can* be exposed from collections; it does not
remove or reconfigure the external server.

**Q:** How does this relate to PYPOST-1017?

**A:** PYPOST-1017 shipped the starter collection, companion environment,
examples README, and contract tests. PYPOST-1026 expands that curated
jira-mcp surface toward skill/workflow parity and updates docs/tests
accordingly.

**Q:** How are secrets handled?

**A:** Same rule as PYPOST-1017: placeholders only in git; credential keys
hidden in the example environment; docs tell readers to substitute locally
and never commit real tokens.

**Q:** Must every Atlassian MCP `jira_*` tool have a one-to-one example
request?

**A:** No. Done requires coverage of the **in-scope skill/workflow
capability set**, documented as an analog, with an explicit gap list for
deliberately omitted tools. One request may serve a capability that several
thin MCP wrappers expose; the business need is capability parity for those
workflows, not a tool-count match.

**Q:** Is live Jira required for Done?

**A:** No. Offline importability, placeholder/secret hygiene, documentation,
and contract tests are sufficient. Live CI against a real Jira instance is
out of scope.

**Q:** What programming language is used for implementation?

**A:** JSON for fixtures, English Markdown for docs, and Python only for
existing fixture contract tests or tiny unavoidable fixture/docs/test
fixes. No new application feature work.

**Q:** May the collection be split or renamed?

**A:** Yes at delivery time if that keeps the jira-mcp story clearer, as
long as the result remains a tracked, importable curated example with an
aligned companion environment and updated docs. Prefer expanding the
existing pair when that stays clear.
