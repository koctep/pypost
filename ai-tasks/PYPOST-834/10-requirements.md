# PYPOST-834: Stable UI identity for key widgets

## Goals

AI agents and automated harnesses that drive PyPost after the lifecycle contract
([PYPOST-833](https://pypost.atlassian.net/browse/PYPOST-833)) need a reliable way
to find the same key controls on every run. Today most widgets lack stable
machine-facing identities: visible labels can change with theme or locale, and
sibling stories for snapshots, actions, and waits cannot depend on ad-hoc
widget traversal.

This task establishes the business contract for **stable UI identity** on the
critical surfaces agents must address: document the naming convention, apply it
to key widgets, keep identities stable across theme/locale where feasible, and
prove the contract with a spot-check.

## Programming Language

Python (`.cursor/lsr/do-python.md`)

## User Stories

- As an **AI agent** (or test harness), I want documented naming conventions for
  key controls so I can look up widgets by a stable identity instead of guessing
  from layout or translated text.
- As an **AI agent**, I want the main window, collection tree, request tabs,
  URL/method controls, Send, response panel, environments entry, and settings
  entry to each expose a stable identity after the UI is ready.
- As an **AI agent**, I want those identities to remain the same when the user
  changes theme or locale (where the product supports that), so scripts do not
  break on cosmetic changes.
- As a **maintainer**, I want a spot-check that critical widgets expose the
  expected identities so regressions are caught early.
- As a **sibling story owner** (snapshots, actions, waits), I want identity as a
  shared foundation so those stories do not invent competing naming schemes.

## Definition of Done

- A documented convention describes how key widgets receive stable identities
  (machine-facing names and/or accessible names as appropriate).
- The following key surfaces expose stable identities after UI ready:
  - main window
  - collection tree
  - request tabs
  - URL / method controls
  - Send control
  - response panel
  - environments entry point
  - settings entry point
- Identities remain stable across theme changes and, where the product supports
  locale variation, across locale — they must not be derived from translated or
  theme-dependent display text where feasible.
- An automated spot-check asserts that critical widgets expose the expected
  identities (runnable via the project’s standard test workflow).
- Scope stays on identity; snapshots, actions, settle waits, and golden flows
  remain sibling stories under PYPOST-832.

## Task Description

**Problem:** After launch and ready (PYPOST-833), agents still cannot reliably
address the same key UI controls. Without stable identities, automation depends
on fragile layout or visible labels that may change with theme or locale.

**Business need:** A small, durable identity contract so agents and sibling
stories can find critical surfaces by stable names before adding richer
observation and action tooling.

### In Scope

- Documented convention for stable widget identity on key surfaces.
- Stable identities on: main window, collection tree, request tabs, URL/method,
  Send, response panel, environments entry, settings entry.
- Stability across theme (and locale where feasible) for those identities.
- Spot-check coverage that critical widgets expose expected identities.
- Documentation of the convention for agents and maintainers (detail may land
  with this story or epic docs; the convention must be stated).

### Out of Scope

- Exhaustive identity for every widget in the product.
- Structured UI snapshots — PYPOST-835.
- UI action primitives — PYPOST-836.
- Settle/wait helpers — PYPOST-837.
- Golden end-to-end product scenario — PYPOST-838.
- Broader agent-e2e docs/`make` packaging — PYPOST-839.
- Changing lifecycle launch/ready/shutdown beyond using it for identity checks.
- Redesigning human-visible labels solely for automation (identities must not
  require changing what users read, except where an accessible name is already
  appropriate).

## Functional Requirements

- FR1: The project documents a naming convention for stable UI identities on
  key widgets (what agents should rely on and what must not be used as the sole
  identity when it can change with theme/locale).
- FR2: The main window exposes a stable identity.
- FR3: The collection tree exposes a stable identity.
- FR4: The request tabs surface exposes a stable identity.
- FR5: URL and method controls expose stable identities.
- FR6: The Send control exposes a stable identity.
- FR7: The response panel exposes a stable identity.
- FR8: Environments and settings entry points expose stable identities.
- FR9: For the key surfaces above, identities remain the same across theme
  changes and, where feasible, across locale — they are not tied to translated
  or theme-dependent display strings.
- FR10: An automated spot-check verifies that critical widgets expose the
  expected identities after the UI is ready.

## Non-functional Requirements

- **Stability:** Identities for key surfaces must not churn without an intentional
  convention change; they are a contract for agents and sibling stories.
- **Discoverability:** Agents and maintainers can find the documented convention
  and the list of key identities without reverse-engineering the UI.
- **Minimalism:** Only key surfaces required by the acceptance criteria; not a
  full accessibility audit of the entire app.
- **Compatibility with lifecycle:** Spot-checks may use the PYPOST-833 ready
  contract so identities are checked only when the UI is ready for interaction.
- **CI suitability:** Spot-check runs under the project’s offscreen/automated
  test path.

## Constraints and Assumptions

- Programming language: Python.
- Parent epic: [PYPOST-832](https://pypost.atlassian.net/browse/PYPOST-832).
  Builds on PYPOST-833 (`AgentAppSession`, `is_ui_ready`). Siblings own
  snapshots, actions, waits, golden flow, and packaging.
- “Stable identity” means a machine-facing name agents can use to locate a
  widget; it is distinct from user-visible labels that may be translated.
- Theme/locale stability means key identities do not change when those product
  settings change; it does not require implementing new locales if none exist.
- Step 1 review is treated as pre-approved under sprint-task-runner autonomy.

## Main Entities and Interactions

| Entity | Role |
| --- | --- |
| AI agent / harness | Locates key widgets by stable identity after UI ready |
| Stable UI identity | Machine-facing name for a key control or surface |
| Naming convention | Documented rules for how identities are chosen and kept stable |
| Key surface | One of the AC-listed areas agents must address |
| Spot-check | Automated verification that critical widgets expose expected identities |
| Theme / locale | Product settings that must not alter key identities where feasible |

Interaction overview:

1. Agent launches PyPost and waits until UI ready (PYPOST-833).
2. Agent uses documented identities to find key surfaces.
3. Sibling stories build snapshots/actions/waits on those identities.
4. Spot-check asserts expected identities are present after ready.

## Q&A

- Q: Why is this separate from snapshots and actions?
  A: Identity is the shared lookup contract. Snapshots and actions need stable
  targets; inventing names inside those stories would fragment the epic.
- Q: Why not identity every widget?
  A: High-priority surfaces unblock agents and siblings; exhaustive coverage is
  out of scope for this story.
- Q: Do identities replace accessible names for users?
  A: No. The convention may use machine-facing names and/or accessible names;
  user-visible labels remain for humans. The requirement is that agents have a
  stable target that does not depend on theme/locale display text where feasible.
- Q: Must locale be fully implemented to satisfy FR9?
  A: No. Where locale variation exists or is feasible, identities must not be
  derived from translated strings. Absence of multiple locales does not block
  Done if identities are locale-independent by design.
- Q: Why a spot-check instead of full e2e?
  A: Golden product flow is PYPOST-838. This story only proves key identities
  exist and match the convention.
