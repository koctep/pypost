# PYPOST-1015: Create structured end-user guide under doc/user/

## Programming language

English Markdown for end-user documentation (`.cursor/lsr/do-markdown.md`).
No application code changes.

## Goals

PyPost's end-user help lived mainly as a single, hard-to-navigate docs landing
page. New and returning users need a clear, step-by-step **User Guide** that
explains what the product can do — sending requests, organizing collections,
switching environments, templating, post-response scripts, history and cURL,
MCP tools for local AI agents, settings, hotkeys, and common workflows — without
having to reverse-engineer the UI or dig through developer notes.

The business goal is discoverability and self-serve adoption: a reader who opens
the repository or the docs index can find a structured guide, follow it from
first install through everyday workflows, and reach deeper MCP or metrics
references when needed. Shipping this guide also keeps the product's
capabilities visible next to the root project README.

Partial draft work already exists in the working tree (user-guide index and
topic pages, docs index rewrite, root README Documentation section). Two topic
pages (collections and environments) were already delivered with related
import/export stories. This task completes and ships that structured guide;
it must not redefine a conflicting topic set or navigation model.

## User Stories

- As an **end user**, I want a single User Guide index that lists every major
  topic in a sensible order, so I can see what PyPost covers and jump to the
  page I need.
- As a **new user**, I want a getting-started path (install, run, first request),
  so I can send a successful call without guessing commands or UI steps.
- As an **end user**, I want an overview of the main window (menus, environment
  bar, sidebar, tabs, editor, settings entry), so I know where to look for each
  action.
- As an **end user**, I want guidance on creating, sending, inspecting, and
  saving HTTP requests (including body options and response search), so I can
  work productively in the editor.
- As an **end user**, I want documentation for collections (save, open, rename,
  delete, import/export as already shipped), so I can organize and share request
  sets.
- As an **end user**, I want documentation for environments (variables, hidden
  values, encryption awareness, import/export as already shipped, MCP enablement
  per environment), so I can switch hosts and secrets safely.
- As an **end user**, I want templating explained (`{{ variables }}` and
  allow-listed functions), so I can reuse values without hard-coding them.
- As an **end user**, I want post-request scripts explained with practical
  examples (for example saving a token), so I can automate follow-up steps.
- As an **end user**, I want history and copy-as-cURL explained, so I can
  reproduce or share a call outside the app carefully.
- As an **end user**, I want MCP tools explained at a user level (mark a request,
  enable the server, connect an agent, safety reminders), so I can expose tested
  requests to a local AI agent without writing a server.
- As an **end user**, I want settings topics covered (editor, timeouts, retries/
  alerts, MCP/metrics ports, encryption, logging), so I can tune the app safely.
- As an **end user**, I want a hotkeys summary with a pointer to the in-app list,
  so I can work faster from the keyboard.
- As an **end user**, I want common end-to-end workflows (ad-hoc call, env
  switching, auth token capture, expose to Cursor, debug agent usage, shell
  reuse), so I can follow recipes instead of assembling steps myself.
- As a **repository visitor**, I want the root README and the docs index to link
  clearly to the User Guide, so documentation is discoverable from the project
  entry points.
- As a **reader of integration docs**, I want the User Guide to point to existing
  MCP and metrics references (and developer docs) without replacing them, so
  deep technical detail stays in the right place.

## Definition of Done

- [ ] A User Guide index exists and lists all required topics: getting started,
      interface, requests, collections, environments, templating, scripts,
      history/cURL, MCP tools, settings, hotkeys, and common workflows.
- [ ] Each listed topic has a dedicated guide page with enough step-by-step
      content for an end user to perform the described capability using current
      product behavior.
- [ ] The docs landing page acts as a documentation index and points readers to
      the User Guide (not a monolithic substitute for the guide).
- [ ] The root project README links to the User Guide (and may also link the docs
      index and related integration docs).
- [ ] Collections and environments pages remain consistent with already-shipped
      import/export behavior; this story does not remove or contradict those
      pages.
- [ ] Content is accurate for current product behavior (no obsolete steps or
      invented features).
- [ ] No application code changes are introduced by this story.
- [ ] Developer documentation under `doc/dev/`, example fixture collections/
      environments, tech-debt Jira sync / baseline metrics updates, and local
      agent tooling config are untouched as out-of-scope items.

## Task Description

**Problem:** End-user documentation was concentrated in a single docs landing
page. Readers could not follow a progressive path through product capabilities,
and the root README did not clearly surface a dedicated User Guide.

**Goal:** Ship a complete structured User Guide under the end-user docs area,
with an index and topic pages covering the capabilities above, and wire
navigation from the docs index and the root README.

**Scope (in):**

