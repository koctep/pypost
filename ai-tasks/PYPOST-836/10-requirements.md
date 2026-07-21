# PYPOST-836: Agent UI action tools

## Goals

AI agents and automated harnesses that can launch PyPost
([PYPOST-833](https://pypost.atlassian.net/browse/PYPOST-833)), address controls by stable
identity ([PYPOST-834](https://pypost.atlassian.net/browse/PYPOST-834)), and observe visible
state ([PYPOST-835](https://pypost.atlassian.net/browse/PYPOST-835)) still cannot **drive** the
UI in a shared, intentional way. Without common action primitives, each harness invents its
own click/type/select paths, and failures when a target is missing or not usable stay opaque.

This task establishes the business capability for **agent UI action tools**: a small set of
interaction primitives (click, type/fill, select, send key/hotkey) that address widgets by
stable identity and report actionable errors when the target cannot be used.

## Programming Language

Python (`.cursor/lsr/do-python.md`)

## User Stories

- As an **AI agent** (or test harness), I want to click, type/fill, select, and send keys
  against named UI controls so I can drive flows without inventing per-story interaction
  helpers.
- As an **AI agent**, I want actions to address controls by stable identity (widget ids from
  PYPOST-834) so my scripts survive theme, layout, and copy changes that do not change
  identity.
- As an **AI agent**, I want clear, actionable errors when a target is missing or not
  interactable so I can recover or fail with a useful diagnosis instead of silent no-ops.
- As a **maintainer**, I want automated coverage of each primitive against a fixture UI or a
  main-window subset so regressions in action behavior are caught early.
- As a **sibling story owner** (settle waits, golden flow), I want a shared action surface so
  those stories compose drive → observe → wait without competing interaction contracts.

## Definition of Done

- Agents and harnesses can perform click, type/fill, select, and send key/hotkey against
  controls addressed by stable widget identity from PYPOST-834.
- Action delivery follows the project’s existing agent/MCP tooling patterns for how agents
  obtain capabilities (prefer MCP tools **or** a local agent interface consistent with those
  patterns — one coherent surface, not a one-off side channel).
- When a target is missing or not interactable, the consumer receives an actionable error
  (clear enough to identify which identity failed and why interaction was refused).
- Automated tests cover each primitive against a fixture UI and/or a main-window subset
  (runnable via the project’s standard test workflow).
- Scope stays on action primitives; lifecycle, identity catalog, snapshot, settle waits, and
  golden flows remain sibling stories under PYPOST-832.

## Task Description

**Problem:** After lifecycle ready, stable identities, and UI snapshot, agents can find and
observe key controls but still lack a durable, shared way to **act** on them. Ad-hoc
widget method calls per test make agent e2e brittle and do not give a product-supported
error contract when a target is gone or disabled.

**Business need:** A small, intentional set of UI action primitives so agents can drive the
app by identity as part of the agent/MCP tooling epic, with failures that explain themselves,
without redesigning the human UI solely for automation.

### In Scope

- Action primitives: click, type/fill, select, send key/hotkey.
- Addressing targets by stable widget identity (PYPOST-834).
- Prefer MCP tools **or** a local agent interface consistent with existing MCP/agent patterns.
- Actionable errors when the target is missing or not interactable.
- Tests covering each primitive against a fixture UI or main-window subset.
- Use of prior lifecycle (ready), identity, and snapshot work as foundations; this story does
  not re-own them.

### Out of Scope

- Defining or changing stable widget identity conventions — already PYPOST-834.
- UI state snapshot observation — already PYPOST-835.
- Settle/wait helpers for UI quiescence — PYPOST-837.
- Golden end-to-end product scenario — PYPOST-838.
- Broader agent-e2e docs/`make` packaging — PYPOST-839.
- Changing agent lifecycle launch/ready/shutdown beyond using ready as a precondition for
  reliable interaction.
- Redesigning human-visible UI solely for automation.
- Exhaustive coverage of every exotic widget type beyond what the primitives need for key
  surfaces and fixtures.
- Drag-and-drop, multi-touch, or accessibility-tree-only drivers as the primary contract.

## Functional Requirements

- FR1: After the UI is ready for agent interaction, a consumer can invoke click, type/fill,
  select, and send key/hotkey against a control identified by stable widget identity.
- FR2: Actions resolve targets using the identity contract from PYPOST-834 (not visible label
  text as the primary address).
- FR3: When the identified target does not exist in the current UI, the consumer receives an
  actionable error naming the missing identity.
- FR4: When the identified target exists but is not interactable (for example disabled or
  otherwise not usable for that primitive), the consumer receives an actionable error
  explaining why interaction was refused.
- FR5: Successful actions produce the expected control effect for that primitive (button
  activates, text is entered, selection changes, key/hotkey is delivered).
- FR6: Automated tests cover each primitive against a fixture UI and/or a main-window subset.
- FR7: The action surface is delivered in a way consistent with existing agent/MCP tooling
  patterns in the product (MCP tools or an equivalent local agent interface — not an
  undocumented one-off).

## Non-functional Requirements

- **Actionability of failures:** Errors must be specific enough for agents and maintainers to
  diagnose missing vs not-interactable targets without reading stack traces alone.
- **Identity stability:** Actions must not depend on locale-sensitive visible labels as the
  primary address.
- **Discoverability:** Maintainers and agent authors can understand the supported primitives
  and error contract without reverse-engineering tests.
- **Minimalism:** A small primitive set sufficient for agent flows; not a full GUI robot
  framework.
- **Compatibility with lifecycle and observation:** Actions are meaningful once the UI is
  ready (PYPOST-833); consumers may combine them with snapshot (PYPOST-835) for verification.
- **CI suitability:** Coverage runs under the project’s offscreen/automated test path.

## Constraints and Assumptions

- Programming language: Python.
- Parent epic: [PYPOST-832](https://pypost.atlassian.net/browse/PYPOST-832). Builds on
  PYPOST-833 (lifecycle / UI ready), PYPOST-834 (stable UI identity), and PYPOST-835
  (snapshot). Siblings own waits, golden flow, and packaging.
- “Stable identity” means the widget id / naming contract from PYPOST-834.
- “Actionable error” means a failure that identifies the target and the refusal reason at a
  business level (missing vs not interactable); concrete exception types are left to
  architecture.
- “Consistent with existing MCP patterns” allows either registering MCP tools or exposing an
  equivalent local agent API that matches how agents already consume capabilities in this
  epic; Step 2 chooses the delivery surface.
- Step 1 review is treated as pre-approved under sprint-task-runner autonomy.

## Main Entities and Interactions

| Entity | Role |
| --- | --- |
| AI agent / harness | Invokes action primitives after ready to drive the UI |
| Action primitive | Click, type/fill, select, or send key/hotkey |
| Stable identity | Address of the target control (PYPOST-834) |
| Target control | Named UI surface the primitive acts on |
| Actionable error | Failure when identity is missing or not interactable |
| UI ready | Precondition from PYPOST-833 before actions are reliable |
| UI snapshot | Optional post-action verification from PYPOST-835 |

Interaction overview:

1. Agent launches PyPost and waits until UI ready (PYPOST-833).
2. Agent addresses controls by stable identity (PYPOST-834).
3. Agent invokes action primitives (this story) to change the UI.
4. On missing/not-interactable targets, the agent receives an actionable error.
5. Agent may obtain a UI snapshot (PYPOST-835) to verify outcomes.
6. Tests cover each primitive against a fixture and/or main-window subset.

## Q&A

- Q: Why is this a separate story from snapshot and identity?
  A: Identity answers “how do I find a control?” Snapshot answers “what do I see?” Actions
  answer “how do I change it?” Mixing them would blur epic ownership and acceptance.
- Q: Must actions be network MCP tools?
  A: Acceptance requires MCP tools **or** a local agent interface consistent with existing
  MCP/agent patterns. Architecture chooses the surface that fits the epic’s in-process
  harness model.
- Q: Does “type/fill” mean character-by-character typing only?
  A: Business intent is entering text into a control. Exact delivery mechanism is left to
  architecture as long as the field ends up with the intended content and failures remain
  actionable.
- Q: Does “select” cover only combo boxes?
  A: It covers choosing among options in selectable controls agents need for key flows
  (for example combo/list-style selection). Exotic multi-select trees can be deferred if
  not needed for the primitive contract.
- Q: Why fixture UI and/or main-window subset?
  A: Golden end-to-end product flow is PYPOST-838. This story proves each primitive works
  against controlled surfaces without owning the full product scenario.
- Q: Are settle waits part of this story?
  A: No. Waiting for quiescence after actions is PYPOST-837.
