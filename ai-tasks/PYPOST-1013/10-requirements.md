# PYPOST-1013: Context-menu Export Collection… on collection rows

## Programming language

Python

## Goals

Export Collection… already exists as a button below the collections tree (PYPOST-989).
On small windows that action row can sit off-screen, so users who have scrolled the
sidebar to a collection may not see or reach **Export Collection…** without
scrolling the panel layout back into view.

Collection rows already expose other actions via right-click (rename, delete). Adding
**Export Collection…** to that menu makes export discoverable and reachable from the
row the user is looking at, without relying on the below-tree action row being
visible.

The business goal is discoverability and reachability of an existing capability —
not a new export format or a second export product.

## User Stories

- As a **user**, I want to export a collection by right-clicking its row in the
  sidebar, so I can start export even when the below-tree **Export Collection…**
  control is off-screen on a small window.
- As a **user**, I want that context-menu export to behave like the existing
  **Export Collection…** action (same save flow, file content, and success/error
  feedback), so I do not have to learn two different export experiences.
- As a **user**, I want the existing **Export Collection…** button to keep working
  as today, so the context menu is an additional entry point, not a replacement.
- As a **user**, I want export from the context menu to apply to the collection I
  right-clicked (or the parent collection when I right-click a request inside it),
  so the menu targets the item under the pointer rather than a distant selection
  I may have forgotten.
- As a **maintainer**, I want automated coverage that the context-menu path can
  start export for a collection row, so the discoverability fix does not regress.

## Definition of Done

- [x] Right-clicking a **collection** row in the collections tree offers an
      **Export Collection…** action.
- [x] Choosing that action runs the same user-visible export outcome as the
      below-tree **Export Collection…** button: save dialog, native JSON file for
      one collection, success or error feedback, and no change to in-app
      collections.
- [x] Right-clicking a **request** row offers export of the **parent collection**
      (consistent with how the button resolves selection today).
- [x] The below-tree **Export Collection…** control remains available and
      unchanged in behavior.
- [x] Automated tests cover the context-menu export entry point for a collection
      row.
- [x] User-facing collections docs mention the context-menu export path alongside
      the existing button steps.

## Task Description

**Problem:** Export is only offered on the action row under the collections tree.
When that row is off-screen (common on small windows), users who are focused on a
collection in the tree have no obvious way to export it from the row they see.
Context menus already host other collection actions; export is missing there.

**Goal:** Add a context-menu **Export Collection…** action on collection (and, per
user stories, request) rows so export stays discoverable and usable without
depending on the below-tree button being visible.

### Scope (in)

- Context-menu entry that starts export for the collection associated with the
  right-clicked tree row.
- Same functional export outcome as PYPOST-989 (one collection → one JSON file,
  save location chosen by the user, success/error feedback, non-destructive).
- Keep the existing **Export Collection…** button as a parallel entry point.
- Automated tests for the context-menu path.
- Brief update to user-facing collections docs for the new entry point.

### Scope (out)

- Changing export file format, fidelity, or round-trip rules.
- Bulk export of all collections (PYPOST-1012).
- Shared JSON write-helper extraction (PYPOST-1011).
- New import entry points or import behavior changes.
- Postman / third-party exporters.
- Redesigning the collections sidebar layout or moving the action row.
- Removing or replacing the below-tree **Export Collection…** button.

## Assumptions

- Single-collection export via the below-tree **Export Collection…** button already
  exists and works as delivered by PYPOST-989.
- Collection (and related) tree rows already offer rename and delete via context
  menu; this task only adds an export entry point to that pattern.
- When a request is selected, the existing button already resolves export to the
  parent collection; context-menu export for a request row must match that.

## Main Entities and Interactions

- **Collection** — named group of requests in the sidebar tree; the unit of export.
- **Request** — saved item under a collection; right-click resolves to the parent
  collection for export.
- **Export action (button)** — existing below-tree control that exports the
  currently selected collection.
- **Export action (context menu)** — new right-click control that exports the
  collection associated with the clicked row.
- **Export file** — the same JSON artifact import already accepts.

Interaction flow: user right-clicks a collection (or request) in the tree → chooses
**Export Collection…** → chooses save location → file is written → confirmation or
error is shown. In-app collections are unchanged.

## Non-Functional Requirements

- **Parity:** context-menu export must produce the same kind of file and feedback as
  the button path.
- **Non-destructive:** export must not alter sidebar collections.
- **Discoverability:** the action must be available from the row the user is
  interacting with, independent of whether the below-tree action row is visible.
- **Consistency:** labeling and dialogs should feel like other collection tree
  context actions and like the below-tree **Export Collection…** button.
- **Clarity:** if nothing can be exported from the clicked row, the user must get a
  clear outcome (no silent no-op).

## Q&A

**Q:** Why add a context menu instead of only keeping the button?

**A:** On small windows the action row under the tree can be off-screen. Right-click
on the row in view is how users already reach rename/delete; export should be
reachable the same way for discoverability.

**Q:** Does this change what gets written to the file?

**A:** No. Same single-collection native JSON export as PYPOST-989.

**Q:** Does the button go away?

**A:** No. Context menu is an additional entry point; the button stays.

**Q:** What if the user right-clicks a request?

**A:** Export the parent collection (whole collection with all requests), matching
how the button treats a selected request today. Omitting export from request rows
is not an option.

**Q:** Is export-all or format work in scope?

**A:** No. Those are separate follow-ups (e.g. PYPOST-1012).
