# PYPOST-1011: Extract shared JSON export write helper

## Programming language

Python

## Goals

PyPost has two independent "export to file" features — collections (PYPOST-989) and
environments (PYPOST-988) — each with its own `write_export_file()` that writes a payload to
disk as indented, UTF-8 JSON with a trailing newline. The two copies were written
independently and have quietly drifted: they catch different exception sets around the same
`json.dumps`/`write_text` calls, so a payload that fails to serialize is handled safely on the
collection side but can crash out as an unhandled exception on the environment side. Every
future export feature (or a fix to this write behavior) currently has to be applied twice, and
any second edit that isn't kept in lockstep reintroduces this kind of silent inconsistency.
Consolidating the file-write logic into one place removes the drift risk and the duplicated
maintenance cost, and guarantees both export features behave identically going forward.

## User Stories

- As a **user exporting an environment**, I want a write failure to always show a clear
  in-app error message (never an unhandled crash), so my experience matches exporting a
  collection.
- As a **developer**, I want one place that implements "write an export payload to disk," so
  fixing a bug or changing the write behavior (e.g. formatting, error handling) automatically
  applies to every export feature instead of requiring me to remember and update every copy.
- As a **developer adding a future export feature** (e.g. exporting requests, or another
  entity type), I want an existing, tested write helper to reuse, so I don't have to
  copy-paste the same file-write logic a third time.

## Definition of Done

- [ ] Collection export and environment export share one implementation of the "write export
      payload to file" behavior — no duplicated write logic between the two features.
- [ ] Both features report file-write failures to the user the same way (same class of
      failures caught and surfaced as a clear, in-app error), closing the current gap where an
      unserializable environment payload is not caught before reaching the user.
- [ ] Existing export behavior is unchanged from the user's perspective: same output file
      format/content, same success feedback, same log messages that operators already rely on
      for these two features.
- [ ] No new coupling is introduced between the collection feature and the environment
      feature (they must remain independent of one another).
- [ ] Automated tests continue to cover write-success and write-failure behavior for both
      collection export and environment export.

## Task Description

**Problem:** `write_export_file()` is implemented twice — once for collections
(`pypost/core/collection_export.py`) and once for environments
(`pypost/core/environment_export.py`) — with the same intent (write a JSON payload to a
user-chosen path) but inconsistent error handling. The environment copy only catches
`OSError`, while the collection copy also catches `TypeError`/`ValueError` (raised by
`json.dumps` for a non-serializable payload). This means the same class of failure is handled
gracefully for one feature and can surface as an unhandled application error for the other.
Beyond the correctness gap, maintaining two copies of the same logic means every future change
(bug fix, behavior tweak, new export feature) has to be remembered and applied twice, which is
exactly how the two copies drifted apart in the first place.

**Goal:** Consolidate the write-to-file behavior so collection export and environment export
rely on one shared, tested implementation, eliminating the duplication and the resulting
inconsistency, while keeping the two features' domain logic independent of each other (no new
requirement for the collection feature to depend on the environment feature, or vice versa).

**Scope (in):**

- Removing the duplication between the two existing `write_export_file()` implementations.
- Making the error-handling behavior (which failures are caught and surfaced to the user)
  consistent between collection export and environment export.
- Preserving current output format, success feedback, and logging behavior for both features.
- Updating/preserving automated test coverage for both features' write-success and
  write-failure paths.

**Scope (out):**

- Any change to *what* is exported (payload shape/content) for collections or environments —
  already-shipped behavior from PYPOST-988/PYPOST-989.
- Any new export feature or export format.
- Any change to the save-dialog UX, filenames, or success/error message wording shown to the
  user.
- Import behavior (unaffected).

## Main Entities and Interactions

- **Collection export** — existing feature (PYPOST-989) that writes a collection's JSON
  payload to a user-chosen file.
- **Environment export** — existing feature (PYPOST-988) that writes an environment (or list
  of environments) JSON payload to a user-chosen file.
- **Export file write** — the shared behavior both features need: given a JSON-serializable
  payload and a destination path, write it to disk and report success or a specific,
  user-facing failure.

Interaction flow (unchanged from the user's point of view): user triggers export (collection
or environment) → chooses a save location → the payload is written to disk → the user sees a
success confirmation or a clear error message if the write failed.

## Non-Functional Requirements

- **Behavioral parity:** file content (indented JSON, UTF-8, trailing newline), success
  logging, and error-surfacing must remain identical to current behavior for both features
  after consolidation.
- **Consistency:** the class of failures treated as a reportable export error must be the same
  for collection export and environment export (closing today's gap).
- **No unwanted coupling:** the collection feature and the environment feature must remain
  independent — neither should end up depending on the other's module as a result of this
  change.
- **Maintainability:** a future third export feature (or a fix to write behavior) should only
  require touching one implementation, not multiple copies.
- **No regression:** existing automated tests for collection export and environment export
  must continue to pass; test coverage for write-success and write-failure must be retained
  for both features.

## Q&A

**Q:** Should this task change what gets caught/reported as an error for environment export
(today only `OSError`; collection export also catches `TypeError`/`ValueError`)?

**A:** Yes — consolidating the write helper should also close this behavioral gap so both
features handle the same class of write failures consistently, per Definition of Done above.
This is a byproduct of using one shared implementation, not a separate feature request.

**Q:** Is it acceptable for the environment feature to import from the collection module (or
vice versa) to share this code?

**A:** No. The existing duplication was intentional specifically to avoid a collection ↔
environment module dependency (per the PYPOST-989 tech-debt note). This requirement still
holds — the two features must stay independent of each other. (How independence is achieved,
e.g. a new shared low-level module, is an architecture decision for Step 2, not covered here.)

**Q:** Does this task change the JSON export file format, filenames, or user-visible
success/error text?

**A:** No — output format and user-facing text are out of scope; only the internal
duplication and the error-handling inconsistency it caused are being addressed.

**Q:** Is a third export feature planned that motivates doing this now?

**A:** Not required — Jira PYPOST-1011 authorizes doing this now regardless of a third caller
appearing, superseding the "if a third caller appears" condition noted in the original
PYPOST-989 tech-debt follow-up.

## Worklog

tokens_used: 21000
role: execution
step: 1
step_name: Requirements
