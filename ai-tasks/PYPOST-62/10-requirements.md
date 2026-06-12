# PYPOST-62: history_panel _selected_entry linear scan

## Goals

Reduce per-selection lookup cost in the History sidebar when resolving the selected
history entry by ID.

## User Stories

- As a user browsing request history, I want selection changes (detail pane, Load into
  Editor, Copy as cURL) to stay responsive even when the history list grows large.

## Definition of Done

- `_selected_entry()` resolves the current list item's entry ID without scanning the
  full `_entries` list.
- The lookup structure stays consistent with `_entries` after `refresh()` (reload from
  `HistoryManager`).
- Existing History panel behaviour is unchanged (filter, detail pane, load, copy, delete).
- Automated tests cover indexed lookup and index rebuild on refresh.

## Task Description

Follow-up from PYPOST-41 TD-5: `_selected_entry()` currently iterates up to
`DEFAULT_MAX_ENTRIES` items on every selection event. Build an id→entry map alongside
`_entries` for constant-time lookup.

## Q&A

- **Q:** Does filtering need its own index?  
  **A:** No. List items store entry IDs; the index maps all loaded entries. Filter only
  affects which rows appear in the list widget.
