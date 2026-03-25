# PYPOST-405: Open request in a new independent tab

## Goals

Users who edit the same saved request in more than one tab need a clear way to open an
additional tab without sharing unsaved edits across tabs. The product should behave like
separate editor buffers for the same underlying saved item, so work in one tab does not
unexpectedly change what another tab shows before save or reload.

Deliver a discoverable action from the Collections tree (context menu on a request) with
short labeling equivalent to “open in new tab,” while keeping global environment behavior
unchanged.

## User Stories

- As a **PyPost user**, I want to **open a saved request in a new tab from the Collections
  tree**, so that I can compare or adjust drafts side by side without one tab mirroring
  unfinished edits from another.
- As a **PyPost user**, I want **only request rows** to offer this action (not collection
  folders), so the menu stays predictable.
- As a **PyPost user**, I expect the **new tab title to match the request name**, so I can
  tell which request I opened.

## Definition of Done

- A context-menu item exists on **request** items in the Collections tree; it is absent for
  **collection** folder rows.
- Choosing the action opens a **new tab** with the correct request name in the tab label.
- With **two tabs** for the same saved request, **editing in one tab does not update the
  other** through a shared in-memory document; each tab keeps its own unsaved state until
  save or explicit reload behavior (if any) applies.
- **Saving** from either tab still updates persisted data as today; if the other tab keeps
  an older buffer after a save elsewhere, that is acceptable for this task unless the team
  expands scope.
- **Shared environment variables** for the window may still apply to all tabs (not considered
  “another tab’s edits”).

## Task Description

PyPost is a desktop HTTP client. The Collections sidebar lists collections and their saved
requests. Users open requests in tabs to edit method, URL, headers, body, and scripts.

Today, opening the same request more than once may reuse one in-memory model, so changes in
one tab can appear in another. The business need is **editor independence** for the new-tab
action: users should trust that a newly opened tab is a separate working copy until they
save.

**Constraints and assumptions**

- Wording in the UI should be concise; English UI strings should align with existing
  actions (e.g. Rename, Delete). A tooltip may explain independence if the label is short.
- **Programming language for implementation:** Python (PySide6 / Qt).

**Entities (business view)**

- **Saved request:** a named request belonging to a collection, with fields users edit before
  sending HTTP traffic.
- **Tab:** one editing surface for a saved or new request; multiple tabs may refer to the
  same saved identity but must not share unsaved buffer state for this feature.
- **Environment:** global variables for the window; out of scope for “independence” in this
  ticket.

## Q&A

| Question | Answer |
|----------|--------|
| Jira issue | [PYPOST-405](https://pypost.atlassian.net/browse/PYPOST-405) |
| Issue type in Jira | Story (`Task` is not configured on this project) |
