# PYPOST-835: UI state snapshot for agents

## Goals

AI agents and automated harnesses that drive PyPost after launch/ready
([PYPOST-833](https://pypost.atlassian.net/browse/PYPOST-833)) and stable widget identity
([PYPOST-834](https://pypost.atlassian.net/browse/PYPOST-834)) still cannot reliably **see** what
the UI currently shows. After an action (or before the next one), they need a structured
observation of the visible interface so they can verify outcomes instead of guessing from
side effects or screenshots alone.

This task establishes the business capability for a **UI state snapshot**: a structured view of
what is currently visible (roles, names, values, and hierarchy), suitable for post-action
verification, with sensitive values handled under the product’s existing masking and secrets
policies.

## Programming Language

Python (`.cursor/lsr/do-python.md`)

## User Stories

- As an **AI agent** (or test harness), I want a structured snapshot of the visible UI so I can
  confirm that an action produced the expected on-screen outcome.
- As an **AI agent**, I want the snapshot to include roles, names, values, and hierarchy so I can
  reason about what is shown and how controls relate, not only flat labels.
- As an **AI agent**, I want sensitive or secret values in the snapshot to follow the same masking
  and secrets rules the product already applies elsewhere (history, env UI, MCP exposure), so
  automation does not leak credentials that a human UI would hide.
- As a **maintainer**, I want automated coverage that the snapshot has a stable shape and
  includes basic expected content after the UI is ready, so regressions are caught early.
- As a **sibling story owner** (actions, waits, golden flow), I want observation as a shared
  capability so those stories can verify results without inventing competing “what do I see?”
  contracts.

## Definition of Done

- Agents and harnesses can obtain a structured snapshot of the visible PyPost UI that includes
  roles, names, values, and hierarchy sufficient to verify post-action outcomes.
- Sensitive values in snapshot output follow the product’s existing masking and secrets policies
  (hidden environment values and other policy-covered secret surfaces are not exposed in clear
  text where those policies already require masking or omission).
- Automated unit and/or integration coverage asserts snapshot shape and basic content (runnable
  via the project’s standard test workflow).
- Scope stays on observation/snapshot; identity remains PYPOST-834; actions, settle waits, and
  golden flows remain sibling stories under PYPOST-832.

## Task Description

**Problem:** After lifecycle ready (PYPOST-833) and stable identities (PYPOST-834), agents can
locate key controls but still lack a durable way to **inspect** what the UI currently displays.
Without a structured visible-state observation, verifying that a click, edit, or send changed
the right panel, tab, or field stays brittle or opaque.

**Business need:** A readable, structured snapshot of the visible UI so agents can check
post-action outcomes as part of the agent/MCP tooling epic, without inventing ad-hoc UI
traversal per story and without weakening existing secret-handling expectations.

### In Scope

- Capability for agents/harnesses to obtain a structured snapshot of the **visible** UI.
- Snapshot content at business level: roles, names, values, and hierarchy useful for verifying
  what changed after an action.
- Sensitive values in the snapshot obey existing masking/secrets product policy.
- Unit and/or integration tests covering snapshot shape and basic content.
- Use of prior lifecycle (ready) and identity work as foundations; this story does not re-own
  them.

### Out of Scope

- Defining or changing stable widget identity conventions — already PYPOST-834.
- UI action primitives (click, type, select, and similar) — PYPOST-836.
- Settle/wait helpers for UI quiescence — PYPOST-837.
- Golden end-to-end product scenario — PYPOST-838.
- Broader agent-e2e docs/`make` packaging — PYPOST-839.
- Changing agent lifecycle launch/ready/shutdown beyond using ready as a precondition for
  observation.
- Redesigning human-visible UI solely for automation.
- Replacing or rewriting the product’s masking/secrets policies; this story **applies** them to
  snapshot output where those policies already define sensitive handling.
- Exhaustive capture of every non-visible, offscreen, or historical UI detail beyond what is
  needed to describe the visible state for verification.

## Functional Requirements

- FR1: After the UI is ready for agent interaction, a consumer can obtain a structured snapshot
  of the currently visible UI.
- FR2: The snapshot conveys control/surface **roles**, **names**, **values**, and **hierarchy**
  so an agent can interpret what is shown and how parts relate.
- FR3: The snapshot is useful for verifying post-action outcomes (for example: expected panel
  content, selected tab, filled field, or status text after a prior step).
- FR4: Values that the product already treats as sensitive under masking/secrets policy appear
  in the snapshot only in a policy-compliant way (masked or omitted as those policies require
  for agent- or log-visible surfaces).
- FR5: Automated tests cover the snapshot’s expected shape and basic content after the UI is
  ready.
- FR6: Snapshot observation builds on the existing ready and identity foundations; it does not
  redefine lifecycle or naming conventions.

## Non-functional Requirements

- **Verifiability:** Snapshot content must be structured and stable enough that agents and tests
  can assert outcomes without relying on pixel comparison.
- **Secret safety:** Snapshot output must not become a back door around existing hidden-variable
  and secrets expectations for agent-visible or persisted surfaces.
- **Discoverability:** Maintainers and agent authors can understand what the snapshot represents
  (visible UI observation for verification) without reverse-engineering ad-hoc traversal.
- **Minimalism:** Capture what is needed to describe the visible state for verification; not a
  full product audit dump of every internal widget.
- **Compatibility with lifecycle:** Observation is meaningful once the UI is ready
  (PYPOST-833); tests may use that contract.
- **CI suitability:** Coverage runs under the project’s offscreen/automated test path.

## Constraints and Assumptions

- Programming language: Python.
- Parent epic: [PYPOST-832](https://pypost.atlassian.net/browse/PYPOST-832). Builds on
  PYPOST-833 (agent session lifecycle / UI ready) and PYPOST-834 (stable UI identity).
  Siblings own actions, waits, golden flow, and packaging.
- “Visible UI” means what a user would currently see in the running app surfaces in scope for
  agent verification — not a reconstruction of hidden internal state unrelated to display.
- “Structured” means machine-readable observation with roles, names, values, and hierarchy —
  not free-form prose or screenshot-only verification as the primary contract.
- Masking/secrets “existing policy” means the product’s current rules for hidden environment
  values and related agent-/history-facing sanitization; this story aligns snapshot exposure
  with those rules rather than inventing a parallel secrets model.
- Step 1 review is treated as pre-approved under sprint-task-runner autonomy.

## Main Entities and Interactions

| Entity | Role |
| --- | --- |
| AI agent / harness | Requests a snapshot after ready (and typically after an action) to verify outcomes |
| UI state snapshot | Structured observation of the currently visible UI |
| Role / name / value | Business attributes of a visible control or surface in the snapshot |
| Hierarchy | Parent/child (or nesting) relationships among visible surfaces in the snapshot |
| Sensitive value | Data already covered by product masking/secrets policy; must not appear clear in the snapshot where policy forbids it |
| UI ready | Precondition from PYPOST-833 before observation is reliable |
| Stable identity | Lookup foundation from PYPOST-834; snapshot may refer to named surfaces without redefining them |

Interaction overview:

1. Agent launches PyPost and waits until UI ready (PYPOST-833).
2. Agent may use stable identities (PYPOST-834) to act on key surfaces (sibling stories).
3. Agent obtains a UI state snapshot to verify what is currently visible.
4. Sensitive fields in that observation follow existing masking/secrets policy.
5. Tests assert snapshot shape and basic content after ready.

## Q&A

- Q: Why is this a separate story from identity and actions?
  A: Identity answers “how do I find a control?” Actions answer “how do I change it?” Snapshot
  answers “what does the UI show now?” Mixing them would blur epic ownership and acceptance.
- Q: Why not verify outcomes only via HTTP history or MCP tool results?
  A: Agents driving the GUI need on-screen confirmation (tabs, panels, field values, status).
  Backend or MCP envelopes do not replace visible UI state.
- Q: Does “roles, names, values, hierarchy” prescribe a wire format?
  A: No. Those are the business content dimensions the observation must convey. Concrete shape
  and transport are left to architecture (Step 2).
- Q: Must the snapshot include every widget in the application?
  A: No. It must describe the visible UI sufficiently for post-action verification. Exhaustive
  internal enumeration is out of scope.
- Q: What does “follow existing masking/secrets policy” mean in practice?
  A: Hidden environment values and other data the product already masks or withholds from
  agent-/history-facing surfaces must not appear in clear text in snapshot output. This story
  does not redefine those policies.
- Q: Is screenshot-only verification enough?
  A: No. Acceptance requires a structured snapshot suitable for automated checks of shape and
  content; screenshots alone are not the Done contract.
- Q: Why unit/integration coverage for shape and basic content?
  A: Golden end-to-end product flow is PYPOST-838. This story proves the observation contract
  exists and returns usable structured content after ready.
