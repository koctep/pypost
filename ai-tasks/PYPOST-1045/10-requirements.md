# PYPOST-1045: Reliable e2e confidence for MCP-exposed collections

## Programming Language

Python for analysis artifacts and any later harness, documentation, or
follow-up work this analysis may recommend. No product feature code is
required in this task. Follow `.cursor/lsr/do-python.md` and
`.cursor/lsr/do-markdown.md` for any Python or Markdown deliverables.

## Goals

PyPost ships curated collections that expose many agent-facing tools against
real external HTTP APIs (notably the Jira Cloud example). Contributors and
maintainers need confidence that those MCP-exposed tools behave correctly
end-to-end — from tool invocation through request execution to a usable
response — without depending on live third-party services in routine CI.

Today, coverage is strong for offline fixture contracts, MCP protocol and
server plumbing, agent UI flows with deterministic Send stubs, and a narrow
maintainer-only live Jira smoke. What is missing is a dependable, CI-safe
way to prove the full collection-MCP path against a **controlled stand-in
for the external HTTP backend**.

**Business goal:** decide, with documented inventory and rationale, whether
the product needs such a controlled backend for MCP collection e2e, so the
team can either invest in that capability (via a follow-up) or explicitly
rely on existing harnesses and live/manual validation — without leaving the
gap as tribal knowledge.

## User Stories

- As a **contributor**, I want a clear map of what MCP/collection e2e
  already proves and what it does not, so I know which regressions CI will
  catch before merge.
- As a **maintainer**, I want a yes/no decision on whether a controlled
  backend is required for collection MCP e2e, with rationale grounded in
  current coverage and CI constraints, so follow-up work is intentional.
- As an **AI agent or developer using curated MCP collections**, I want this
  analysis to state whether automated, secret-free confidence for exposed
  tools is needed and to sketch the follow-up that would deliver it, so the
  gap is planned rather than left as tribal knowledge. (Harness delivery is
  **not** this ticket — see Out of Scope and follow-up handoff.)
- As a **CI / release steward**, I want the analysis to confirm that routine
  validation can stay secret-free and deterministic, and that protected live
  checks remain optional complements — not the only planned proof of
  collection MCP behavior.
- As a **product steward**, I want this task limited to analysis and a
  requirements-level recommendation, so full controlled-backend
  implementation is deferred to an explicit follow-up ticket.

## Definition of Done

- [x] Inventory of current MCP/collection-related automated and opt-in
      coverage is documented (what each harness proves, and its limits).
- [x] Gaps are explicit for MCP tools backed by collections that call real
      external APIs (especially curated Jira MCP examples).
- [x] Inventory (or the must-cover section) enumerates the **concrete tool
      ids** that constitute the minimum representative slice for a future
      CI-safe collection MCP e2e path (see Outcomes below for required
      behavior categories).
- [x] A clear recommendation is recorded at requirements level: **whether a
      controlled stand-in for the external HTTP backend is needed** for
      reliable collection MCP e2e, with business rationale.
- [x] If **yes**: architecture (Step 2) must propose the concrete form,
      operator interface, packaging/docs expectations, and a follow-up ticket
      sketch; this Step 1 artifact states only the business need and must-cover
      outcomes. This ticket’s DoD does **not** include implementing the
      harness.
- [x] If **no**: architecture must document how existing harnesses and
      live/manual paths together satisfy collection MCP confidence.
      (N/A — recommendation is yes; path covered by yes branch above.)
- [x] Full controlled-backend / mock-server implementation is **out of
      scope** for this task; any build work belongs in a follow-up ticket
      sketched in Step 2.
- [x] Roadmap and requirements artifacts exist under
      `ai-tasks/PYPOST-1045/`; no product feature code is required here.

## Task Description

**Problem:** Example collections such as the curated Jira MCP set expose many
tools via MCP against live REST surfaces. Without a controlled backend,
automated end-to-end proof of those tools is fragile or impossible in
default CI (credentials, network, tenant state, flakiness, secrecy).

**What exists today (inventory):**

