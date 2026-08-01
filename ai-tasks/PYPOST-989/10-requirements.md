# PYPOST-989: Export collection

## Programming language

Python

## Goals

PyPost can import collections from JSON (PYPOST-987), but users still had no in-app way to
produce those files from the sidebar. Export closes the loop: save the selected collection
(with all requests) to a file compatible with import, for backup, sharing, or moving setups
between machines — without copying files out of the data directory by hand.

## User Stories

- As a **user**, I want to export the collection I selected in the sidebar to a file, so I
  can back up or share it without finding my PyPost data folder.
- As a **user**, I want the exported file to work with **Import Collection…**, so export
  and import round-trip on my installation.
- As a **user**, I want clear success or error feedback after export.
- As a **user**, I want to start export from near the collections tree, consistent with
  Import Collection.

## Definition of Done

- [x] **Export Collection…** action below the collections tree (near Import).
- [x] Exports the selected collection (click collection or a request inside it).
- [x] Save dialog; native PyPost JSON format (single object).
- [x] Success/error feedback; automated tests; `doc/user/collections.md` updated.

## Task Description

**Problem:** Sharing a collection today means locating `collections/<id>.json` in the data
directory or re-entering every request manually on another machine. Import exists, but there
is no matching export action in the UI.

**Goal:** Add **Export Collection** near the collections tree. Write the selected collection
and its requests to a user-chosen file in the same format import accepts.

**Scope (in):**

- Export the selected sidebar collection (including all requests).
- Native JSON format round-tripping with PYPOST-987 import.
- Save dialog, success and error feedback.
- Automated tests and user documentation.

**Scope (out):**

- Postman or third-party exporters.
- Import (already shipped).
- Environments export/import (separate stories).
- Exporting multiple collections in one file (import supports lists, but this story exports
  one selected collection at a time).

## Main Entities and Interactions

- **Collection** — named group of requests in the sidebar tree.
- **Request** — saved HTTP call inside a collection.
- **Export action** — user picks a collection (via tree selection), chooses a save path,
  receives confirmation or an error.
- **Export file** — JSON artifact import can load.

Interaction flow: user selects a collection in the tree → clicks **Export Collection…** →
chooses save location → file is written → confirmation shows path and request count.

## Non-Functional Requirements

- **Fidelity:** every request field needed to send, save, or re-import must appear in the
  file.
- **Non-destructive:** export must not change in-app collections.
- **Clarity:** errors (no selection, disk failure) must be specific and visible.
- **Consistency:** discoverability and dialog style match Import Collection and Export
  Environments.

## Q&A

**Q:** What is exported when the user selected a request instead of the collection row?

**A:** The parent collection — the whole collection with all requests is exported, not a
single request.

**Q:** Single object or list in the file?

**A:** One selected collection → single JSON object, matching one on-disk
`collections/<id>.json` file. Import already accepts that shape.

**Q:** Is export-all-collections in scope?

**A:** No. This story exports one selected collection at a time. Bulk export can be a
follow-up if needed.

**Q:** Hidden secrets confirmation like environment export?

**A:** No. Collections hold request definitions, not environment secrets. No extra
confirmation beyond the save dialog.

## Worklog

tokens_used: 8000
role: execution
step: 1
step_name: Requirements
