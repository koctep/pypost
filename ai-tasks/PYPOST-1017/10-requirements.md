# PYPOST-1017: Importable example collections and environments

## Programming language

JSON for importable example fixtures under `examples/`, plus English Markdown
for import/use documentation (`.cursor/lsr/do-markdown.md`). No application
Python work unless a tiny fixture/docs-only fix is unavoidable.

## Goals

Readers of the User Guide and new PyPost users need **concrete, importable
examples** that show how real workflows look in the product — especially
requests exposed as MCP tools for local AI agents, paired with environments
that hold hosts and secrets. Today that gap is only partly filled:

- [PYPOST-1015](https://pypost.atlassian.net/browse/PYPOST-1015) (User Guide)
  documents concepts and import UI steps, but **explicitly left example
  fixtures under `examples/` out of scope**.
- The repo already tracks a small MCP probe collection
  (`examples/collections/mcp.json`) aimed at local/dev probing, not a
  full end-user “import and adapt” story.
- Working-tree drafts for a Jira Cloud MCP collection and companion
  environment exist but are not yet shipped as curated, documented fixtures.

**Business goal:** Ship curated example collection(s) and environment(s)
under `examples/` that a reader can import into PyPost, fill in placeholder
secrets safely, and run or adapt — demonstrating MCP-exposed requests and
environment variables without committing real credentials. Application
feature behavior stays unchanged unless a tiny fixture/docs-only fix is
unavoidable.

## User Stories

- As an **end user**, I want importable example collections under
  `examples/collections/` so I can learn PyPost by adapting real request
  sets instead of building everything from scratch.
- As an **end user**, I want importable example environments under
  `examples/environments/` so I know which variables and hidden secrets a
  companion collection expects.
- As an **end user**, I want at least one curated **Jira Cloud + MCP**
  example (collection + environment) so I can see how MCP-exposed REST
  tools, templating, and credentials work together.
- As an **end user**, I want documentation that explains **where the
  examples live**, **how to import them**, and **how to replace
  placeholders with my own values** without putting real tokens into git.
- As an **operator / contributor**, I want `.gitignore` to keep allowing
  tracked fixtures under `examples/{collections,environments}/` while still
  ignoring local runtime collection and environment data elsewhere.
- As a **User Guide reader**, I want a clear pointer from user-facing docs
  (and/or README / examples README) to these fixtures so the guide and the
  examples reinforce each other without reopening the full PYPOST-1015
  scope.

## Definition of Done

- [ ] One or more example collections are tracked in git under
      `examples/collections/` and importable via PyPost’s existing
      **Import Collection…** flow.
- [ ] One or more example environments are tracked in git under
      `examples/environments/` and importable via the existing
      **Manage Environments → Import…** flow.
- [ ] The Jira Cloud MCP draft collection and companion environment are
      finished or reviewed as the primary curated pair (or replaced only if
      they cannot be made safe/usable as examples).
- [ ] Existing tracked example material (at minimum
      `examples/collections/mcp.json`) remains discoverable; docs clarify
      its role relative to the curated Jira Cloud pair if both ship.
- [ ] `.gitignore` continues to allow tracking
      `examples/collections/*.json` and `examples/environments/*.json`
      without exposing or tracking local user data directories.
- [ ] Documentation (User Guide topic link and/or README / examples README)
      explains import steps, placeholder filling, and secret handling.
- [ ] Fixtures contain **placeholder** hosts/credentials only — no real API
      tokens, passwords, or personal secrets.
- [ ] A reader can import the examples, substitute their own values for
      placeholders, and run or adapt the workflow (including MCP exposure
      where the example demonstrates it).
- [ ] Example files import successfully through the existing UI flows without
      requiring the reader to convert formats by hand.
- [ ] Application feature code is unchanged unless a tiny fixture/docs-only
      fix is required; no new product features.

## Task Description

**Problem:** Conceptual User Guide pages alone do not give newcomers a
ready-to-import starting point. Without curated fixtures, demonstrating
MCP tools + environments/secrets requires inventing requests by hand or
relying on incomplete local drafts.

**Goal:** Deliver importable example fixtures under `examples/` plus enough
docs for safe import and secret handling, using existing drafts as the
baseline.

**Scope (in):**

- Curated example collection JSON file(s) under `examples/collections/`.
- Curated example environment JSON file(s) under `examples/environments/`.
- Finish/review the existing Jira Cloud MCP collection draft
  (`examples/collections/jira_mcp.json`, ~12 MCP-exposed Jira REST tools)
  and companion environment (`examples/environments/jira_cloud.json`).
- Keep or clarify the already-tracked `examples/collections/mcp.json`
  local MCP probe example as part of the examples story.
- Ensure `.gitignore` exceptions for these fixture paths remain correct
  (`!examples/collections/`, `!examples/collections/*.json`,
  `!examples/environments/`, `!examples/environments/*.json`).
- Document import/use and secret/placeholder handling in user-facing docs
  (User Guide and/or root README / examples README) without completing the
  full User Guide story.
- Keep examples importable with PyPost’s current collection and environment
  import behavior (no format redesign).

**Scope (out):**

- Completing the full User Guide ([PYPOST-1015](https://pypost.atlassian.net/browse/PYPOST-1015)).
- Tech-debt Jira sync or baseline metrics updates.
- Local agent tooling config (for example `.codex`, `.claude`, `.mcp.json`).
- New product features, UI changes, or import/export format redesigns.
- Replacing or absorbing the full MCP Integration reference; examples may
  point readers to existing MCP / User Guide pages.

**Constraints and assumptions:**

- Working-tree drafts
  (`examples/collections/jira_mcp.json`,
  `examples/environments/jira_cloud.json`) and the tracked
  `examples/collections/mcp.json` are the **baseline**, not a greenfield
  redesign.
- Existing `.gitignore` exceptions already allow tracking those fixture
  paths; this story must keep that allowance correct rather than inventing
  a new ignore model.
- Root README does not currently mention `examples/`; discoverability may
  need a short pointer as part of docs for this story.
- User Guide pages already explain generic collection/environment import
  and MCP enablement; this story adds **fixture-specific** guidance (paths,
  what to fill in, secret safety), not a second full import tutorial.
- Example environments use obvious placeholders (for example a sample
  Atlassian site URL and `you@example.com:your-api-token`-style values)
  and mark credential keys as hidden where appropriate.

## Main Entities and Interactions

- **Example collection** — a shareable set of named requests (methods, URLs
  with placeholders, optional MCP tool exposure and descriptions) that
  demonstrates a real workflow.
- **Example environment** — a named set of variables (hosts, credentials)
  expected by a companion collection, with clear placeholders and hidden
  secret keys; may indicate MCP server enablement for agent demos.
- **Placeholder secret** — a non-real credential value that the reader
  replaces locally after import; never a production token in git.
- **Import path** — the user’s action of bringing example JSON into PyPost
  via existing collection and environment import UI.
- **User-facing example docs** — short guidance that points to fixture
  locations, import steps, and safe secret handling.
- **Existing drafts / tracked examples** — working-tree
  `jira_mcp.json` + `jira_cloud.json`, tracked `mcp.json`, and the
  `.gitignore` exceptions that keep those paths trackable.

Interaction flow: reader finds fixtures via docs/README → imports the
example environment and replaces placeholders → imports the companion
collection → selects the environment → sends a request or enables MCP for
agent use. Contributors clone the repo and see fixtures tracked while local
runtime data remains ignored.

## Non-Functional Requirements

- **Secret safety:** committed fixtures contain only obvious placeholders;
  no real API tokens, passwords, or personal secrets.
- **Importability:** a reader can import the shipped examples through the
  existing UI flows without manual format conversion.
- **Discoverability:** a reader can find fixture paths and import/secret
  guidance from user-facing docs and/or README without hunting the tree.
- **Clarity of roles:** if both the Jira Cloud pair and `mcp.json` ship,
  docs distinguish curated end-user example vs local MCP probe material.
- **Ignore hygiene:** `.gitignore` keeps allowing tracked
  `examples/{collections,environments}/*.json` while still ignoring local
  runtime collection/environment data elsewhere.
- **Scope discipline:** no new product features; application code unchanged
  unless a tiny fixture/docs-only fix is unavoidable.
- **Baseline fidelity:** finish/review existing drafts rather than a
  greenfield redesign, unless a draft cannot be made safe or usable.

## Q&A

**Q:** Why do example fixtures matter if the User Guide already explains
import and MCP?

**A:** The guide teaches *how* features work. Examples let a reader *start
from a working shape* — especially MCP-exposed requests plus environment
variables/secrets — without inventing a dozen requests. That shortens time
to a successful first real workflow.

**Q:** How does this relate to PYPOST-1015?

**A:** PYPOST-1015 ships the structured User Guide and explicitly lists
example fixtures under `examples/` as out of scope. PYPOST-1017 closes that
gap with fixtures and fixture-specific docs; it does not reopen completing
the full User Guide.

**Q:** Why start from the existing Jira Cloud drafts instead of designing
new examples from scratch?

**A:** The drafts already model the intended story (MCP-exposed Jira REST
tools + companion environment with placeholders and a hidden credentials
key). Finishing and documenting them is lower risk and matches the Jira
task notes: use partial working-tree drafts as the baseline.

**Q:** How are secrets handled?

**A:** Committed fixtures may only contain obvious placeholders (fake site
URL, example email + `your-api-token` style values). Credential-like keys
should be marked hidden in the example environment. Docs must tell readers
to substitute their own secrets locally after import and never commit real
tokens. No real API tokens or credentials may be committed.

**Q:** Is `examples/collections/mcp.json` in or out?

**A:** In as existing tracked example material. Docs should make its role
clear (local MCP/SSE probe style) relative to the curated Jira Cloud pair
so readers are not confused about which file to import for which goal.

**Q:** Does this story change application import/export behavior?

**A:** No. Examples must remain importable with current product behavior.
Application code stays unchanged unless a tiny fixture/docs-only fix is
required.

**Q:** Where should import/use docs live?

**A:** Wherever best serves discoverability without expanding PYPOST-1015:
a short User Guide pointer and/or root README / examples README. Exact
placement is a delivery choice as long as a reader can find import steps
and secret-handling guidance.

**Q:** What programming language is used for implementation?

**A:** JSON for the example fixtures and English Markdown for
documentation. Application Python is out of scope unless a tiny
fixture/docs-only fix is unavoidable.

**Q:** Are local agent configs (`.codex`, `.claude`, `.mcp.json`) part of
Done?

**A:** No. Those remain out of scope, consistent with PYPOST-1015 and the
Jira description.

**Q:** Are the working-tree drafts and `.gitignore` exceptions in scope?

**A:** Yes as baseline. Requirements acknowledge
`examples/collections/jira_mcp.json`,
`examples/environments/jira_cloud.json`,
`examples/collections/mcp.json`, and the existing `.gitignore` exceptions
that keep those fixture paths trackable.
