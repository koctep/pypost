# PYPOST-949: Tab-scoped wait_for_text on AgentAppSession

## Goals

[PYPOST-920](https://pypost.atlassian.net/browse/PYPOST-920) introduced stable
response status/body identities and golden Send settle via identity-scoped text
waits. UI actions already support `in_current_tab=True` (PYPOST-851) so
multi-tab flows can click/fill under the active request tab. Text and widget
**wait** helpers on `AgentAppSession` still root at the main window, so the
first matching `objectName` under the window wins — wrong for multi-tab Send
proofs where an inactive tab still exposes the same role ids with stale text.

**Business why:** Agent e2e and harness authors need the same tab-scoping
contract for waits as for actions, so multi-tab Send → response settle proofs
target the active tab without free-function workarounds or accidental matches on
background tabs.

Parent: [PYPOST-920](https://pypost.atlassian.net/browse/PYPOST-920) TD-2.
Browse: [PYPOST-949](https://pypost.atlassian.net/browse/PYPOST-949).

## Programming Language

Python (`.cursor/lsr/do-python.md`). Production change in
`pypost/agent/lifecycle.py`; tests under `tests/`. Task artifacts in English
Markdown (`.cursor/lsr/do-markdown.md`).

## User Stories

- As an **agent e2e author**, I want `session.wait_for_text(...,
  in_current_tab=True)` so Send settle on the active tab does not match stale
  status/body widgets on another tab.
- As a **harness maintainer**, I want related session waits (`wait_for_widget`,
  `wait_for_enabled`) to accept the same flag so tab-scoped readiness stays
  consistent with `ui_fill` / `ui_click`.
- As a **regression owner**, I want automated proof that window-scoped text
  wait fails the multi-tab scenario while tab-scoped wait succeeds, so the
  contract cannot regress silently.

## Definition of Done

- [x] `AgentAppSession.wait_for_text` accepts optional `in_current_tab=False`;
  when `True`, polls under `current_request_tab()` instead of `session.window`.
- [x] Related session waits (`wait_for_widget`, `wait_for_enabled`) mirror the
  same optional flag (default `False` preserves existing window-first behaviour).
- [x] Automated test demonstrates multi-tab Send: window-scoped wait for
  updated status fails; tab-scoped wait succeeds.
- [x] Developer docs describe the flag on session wait helpers and when to use
  it (multi-tab Send / per-tab role ids).
- [x] `make test` green for scoped modules; no user-facing `doc/user/` changes.

## Task Description

PYPOST-920 deferred tab-scoped session text waits. PYPOST-948 migrated sibling
e2e settle to `wait_response_after_send`, which roots free-function
`wait_for_text` at `current_request_tab()` when `in_current_tab=True` — a
workaround until session API parity. This task closes that gap on
`AgentAppSession` so callers can use `session.wait_for_text` directly.

Constraints:

- Default behaviour unchanged (`in_current_tab=False` → window root).
- Reuse existing `current_request_tab` / `_action_root` pattern from actions.
- No new wait primitive family; extend session wrappers only.
- Golden e2e may keep inline tab-root free function calls; no requirement to
  rewrite golden in this task.

## Q&A

| Q | A |
| --- | --- |
| Why not a generic `root=` override? | `in_current_tab` matches PYPOST-851 action API; keeps call sites uniform. |
| Must golden migrate to `session.wait_for_text`? | No — out of scope; golden tab-root calls remain valid. |
| Which waits are “related”? | `wait_for_widget` and `wait_for_enabled` — same per-tab id ambiguity as text wait. |