| Area | What it proves | Limit for collection MCP e2e |
| ---- | -------------- | ---------------------------- |
| Agent UI e2e pack (`make test-agent-e2e`, agent e2e docs) | Offscreen UI flows; Send path with deterministic HTTP stubs and seed workspace | Does not exercise MCP tool calls against curated example collections or a live MCP client |
| Agent e2e HTTP stubs / seed fixtures | Deterministic responses at the UI Send boundary | Scoped to agent UI scenarios; not a shared stand-in for collection-backed MCP tool backends |
| MCP client/server unit and integration tests | Protocol, tool listing/calling, manager lifecycle; some tools hit ad-hoc local HTTP or mocked execution | Not a full curated-collection surface; stubs are scenario-local, not a reusable collection-e2e backend |
| MCP fixture generators (`make generate-mcp-fixtures` / `check-mcp-fixtures`) | Committed MCP test collection/env JSON stays in sync with builders | Offline artifact integrity only; no runtime tool→HTTP path |
| Example / Jira MCP fixture contracts (`tests/test_example_fixtures.py` and related docs) | Import, MCP exposure, skill coverage, placeholders, env/auth/MCP-input agreements | Static agreements only; no tool invocation or outbound HTTP |
| MCP test collection integration | Live loopback MCP against the probe test collection with mocked or local stub HTTP | Probe collection, not the curated Jira example surface |
| Optional live Jira MCP smoke (`make test-jira-mcp-live`) | Four read-only tools against a real authorized Jira site (maintainer opt-in) | Not default CI; needs secrets; narrow read-only slice; unsuitable as the only confidence path |

**Gap:** There is no default-CI, secret-free path that proves: MCP client
invokes a curated collection tool → PyPost executes the request → response
comes from a **controlled** external-HTTP stand-in that is stable enough for
repeatable e2e of collection-backed tools.

### Recommendation (requirements level)

**Yes — a controlled stand-in for the external HTTP backend is needed** for
reliable MCP collection e2e in routine automation.

Rationale:

1. Offline contracts and protocol tests do not prove the executed request
   path against collection URLs and response shapes agents rely on.
2. Agent UI HTTP stubs solve a different path (UI Send), not collection MCP
   tool execution.
3. Live tenant smoke is valuable but intentionally narrow, secret-bearing,
   and opt-in — it cannot be the primary CI confidence for the curated
   surface.
4. Ad-hoc per-test local stubs in integration suites show the pattern works,
   but do not yet give contributors a shared, documented, collection-oriented
   e2e capability.

Step 2 (architecture) must choose *how* to provide that controlled backend
(reuse, new packaging, or hybrid) and define operator-facing interface and
follow-up scope. Step 1 only establishes the business need. Delivering the
harness is a **follow-up** after this analysis ticket.

### Outcomes a controlled backend must cover (business)

Minimum representative slice for the curated **Jira MCP example** (aligned
with the existing maintainer live-smoke critical paths):

- At least one **list/search** style tool path (e.g. `jira_search_issues_jql`
  and/or `jira_list_boards`).
- At least one **get-by-id** style tool path (e.g. `jira_get_issue`).
- Optionally the same read-oriented companion already treated as
  smoke-critical (`jira_get_current_user`), if inventory confirms it remains
  part of the minimum slice.

The inventory / Step 2 follow-up sketch must list the **exact tool ids** that
form this minimum slice (not “representative” in the abstract). Broader
curated surface coverage may be recommended later; it is not required for
this analysis ticket’s DoD.

Cross-cutting must-cover outcomes:

- Deterministic, secret-free responses for that minimum tool-id slice.
- Usable from automated tests without live third-party credentials or
  network to external SaaS.
- Clear documentation of what is covered vs what remains live/manual-only.
- Packaging discoverable via the project's standard developer workflows
  (exact targets deferred to architecture).

### In Scope

- Inventory of existing MCP/collection e2e and related harnesses.
- Gap analysis for collections that call real external APIs.
- Enumeration of concrete tool ids for the minimum representative
  must-cover slice (Jira MCP example as the primary case).
