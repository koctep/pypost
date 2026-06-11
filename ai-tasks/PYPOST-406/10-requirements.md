# PYPOST-406: Collections — unify left-click tree navigation object-copying behavior

## Goals

PyPost users open saved requests from the Collections sidebar to edit and send HTTP traffic.
When the same saved request appears in more than one tab, each tab should behave like an
independent editor buffer: unsaved changes in one tab must not appear in another until the
user saves or explicitly reloads.

The context-menu **New tab** action (PYPOST-405) already opens an isolated copy. Left-click
navigation still reuses the same in-memory request object as the tree in some flows, so edits
can leak across tabs opened from the sidebar. This task closes that gap so every **new tab
populated from a tree click** gets its own working copy, matching user expectations set by
**New tab** and session restore.

## Programming Language

Python (PySide6 / Qt), consistent with the PyPost desktop application.

## User Stories

- As a **PyPost user**, I want **left-clicking a saved request in Collections** to open a tab
  with its **own unsaved state**, so editing in one tab does not immediately change another
  tab for the same request.
- As a **PyPost user**, I expect **left-click and New tab** to follow the **same isolation
  rules** when a fresh tab is filled from the tree, so I do not need to remember which gesture
  is safe for parallel drafts.
- As a **PyPost user**, I still want **tab titles and save/rename behavior** for a request id
  to work as today after this change.

## Definition of Done

- Left-clicking a **request row** in Collections and opening a **new tab** gives that tab an
  **independent working copy** of the request fields (method, URL, headers, body, etc.).
- With **two tabs** opened for the same saved request via left-click (or left-click plus
  **New tab**), **editing in one tab does not update the other** through shared in-memory
  state.
- **Saving** from either tab continues to update persisted data and the Collections tree as
  today; sibling-tab stale notification from PYPOST-408 continues to apply where relevant.
- **Collection folder** left-clicks still expand/collapse only (no tab opened).
- Automated tests verify isolation for the tree left-click path (or equivalent tab-open path).

## Task Description

PyPost is a desktop HTTP client. The Collections tree lists saved requests. Users left-click
requests to open them in tabs. PYPOST-405 added **New tab** with isolated copies but
deliberately left left-click unchanged. Follow-up work (PYPOST-408) added stale-state
awareness across isolated tabs. Left-click sharing remains a trust and data-integrity gap:
users who open the same request twice from the tree can still see cross-tab edit leakage.

The business need is **consistent editor independence** for any fresh tab populated from the
Collections tree, aligned with **New tab** and restored sessions.

### In Scope

- Object-copying behavior when a **new tab** is created and populated from a **left-click** on
  a request in the Collections tree.
- Verification through automated tests.

### Out of Scope

- Changing whether left-click **focuses an existing tab** vs always opening a new tab (tab
  reuse policy).
- History panel, blank **+** tab, or other non-tree tab creation paths unless required for
  consistency with the tree open path.
- Real-time merge of concurrent drafts; external file change detection.
- Global environment variable synchronization (remains window-wide).

### Constraints and Assumptions

- Multiple tabs may reference the same saved request **identity** while holding separate
  in-memory drafts.
- The Collections tree continues to hold canonical saved instances from storage; reloading
  after save refreshes the sidebar without merging unsaved tab buffers into tree nodes.
- English UI strings are unchanged for this task.

## Functional Requirements

- Opening a request in a tab via **Collections left-click** must not share mutable request
  field state with other open tabs or with the tree item’s in-memory object.
- Isolation must cover nested request fields (headers, params, body, etc.), not only top-level
  attributes.
- Existing rename, save, delete, and sibling stale-notification flows must not regress.

## Non-functional Requirements

- **Predictability:** left-click and **New tab** behave consistently regarding unsaved-state
  isolation.
- **Safety:** no silent cross-tab mutation of draft content.
- **Performance:** copy cost remains acceptable for typical request sizes (same as PYPOST-405).

## Main Entities and Interactions

| Entity | Role |
|--------|------|
| **Saved request** | Named item in a collection; stable identity; source for tab content. |
| **Collections tree row** | User selects a request to open; must not tie multiple tabs to one draft buffer. |
| **Open tab** | Editing surface with its own in-memory draft linked to a saved request id. |
| **New tab (context menu)** | Reference behavior for isolated open from the tree (PYPOST-405). |

Interaction overview:

1. User left-clicks a saved request in Collections.
2. Application opens (or populates) a tab with a **separate working copy** of that request.
3. User opens the same request again; each tab keeps independent unsaved edits until save or
   explicit reload per PYPOST-408 flows.

## Q&A

| Question | Answer |
|----------|--------|
| Jira issue | [PYPOST-406](https://pypost.atlassian.net/browse/PYPOST-406) |
| Why not change tab focus behavior? | Out of scope; this task addresses shared object references when a fresh tab is populated. |
| Relation to PYPOST-405 / 408? | 405 established isolated **New tab**; 408 added stale sync across isolated tabs; 406 extends isolation to left-click. |
| Autonomous sprint execution? | Steps 1–3 run without per-step user approval per sprint-task-runner. |
