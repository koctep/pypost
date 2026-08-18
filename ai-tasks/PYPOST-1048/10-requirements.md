# PYPOST-1048: Preserve sprint-management safety and membership guidance

## Programming Language

Python is the project language. English Markdown records the workflow
requirements.

## Goals

Two established sprint-management actions carry consequential meanings that
agents need when making planning decisions. One removes a sprint and may
affect the backlog; the other moves issues to the backlog and removes their
sprint membership. If this guidance becomes vague or incomplete, an agent may
make an unsafe or poorly informed choice even though the actions themselves
remain available.

**Business goal:** Keep the essential meaning of these existing actions clear
over time so agents can make safe, deliberate cleanup and replanning
decisions.

## User Stories

- As an **AI agent**, I want sprint-removal guidance to remain explicit about
  irreversibility and backlog-related consequences, so I can make a deliberate
  cleanup decision.
- As an **AI agent**, I want backlog-movement guidance to remain explicit that
  it removes issues from sprint membership, so I can replan work confidently.
- As a **contributor**, I want durable protection for this essential guidance,
  so future maintenance cannot quietly reduce its clarity.
- As a **product steward**, I want this work limited to preserving the meaning
  of existing actions, so it does not alter their purpose or supported user
  outcomes.

## Definition of Done

- [ ] Protection preserves the essential safety meaning of the existing
      sprint-removal action, including irreversibility and its backlog-related
      impact.
- [ ] Protection preserves the essential membership meaning of the existing
      backlog-movement action, including removing an issue from a sprint.
- [ ] The two established actions remain available with their existing
      purposes and meanings unchanged.
- [ ] The protection is durable, deterministic, credential-free, and does not
      expose secrets.
- [ ] This narrowly focused work does not alter user-visible behavior or
      expand the available sprint-management actions.

## Task Description

**Problem:** Confirming that an action is available does not ensure that its
guidance still communicates its key consequences. Guidance could become less
clear and make an irreversible action or a membership-removal action harder
for an agent to use safely.

**Scope (in):** Preserve the most important user-visible guidance for the
existing sprint-removal and backlog-movement actions.

**Scope (out):**

- Changing, adding, or removing sprint-management actions.
- Altering the purpose, outcome, or user-visible meaning of the established
  actions.
- Expanding the work into a broad rewrite of agent guidance.

**Constraints and assumptions:**

- The established actions and their existing meanings are the baseline for
  this work.
- The valuable outcome is durable clarity and safe decision-making, not a new
  user-visible capability.
- Protection must remain deterministic and credential-free.
- The wording may evolve, provided it continues to communicate the required
  irreversible/backlog and remove-from-sprint/membership meanings.

## Main Entities and Interactions

- **Sprint** — a planning container that an agent may need to remove when it
  should no longer exist.
- **Issue** — a work item whose sprint membership may need to be cleared
  during replanning.
- **Backlog** — the destination for an issue that is no longer part of a
  sprint.
- **Agent-facing action guidance** — the information an AI agent uses to
  understand consequences and choose the appropriate existing action.
- **Durable guidance protection** — the product-quality safeguard that keeps
  critical meaning available over time without credentials.

Interaction: an AI agent considers existing sprint-management actions, reads
their guidance, understands whether sprint removal has irreversible and
backlog-related consequences or whether backlog movement clears sprint
membership, and selects the appropriate action. The durable protection keeps
this information available as the product evolves.

## Non-Functional Requirements

- **Discoverability:** Critical action meaning must be clear enough for an
  agent to choose safely without relying on guesswork.
- **Durability:** Protection must preserve the critical meaning
  deterministically over time.
- **Credential safety:** Protection must not require credentials or expose
  secrets.
- **Scope discipline:** Preserve guidance only; do not change supported
  actions or user-facing behavior.

## Q&A

**Q:** Why is this needed when the actions remain available?

**A:** Availability proves that an action exists, but not that agents can
still understand its consequential safety or membership meaning. Both are
required for reliable sprint-management decisions.

**Q:** Does this add or modify a sprint-management capability?

**A:** No. It preserves the discoverability meaning of two established
actions.

**Q:** Why must the protection be credential-free?

**A:** The required outcome is a durable, deterministic safeguard for critical
guidance. It must remain repeatable, secret-safe, and independent of external
access.