- Requirements-level recommendation (controlled backend yes/no + rationale).
- Architecture handoff: must-cover outcomes; follow-up ticket sketch belongs
  in Step 2 if recommendation is yes.
- Workflow artifacts for this analysis task.

### Out of Scope

- Implementing a full controlled backend or mock server (no exception for
  “trivially small” builds in this ticket).
- Expanding curated Jira capability set or changing product MCP runtime
  behavior.
- Replacing the optional live Jira smoke or weakening its secrecy rules.
- Redesigning agent UI e2e or converting it into an MCP collection suite.
- Committing real credentials, tenant data, or live URLs into the repo.
- Delivering automated e2e confidence itself — that is follow-up work after
  this analysis recommends and scopes it.

### Constraints and Assumptions

- Default CI must remain free of live SaaS credentials and non-deterministic
  tenant state.
- Curated example collections are skill-oriented starters, not full API
  parity promises.
- Protected live smoke remains a complementary maintainer check, not a
  substitute for CI-safe e2e of the collection MCP path.
- Estimate: 3 story points (analysis + recommendation; implementation is
  follow-up).
- Programming language for any later harness work: Python.

## Main Entities and Interactions

- **Curated MCP collection** — shipped set of requests exposed as agent
  tools (e.g. Jira example, local MCP probe).
- **Companion environment** — configuration/placeholders that make the
  collection runnable without embedding secrets in the collection file.
- **MCP exposure path** — agent invokes a tool; PyPost runs the matching
  request and returns a tool result.
- **External HTTP dependency** — the real service the collection would call
  in production use (e.g. Jira Cloud REST).
- **Controlled backend stand-in** — a deterministic substitute for that
  external dependency used only for automated confidence (form TBD in
  architecture).
- **Existing automated harnesses** — agent UI e2e, MCP unit/integration,
  fixture contracts, fixture generators, optional live smoke — each covering
  a distinct slice of the problem.
- **Contributor / CI consumer** — needs a clear, secret-free signal that
  collection MCP e2e either is covered or is explicitly out of default CI
  with an approved alternative.

```text
Agent / test client
    → MCP tool on curated collection
        → PyPost request execution
            → External HTTP dependency
                 OR controlled backend stand-in (recommended need)
```

## Q&A

**Q: Why not treat offline fixture contracts as enough e2e?**
**A:** They prove importability and agreements (exposure, env, auth, inputs),
not that invoking a tool yields a successful, realistic HTTP-backed result.

**Q: Why not rely only on the live Jira smoke?**
**A:** It is opt-in, secret-bearing, read-only, and outside default PR CI. It
complements confidence; it cannot be the sole proof for contributors.

**Q: Why not say agent e2e HTTP stubs already solve this?**
**A:** Those stubs serve the offscreen UI Send path. They do not provide a
shared, collection-oriented stand-in for MCP tool → outbound HTTP e2e.

**Q: Is “mock server” mandated as a specific technology?**
**A:** No at requirements level. The business need is a **controlled
stand-in for the external HTTP backend**. Architecture decides whether that
is a reused stub layer, a standalone process, fixtures only, or another
form.

**Q: Is full implementation in this ticket?**
**A:** No. Deliverable is inventory, gap analysis, recommendation, and
must-cover tool-id slice. Controlled-backend / mock-server implementation is
always a follow-up; there is no “trivially small” exception in this ticket.

**Q: What must the minimum must-cover slice include?**
**A:** For the Jira MCP example: at least one list/search path
(`jira_search_issues_jql` and/or `jira_list_boards`) and one get-by-id path
(`jira_get_issue`), with concrete tool ids enumerated in inventory / Step 2
follow-up sketch. Optionally `jira_get_current_user` if it remains
smoke-critical.

**Q: What must Step 2 produce if the recommendation stays yes?**
**A:** Concrete form, interface (how tests/operators start and point
collections at the stand-in), coverage boundaries (including the enumerated
tool-id minimum slice), Makefile/docs expectations, and a follow-up ticket
sketch — without expanding this task into a harness build.
