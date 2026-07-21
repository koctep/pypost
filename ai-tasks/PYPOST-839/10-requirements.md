# PYPOST-839: Docs and Makefile target for agent e2e

## Goals

Sibling stories under epic PYPOST-832 delivered the agent UI testing stack:
application lifecycle, stable widget identity, UI actions, UI snapshots, settle
and wait helpers, and one golden product flow. Those pieces are documented
separately and runnable under the general fast test suite, but there is no
single developer entry point that explains the stack as a whole or a dedicated
project-standard command to run the agent e2e harness.

This task packages that stack for maintainers and agents: one cohesive
developer guide covering setup, tools, identity convention, and the golden
scenario, plus a Makefile target (or clearly documented extension of existing
test targets) so agent e2e is a first-class, documented workflow — not a
one-off shell-only recipe.

Business value: faster onboarding to agent UI e2e, fewer undocumented
`pytest` invocations, and a clear map from epic capabilities to how to run
and extend them.

## Programming Language

Python (`.cursor/lsr/do-python.md`) for any harness/test wiring; Makefile for
the run entry; Markdown for developer docs (`.cursor/lsr/do-markdown.md`).

## User Stories

- As a **maintainer**, I want one umbrella developer doc that links lifecycle,
  identity, actions, snapshot, wait, and the golden scenario so I can learn
  the agent e2e stack without hopping between unrelated guides.
- As a **maintainer / AI agent**, I want that doc to cover setup (how to run
  under the project’s offscreen GUI path), the tool surface agents use,
  the widget identity convention, and the golden product scenario so the
  intended workflow is explicit.
- As a **CI / local runner**, I want a Makefile target with a `##` help
  description that runs the golden scenario and related agent e2e harness
  tests so I do not invent ad-hoc shell commands.
- As a **developer reading testing or MCP docs**, I want cross-links to the
  agent e2e umbrella (and the Makefile entry) so I can distinguish in-process
  agent UI e2e from live MCP verification against a running app.
- As a **sibling story owner**, I want this packaging story to document and
  wire existing capabilities rather than redesign helpers or add new product
  flows beyond what siblings already delivered.

## Definition of Done

- A cohesive umbrella developer document exists under `doc/dev/` covering
  setup, tools, identity convention, and the golden scenario, and linking the
  existing sibling docs.
- A Makefile target (or documented extension of existing test targets) runs
  the agent e2e harness / related tests, appears in `make help` via a `##`
  description, and uses the project’s standard offscreen / test environment.
- Cross-links exist from `doc/dev/testing.md` and from MCP / related testing
  docs where appropriate so the agent e2e path is discoverable.
- No one-off undocumented shell-only workflow is the primary documented path;
  `make` is preferred.
- Scope stays on packaging and documentation; new golden product scenarios,
  helper redesign, and Jira ticket ops remain out of scope for this story.

## Task Description

**Problem:** After PYPOST-833–838, the agent UI e2e stack works piece by piece
and has per-capability docs, but maintainers still lack an umbrella guide and
a dedicated make entry. That invites undocumented `pytest` one-liners and
unclear ownership of “how do I run agent e2e?”

**Business need:** First-class docs and Makefile packaging so the epic’s
capabilities are discoverable and runnable through the project’s standard
quality workflow.

### In Scope

- Umbrella developer doc under `doc/dev/` linking the agent e2e stack
  (setup, tools, identity, golden scenario).
- Makefile target (preferred) or documented extension of existing test
  targets to run golden + related agent harness tests.
- Cross-links from testing docs and MCP / related docs as appropriate.
- Index updates under `doc/dev/README.md` so the umbrella is findable.
- Light updates to sibling docs that currently say packaging is “owned by
  839” so they point at the completed packaging entry.

### Out of Scope

- Designing or rewriting lifecycle / identity / actions / snapshot / wait APIs.
- Adding new golden product flows beyond the existing PYPOST-838 scenario.
- Changing CI job matrices beyond what the Makefile target naturally enables
  for local/maintainers (unless a minimal doc pointer is needed).
- User-facing product documentation (`doc/user/`).
- Jira transitions, worklogs, or git commit / branch operations (handled
  outside this story’s execution constraints when requested).

## Main Entities (business)

| Entity | Role |
| --- | --- |
| Agent e2e stack | Lifecycle, identity, actions, snapshot, wait, golden flow |
| Umbrella developer guide | Single entry doc for the stack |
| Agent e2e run entry | Project-standard command to execute related tests |
| Golden scenario | Existing composed Send → response product proof |
| Related harness tests | Sibling spot-checks / smokes that prove stack pieces |
| Testing / MCP docs | Discovery surfaces that should cross-link agent e2e |

## Constraints and Assumptions

- Sibling capabilities and the golden scenario already exist and remain the
  source of truth for behavior.
- Offscreen Qt / project-equivalent headless GUI settings remain the
  supported automation environment.
- Makefile remains the preferred interface for build/test workflows
  (workspace `makefile.mdc`).
- Docs stay in English; markdown follows project LSR line-length rules.

## Q&A

- Q: Why not only document `make test PYTEST_ARGS=…`?
  A: AC requires a make target or documented extension so agent e2e is not a
  one-off shell-only workflow; a dedicated target with `##` help meets that
  and remains discoverable via `make help`.

- Q: Does this story own new product flows?
  A: No — packaging and documentation of the existing stack and golden proof.

- Q: How does this relate to live MCP testing?
  A: MCP docs cover agents talking to a running PyPost via MCP. Agent e2e is
  in-process harness/pytest. Cross-links should clarify that distinction, not
  merge the two workflows.

- Q: Does this story own full epic CI redesign?
  A: No — provide the make entry maintainers and agents use; broader CI
  policy changes are follow-up if needed.
