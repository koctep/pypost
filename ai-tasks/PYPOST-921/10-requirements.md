# PYPOST-921: Plus-tab create path in golden flow

## Goals

AI agents and golden/e2e maintainers must prove they can **create a blank
request via the plus-tab control** and complete the same Send → response proof
when session restore does **not** hand them a ready blank request tab.

Today the golden flow relies on fresh-session blank restore (`opened_blank_tab`)
and never exercises plus-tab create. If restore stops opening a blank tab, the
golden open/create step has no covered agent path.

**Business why:** Guard agent and golden coverage against lifecycle restore
behavior shifts so “create request then send” remains proven without depending
on blank-tab restore.

Source: [PYPOST-853](https://pypost.atlassian.net/browse/PYPOST-853) TD-4.
Browse: [PYPOST-921](https://pypost.atlassian.net/browse/PYPOST-921).

## Programming Language

Python (`.cursor/lsr/do-python.md`). Agent/golden harness and UI identity
coverage. Developer docs in English Markdown (`.cursor/lsr/do-markdown.md`).

## User Stories

- As an **AI agent / e2e author**, I want a stable, clickable identity on the
  plus-tab create control so I can open a new request tab without calling
  presenter internals.
- As a **golden-flow maintainer**, I want an agent_e2e / golden scenario that
  starts from a “no blank request tab” precondition, creates via plus-tab, then
  completes Send → response settle — so restore changes do not silently remove
  open/create coverage.
- As a **maintainer**, I want developer docs for golden e2e to document that
  blank restore is optional and plus-tab create is the covered fallback path.

## Definition of Done

- Agents can target the plus-tab **create** control via a stable widget identity
  and the existing click action (not presenter `add_new_tab` / `handle_new_tab`
  bypasses as the primary covered path).
- Golden or agent_e2e covers: simulate or start without a usable blank request
  tab → create via plus-tab → fill URL/method → Send → settle on response
  status/body (same canned HTTP contract as the main golden).
- Developer golden/agent docs describe blank-restore vs plus-tab create and how
  to run the new scenario.
- Unticketed follow-ups (if any) live only in this task’s `60-tech-debt.md`
  (no Jira ticket creation in this run).

Acceptance (from Jira): **Golden or agent_e2e covers creating a request via
plus-tab when restore does not open a blank tab.**

## Task Description

**Problem:** The golden product flow assumes restore already opened a blank
request tab. Plus-tab create is unit-tested in tab header / tabs presenter, but
not composed in agent/golden e2e. Parent debt (PYPOST-838 / PYPOST-853 TD-4)
called out this gap explicitly.

**Business need:** When blank restore changes or is absent, agents still need a
proven create path that matches real user chrome (the trailing `+` control).

### In Scope

- Stable identity on the plus-tab create button (agent-clickable).
- Agent/golden e2e coverage for create-via-plus when no blank request tab is
  available, then the existing Send → response proof.
- Docs updates for golden / agent e2e guidance.

### Out of Scope

- Changing default restore behavior (still may open a blank tab today).
- Redesigning plus-tab chrome or keyboard Ctrl+N as the primary covered path
  (shortcut may remain a secondary path; acceptance asks for plus-tab).
- Broader agent-e2e packaging (`make` umbrella) — owned by PYPOST-922.
- Migrating sibling e2e modules beyond this create-path scenario.

## Constraints and Assumptions

- Fresh agent sessions may still restore one blank tab today; the new scenario
  must **force** a no-blank-request-tab precondition rather than waiting for
  product restore to change.
- Closing the last request tab via normal close currently recreates a blank;
  the scenario must not rely on that auto-replacement as “create via plus.”
- Existing unit coverage of plus click (header + presenter) remains; this task
  adds agent composition, not a replacement for those unit tests.
- Shared HTTP canned golden stub and status/body text waits remain the settle
  contract (PYPOST-859 / PYPOST-920).

## Main Entities (business)

- **Blank request tab** — empty request editor ready for URL/method/Send.
- **Plus-tab create control** — trailing `+` chrome that opens a new blank
  request.
- **Session restore** — startup behavior that may or may not open a blank tab.
- **Golden / agent e2e scenario** — composed lifecycle + identity + actions +
  wait proof.

## Q&A

| Q | A |
| --- | --- |
| Why not only document that blank restore is enough? | Parent TD-4 requires coverage when restore does **not** open a blank tab. |
| Why plus-tab and not Ctrl+N? | Acceptance names plus-tab; unit tests already treat plus as the primary chrome path. |
| Change restore product behavior? | No — force the precondition in the test; keep current restore. |
| Create Jira follow-ups this run? | No — list debt in `60-tech-debt.md` only. |
