# PYPOST-922: Broader agent-e2e packaging make entry

## Goals

The golden Send → response flow
([PYPOST-838](https://pypost.atlassian.net/browse/PYPOST-838)) is one product
proof. The agent UI e2e surface has since grown into an **environment pack**
and related harness scenarios (seed, HTTP stubs, presentation matrix, dialog
settle, failure artifacts, and more) that run under the shared `agent_e2e`
contract.

When the golden shipped, broader packaging was deferred to an epic packaging
story. Maintainers and agents still need a **clear, documented make packaging
path** whose primary meaning is the **broader** agent e2e pack — not “run the
golden file only.” Without that, people invent ad-hoc pytest one-liners, or
assume golden-only is the full packaging story.

Business value: one discoverable project-standard entry to run and extend the
broader agent e2e pack beyond the golden scenario, aligned with Makefile-first
workflows.

Source: [PYPOST-853](https://pypost.atlassian.net/browse/PYPOST-853) TD-5
(originally [PYPOST-838](https://pypost.atlassian.net/browse/PYPOST-838) TD-5;
epic packaging context [PYPOST-839](https://pypost.atlassian.net/browse/PYPOST-839)).

## Programming Language

Python (`.cursor/lsr/do-python.md`) for any harness/test wiring that locks the
packaging contract. Makefile for the run entry (workspace makefile rules).
Developer docs in English Markdown (`.cursor/lsr/do-markdown.md`).

## User Stories

- As a **maintainer**, I want a documented make packaging path that runs the
  **broader** agent e2e surface (pack / harness beyond the single golden), so
  I do not treat golden-only as the full entry.
- As an **AI agent / contributor**, I want that path listed in `make help` and
  pointed from agent e2e / testing docs, so I prefer the project-standard
  command over ad-hoc shell pytest.
- As a **CI / local runner**, I want the documented default pack selection to
  be the broader agent e2e set (not golden-only), with a clear way to narrow
  to the golden file when needed.
- As a **sibling story owner** (golden, env pack, dialog settle), I want this
  story to package and document the existing broader surface rather than add
  new product scenarios.
- As a **reader of golden docs**, I want the golden guide to point at the
  broader packaging path so golden remains one scenario inside the pack, not
  the only documented run entry.

## Definition of Done

- A **documented make target / packaging path** exists for **broader agent
  e2e beyond the current golden** (Jira acceptance).
- The primary documented run entry selects the broader agent e2e pack (shared
  marker / pack contract), not only `tests/test_agent_golden_e2e.py`.
- `make help` (or equivalent project help) surfaces that entry with a `##`
  description so it is discoverable without reading Makefile source.
- Developer docs distinguish:
  - broader pack entry (default packaging path), and
  - optional narrow-to-golden (or other single-module) override.
- Golden and umbrella / testing docs cross-link so maintainers find the
  broader path from the golden story and from general testing guidance.
- No new product golden scenarios are required for this debt; packaging and
  documentation (plus minimal contract locks if needed) are sufficient.
- Unticketed follow-ups (if any) are recorded only in this task’s
  `60-tech-debt.md` (no Jira ticket creation in this run).

Acceptance (from Jira): **Documented make target / packaging path for broader
agent e2e beyond current golden.**

## Task Description

**Problem:** PYPOST-838 delivered one golden product proof and deferred
“broader agent-e2e packaging / make entry” to epic packaging. The pack has
grown (env pack, seed, HTTP, matrix, dialog settle, failure artifacts, etc.).
Debt PYPOST-853 TD-5 / this ticket still asks for an explicit, documented
make packaging path whose scope is that **broader** surface — so golden is
not mistaken for the full packaging story.

**Business need:** First-class, Makefile-preferred packaging documentation
(and any missing packaging clarity) so maintainers and agents can run the
broader agent e2e pack confidently.

### In Scope

- Documented make packaging path for the broader agent e2e pack beyond golden.
- Discoverability via `make help` and agent e2e / testing / golden docs.
- Clear distinction between default broader pack run and optional golden-only
  (or single-module) narrowing.
- Light updates to sibling docs that still imply packaging is “golden only”
  or leave “broader packaging” as an open epic deferral without a closed
  path for this debt.
- Minimal automated contract checks if needed to keep the documented packaging
  path from drifting (help listing, default selection meaning broader than
  golden).

### Out of Scope

- New product UI scenarios or expanding the Send → response golden itself.
- Redesigning lifecycle / identity / actions / snapshot / wait APIs.
- Full CI matrix redesign (dedicated job policy already exists elsewhere;
  this story owns packaging path clarity, not CI topology overhaul).
- Live MCP verification against a running app (distinct from in-process
  agent e2e).
- User-facing product documentation (`doc/user/`).
- Creating Jira Debt tickets (unticketed items only in `60-tech-debt.md`).
- Commit or Jira status transitions / worklog MCP writes (orchestrator).

## Functional Requirements

- FR1: A project-standard make packaging path is documented as the way to run
  **broader** agent e2e (pack / harness beyond the golden module alone).
- FR2: The default behavior of that path selects the broader agent e2e set,
  not solely the golden file.
- FR3: Maintainers can discover the path via `make help` (description present).
- FR4: Docs show how to narrow to the golden scenario (or a single module)
  without replacing the broader path as the primary packaging entry.
- FR5: Golden docs and the agent e2e umbrella / testing docs present the
  broader packaging path as the preferred entry for the pack.
- FR6: Packaging remains Makefile-first; undocumented bare pytest is not the
  primary documented workflow.
- FR7: Existing broader pack scenarios remain runnable through that path;
  this story does not remove coverage.

## Non-Functional Requirements

- **Discoverability:** A new maintainer can find “how do I run broader agent
  e2e?” from help and docs without reverse-engineering the Makefile.
- **Clarity:** Golden vs broader pack is explicit in wording (beyond current
  golden).
- **CI suitability:** Documented path uses the project’s standard offscreen /
  test environment expectations.
- **Minimalism:** Prefer documenting and aligning existing packaging over
  inventing parallel entry points unless a gap remains.
- **Stability:** If contract locks are added, they stay fast and do not
  require a live GUI session beyond what packaging smoke already needs.
- **No production → tests imports:** Production agent code must not import
  from `tests/`.

## Constraints and Assumptions

- Programming language: Python for any test locks; Makefile for the entry;
  Markdown for docs.
- Parent / source debt: PYPOST-853 TD-5 ← PYPOST-838 TD-5; epic packaging
  context PYPOST-839 (may already have delivered parts of the make entry —
  this story closes the **documented broader-than-golden** acceptance bar).
- Shared `agent_e2e` marker / env-pack model is the business notion of
  “broader agent e2e”; golden is one module inside that surface.
- Workspace rule: prefer Makefile targets over ad-hoc toolchain commands.
- Offscreen Qt / project-equivalent headless GUI remains the supported
  automation environment for agent e2e.
- Step 1 review is treated as pre-approved under sprint-task-runner autonomy
  (no approval gate / no Jira updates in this step).

## Main Entities and Interactions

| Entity | Role |
| --- | --- |
| Broader agent e2e pack | Shared pack / harness scenarios beyond the golden alone |
| Golden scenario | Single Send → response product proof inside the pack |
| Make packaging path | Project-standard documented command to run the pack |
| Help listing | Discoverability surface for the packaging path |
| Umbrella / testing docs | Onboarding map from pack concepts to the run entry |
| Golden docs | Point readers at broader packaging, not only golden-only run |
| Narrow override | Optional run of golden or one module without replacing pack entry |

Interaction overview:

1. Maintainer (or agent) looks up how to run agent e2e beyond golden.
2. Docs / `make help` point to the packaging path for the broader pack.
3. Default run executes the broader pack selection.
4. Optional override narrows to golden (or one module) when needed.
5. Golden docs remain the scenario guide and defer pack packaging to the
   broader path.

## Q&A

- Q: Why is this still open if PYPOST-839 added `make test-agent-e2e`?
  A: 838/853 deferred **broader** packaging as debt; acceptance for this
  ticket is an explicit documented make/packaging path for the pack
  **beyond golden**. Closing 922 means that bar is met and attributable
  here — including doc clarity that the primary entry is the broader pack,
  not golden-only.

- Q: Must this story add new agent e2e product scenarios?
  A: No. Packaging and documentation (plus optional contract locks) are the
  acceptance surface.

- Q: Is golden-only an acceptable default packaging path?
  A: No. Acceptance requires the broader path beyond current golden. Golden
  narrowing may remain documented as an override.

- Q: Does this include live MCP e2e?
  A: No. In-process agent UI e2e / env pack only; MCP remains a separate
  workflow.

- Q: Does this redesign CI jobs?
  A: No. Packaging path clarity for maintainers/agents; CI topology changes
  are out of scope unless a minimal doc pointer is needed.

- Q: Why not only update consolidated debt notes?
  A: The business value is a usable, documented packaging path maintainers
  follow — not a debt-table footnote.
