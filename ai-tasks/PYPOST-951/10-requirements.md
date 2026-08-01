# PYPOST-951: Document removeTab orphan hazard for agents

## Goals

AI agent and golden e2e authors who manipulate the request tab strip need a
clear developer warning about Qt `removeTab` orphan hazards. Without it, tests
that strip tabs (for example the plus-tab create precondition from PYPOST-921)
fail mysteriously or drive the wrong tab because window-scoped identity lookups
match detached widgets that still carry shared per-tab role ids.

**Business why:** Reduce wasted debugging time and flaky agent e2e when authors
use direct tab-strip manipulation instead of presenter close paths.

Parent: [PYPOST-921](https://pypost.atlassian.net/browse/PYPOST-921) (plus-tab
create golden). Follow-up from PYPOST-921 TD-2.

Browse: [PYPOST-951](https://pypost.atlassian.net/browse/PYPOST-951).

## Programming Language

English Markdown (`.cursor/lsr/do-markdown.md`). Documentation only.

## User Stories

- As an **agent e2e author**, I want a documented warning about `removeTab` +
  orphan role ids so I know why window-scoped finds fail after stripping tabs.
- As a **golden-flow maintainer**, I want the safe strip pattern (`deleteLater`
  + `processEvents` + current-tab scope) written down next to the plus-tab
  scenario so I can reuse it without reading test source first.
- As a **maintainer**, I want cross-links from umbrella agent e2e and ui_actions
  troubleshooting so the hazard is discoverable outside the golden doc alone.

## Definition of Done

- Developer documentation includes a **broader** note (not only a one-line
  mention) warning about `removeTab` + `deleteLater` orphan hazards for agent
  e2e authors.
- The note explains symptoms, cause, safe strip pattern, and current-tab
  scoping after tab manipulation.
- Umbrella agent e2e and/or ui_actions docs cross-link the hazard section.
- Unticketed follow-ups (if any) live only in this task's `60-tech-debt.md`.

Acceptance (from Jira): **Dev doc note warns about removeTab + deleteLater
orphan hazards for agent e2e authors.**

## Task Description

**Problem:** PYPOST-921 added plus-tab golden coverage and brief mentions of
`removeTab` + `deleteLater` in `agent_golden_e2e.md`, but agent authors still
lack a consolidated hazard guide. PYPOST-921 TD-2 called for broader
documentation (possibly in ui_actions).

**Business need:** Authors copying the blank-tab strip pattern must understand
Qt semantics and identity scoping without reverse-engineering
`_strip_request_tabs`.

### In Scope

- Expand developer docs with removeTab orphan hazard guidance.
- Cross-links from related agent e2e / ui_actions pages.
- Task artifacts for top-down Steps 1–8.

### Out of Scope

- Production code or test changes (reference existing golden helper only).
- Changing tab close product behavior or presenter APIs.
- Jira ticket creation for follow-ups this run.

## Constraints and Assumptions

- Reference implementation already exists in
  `tests/test_agent_golden_e2e.py::_strip_request_tabs` (PYPOST-921).
- Per-tab role ids are shared across tabs ([ui_identity.md](../../doc/dev/ui_identity.md)).
- Docs-only; no failing repro test required.

## Main Entities (business)

- **Request tab strip** — Qt tab widget holding request editors and plus chrome.
- **Orphan tab page** — detached widget still alive after `removeTab`.
- **Agent identity lookup** — window- or tab-scoped find by stable role id.
- **Strip precondition** — test setup that removes tabs without presenter close.

## Q&A

| Q | A |
| --- | --- |
| Why not only the existing golden doc bullets? | Acceptance asks for a broader warning; PYPOST-921 TD-2 explicitly deferred this. |
| Add new tests? | No — document existing pattern; behavior already covered by golden. |
| Create Jira follow-ups this run? | No — list debt in `60-tech-debt.md` only. |