- User Guide index plus topic pages for: getting started, interface, requests,
  collections, environments, templating, post-request scripts, history and
  cURL, MCP tools for AI agents, settings, hotkeys, and common workflows.
- Docs landing page as an index that points at the User Guide (and may still
  point at integration and developer docs).
- Root README Documentation section linking to the User Guide.
- Accuracy review and completion of the existing working-tree drafts so the
  shipped guide matches current product behavior.
- Docs-only deliverables.

**Scope (out):**

- Developer documentation under `doc/dev/`.
- Example collections/environments fixtures under `examples/`.
- Tech-debt Jira sync or baseline metrics updates.
- Local agent tooling config (for example `.codex`, `.claude`, `.mcp.json`).
- Application feature work, UI changes, or new product capabilities.
- Replacing the full MCP integration or Prometheus monitoring references; the
  User Guide may link to them, not absorb them.

**Constraints and assumptions:**

- Draft artifacts already present in the working tree are the baseline: user
  guide index, the topic pages listed in Goals, rewritten docs index, and root
  README Documentation links. Requirements must refine and complete that
  structure, not invent a conflicting table of contents.
- `collections` and `environments` topic pages already exist from related
  stories; this task keeps them as part of the guide and ensures the index and
  navigation treat them as first-class topics.
- Audience is end users and operators of the desktop app, not contributors
  extending the codebase.
- Language and tone: clear English, step-by-step where actions matter, with
  safety notes for secrets, MCP binding, and sharing cURL.
- Accuracy is judged against current product behavior, not aspirational
  features.

## Main Entities and Interactions

- **User Guide** — the structured set of end-user topics and its index; the
  primary self-serve help surface for product capabilities.
- **Topic page** — one guide chapter focused on a single capability area (for
  example requests or MCP tools).
- **Docs index** — the documentation landing page that routes readers to the
  User Guide, integration/ops docs, and developer docs.
- **Root README Documentation section** — the project entry-point links that
  make the User Guide discoverable from the repository front page.
- **Integration references** — existing MCP and metrics docs that remain the
  deep references; the User Guide links out rather than duplicating them.
- **End user** — person installing and using PyPost to call APIs and optionally
  expose tools to a local agent.
- **Existing draft guide** — working-tree (and already-committed collections/
  environments) pages that this story completes and ships.

Interaction flow: a reader arrives at the root README or docs index → follows
the User Guide link → lands on the guide index → chooses a topic (or follows
getting started → interface → requests → …) → completes a workflow → optionally
follows links to MCP/metrics references for deeper detail.

## Non-Functional Requirements

- **Discoverability**: a reader of the root README or docs index can reach the
  User Guide in one obvious click/link.
- **Completeness**: every capability listed in Goals has a dedicated topic
  reachable from the guide index.
- **Accuracy**: steps and capabilities match the current product; outdated or
  contradictory instructions are corrected before the story is done.
- **Clarity**: pages favor short, actionable steps and concrete examples over
  abstract description.
- **Separation of concerns**: end-user guidance stays in the User Guide;
  developer/contribution material stays out of this deliverable.
- **Consistency**: collections and environments guidance remains aligned with
  the import/export behavior already documented for those features.
- **Safety awareness**: secrets, hidden variables, MCP network exposure, and
  sharing cURL are called out where users could make a costly mistake.

## Q&A

**Q:** Why is this a documentation story rather than a product feature?

**A:** Users already have the capabilities in the app; the gap is finding and
learning them. Structured docs reduce onboarding time and support without
changing application behavior.

**Q:** Must this story rewrite the existing draft pages from scratch?

**A:** No. Existing working-tree drafts and the committed collections/
environments pages are the baseline. The story completes, corrects for
accuracy, and ships that structure — it must not invent a conflicting topic
set or navigation model.

**Q:** Are collections and environments pages in scope even though they were
committed earlier?

**A:** Yes as part of the guide index and navigation. Their content should stay
consistent with shipped import/export behavior; this story does not reopen
those features unless a doc accuracy fix is required.

**Q:** Does the User Guide replace the MCP Integration or Prometheus docs?

**A:** No. The guide covers user-level setup and workflows and links to those
references for transport details, envelopes, scrape setup, and similar depth.

**Q:** Is automated testing required for this story?

**A:** No behavioral application change is in scope. Step 3 is N/A unless a
later architecture decision introduces a lightweight docs-contract check; that
is not required by the business goals here.

**Q:** What counts as "accurate for current product behavior"?

**A:** A reader following the guide can perform the described action in the
current desktop app (or reach the stated settings/MCP outcomes) without
encountering missing UI, renamed actions, or undocumented prerequisites that
the page claims exist.

**Q:** Are example fixture files under `examples/` part of Done?

**A:** No. Explicitly out of scope for this ticket.
