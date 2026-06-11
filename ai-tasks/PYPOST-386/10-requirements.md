# PYPOST-386: Reduce redundant disk writes from frequent UI state changes

## Goals

PyPost persists certain UI choices (which collection nodes are expanded, which request tabs are
open, last selected environment) so the workspace looks the same after restart. Today, each
expand or collapse in the collections sidebar writes the full settings file to disk
immediately. Rapid toggling causes many redundant writes that are unnecessary at current scale
but can add I/O overhead and risk sluggish UI as usage grows.

This task addresses the follow-up from [PYPOST-8](https://pypost.atlassian.net/browse/PYPOST-8)
tech debt (“Synchronous tree-state saves”). Related consideration
[PYPOST-392](https://pypost.atlassian.net/browse/PYPOST-392) tracks the same business concern
(fewer redundant writes while keeping durable UI state) for when I/O from frequent saves becomes
noticeable.

**Programming language:** Python (PySide6).

## User Stories

- As a user, I want to expand and collapse collections quickly without the app feeling sluggish
  or doing unnecessary work on every click.
- As a user, I want my expanded collections (and other restored UI state) to match what I last
  had on screen when I reopen the app, including if I quit soon after changing expansion state.
- As a user, I want saving preferences from the Settings dialog to remain reliable and
  predictable when I confirm my changes.
- As a maintainer, I want UI-state persistence to avoid writing the settings file repeatedly
  when several changes happen in quick succession, while keeping existing save/restore behavior
  testable.

## Definition of Done

- Expanding or collapsing a collection no longer triggers a full settings-file write on every
  single toggle when changes arrive in rapid succession.
- After a burst of expand/collapse actions, the persisted expanded-collection list matches the
  final on-screen tree state.
- If the user closes the application shortly after changing UI state, the latest state is still
  written to disk before exit (no loss of expansion or other session state covered by this
  change).
- Restarting the app restores expanded collections correctly (no regression from PYPOST-388,
  PYPOST-389, PYPOST-391).
- Explicit Settings-dialog saves (user confirms OK) continue to persist immediately and apply
  as they do today.
- Redundant saves when the expanded list is unchanged remain skipped (existing no-op behavior
  preserved).
- Relevant unit and integration tests pass locally and in CI.

## Task Description

### Problem

UI session state is persisted through a central mechanism that writes the user settings file on
every change. The collections sidebar connects expand/collapse actions to that mechanism, so
each click can cause an immediate disk write of the entire settings document. Other automatic
UI-state updates (open tabs, ensuring a collection is expanded after save) use the same
immediate-write path.

Explicit preference changes from the Settings dialog are saved once when the user accepts the
dialog; that path is intentional and should not be degraded.

### Scope

**In scope**

- Automatic persistence of UI session state driven by frequent user interactions, with primary
  focus on collection expand/collapse.
- Ensuring pending UI state is flushed before application shutdown.
- Preserving correctness of save/restore for expanded collections, open tabs, and last
  environment where those flows share the same persistence mechanism.

**Out of scope**

- Changing the settings file format or which fields are stored.
- Settings-dialog field edits (saved only on OK today).
- Environment selection saves that bypass automatic UI-state persistence and write settings
  directly on each environment switch.
- Restore-time performance (addressed by PYPOST-390).

### Current behavior (for requirements accuracy)

| Trigger | What is persisted | When write happens |
| --- | --- | --- |
| Collection expand/collapse | Expanded collection ids | Immediately on each toggle |
| Tab open/close/save flows | Open tab request ids | Immediately on each tab-state change |
| Save request to collapsed collection | Expanded collection ids | Immediately when expansion is added |
| Settings dialog OK | Full user preferences | Once on dialog accept |
| Environment selection change | Last environment id (and related fields) | Immediately on selection |

The settings file stores all preferences in one document; each save rewrites the whole file.

### Non-functional requirements

- **Responsiveness:** Rapid expand/collapse and other frequent UI-state changes must not make
  the app feel sluggish; unnecessary disk work during bursts of interaction should be reduced.
- **Durability:** The latest on-screen UI state must still be written to disk before normal
  application exit and, where the platform allows, on unexpected close.
- **Correctness:** After restart, restored expanded collections, open tabs, and last environment
  must match the user's final on-screen state; no regression from existing restore behavior.
- **Predictability:** Explicit Settings-dialog saves must remain immediate and reliable when the
  user confirms changes.
- **Testability:** Existing automated tests for tree state and settings persistence remain the
  behavioral contract; changes must preserve verifiable save/restore semantics.

### Constraints and assumptions

- Typical usage involves a modest number of expanded collections; bursts of expand/collapse are
  the main concern, not thousands of simultaneous expansions.
- Users expect UI state to survive normal quit and unexpected close where the platform allows
  flush-on-exit.
- Existing automated tests for tree state and settings persistence define the behavioral
  contract to preserve.

### Main entities (business view)

| Entity | Description |
| --- | --- |
| **User preferences** | Explicit choices edited deliberately in the Settings dialog. |
| **Session UI state** | Transient workspace layout the user sees during a session. |
| **Persisted configuration** | Single user settings store on disk, loaded at startup and updated when state changes. |

**Key attributes (business):**

- **User preferences:** display and behavior options (e.g. font size, request timeout,
  encryption-related choices); saved only when the user confirms the Settings dialog.
- **Session UI state:** which collection nodes are expanded; which request tabs are open; last
  selected environment identifier.
- **Persisted configuration:** combined document holding user preferences and session UI state;
  rewritten as a whole when persisted; source of truth after restart.

**Interactions (business view):**

- User interactions in the collections sidebar and tab area update **session UI state** and
  trigger automatic persistence to **persisted configuration**.
- Settings dialog edits update **user preferences** and persist on explicit confirm, separate
  from rapid automatic UI-state updates.
- On startup, **persisted configuration** restores **session UI state** and **user preferences**
  so the workspace matches the user's last session.

## Q&A

- **Q:** Why address this now if PYPOST-8 marked it non-critical at current scale? **A:** The
  debt item is tracked for completion; reducing redundant writes during rapid interaction is
  low-risk hardening before larger libraries or faster interaction make I/O noticeable.
- **Q:** Is SettingsDialog part of this task? **A:** No. It already saves once on explicit
  confirm; requirements only note it must stay unchanged.
- **Q:** Should open-tab and last-environment automatic saves be included? **A:** Yes where they
  share the same immediate-write persistence path, so one consistent policy applies; expand/collapse
  remains the primary acceptance scenario.
- **Q:** Relation to PYPOST-392? **A:** PYPOST-392 raised the same follow-up concern; PYPOST-386
  delivers the business outcome (fewer redundant writes, durable state) that PYPOST-392
  anticipated.
- **Q:** Change visible behavior for users? **A:** No intentional UX change — responsiveness and
  durability should improve or stay the same; expansion after restart must match final UI state.
