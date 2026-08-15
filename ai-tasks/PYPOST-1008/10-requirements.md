# PYPOST-1008: EnvPresenter export wiring test

## Goals

When a user opens the Environments manager from the main window, Export must
turn selected or all environments into a file using the same storage-backed
serialization the rest of the app trusts. That connection is a thin hand-off
from the environment presenter into the Environments dialog: without it,
Export either cannot write a useful file or uses a disconnected serializer
that can drift from how environments are stored (and later imported).

Today the hand-off exists in product code, but automated tests do not lock
that the presenter actually gives the dialog a callable that works against
storage. A future change could drop or break that wiring and CI would still
pass, while Export would silently regress for users. This task adds a
focused verification so the wiring cannot be removed or broken unnoticed.

Related coverage may already exist beside EnvPresenter tests (including a
check that a storage serializer is passed when the manager opens). Step 1
still records the intended quality lock. Later steps decide whether that
coverage already meets it or a stronger proof is still required.

**Implementation language**: Python (verification/testing debt within the
existing Python codebase; no new language or stack is introduced).

## User Stories

- As a developer changing environment export or the Environments manager
  wiring, I want an automated test that fails if the presenter no longer
  passes a working export serializer into the Environments dialog, so that
  I catch regressions before users hit a broken Export flow.
- As a maintainer of environment export, I want that test to exercise the
  serializer against a fake storage manager (not only a look-alike stub),
  so that the storage-bound path the presenter chooses is what is locked.
- As a user of Export in the Environments manager, I want confidence that
  the dialog still receives a serializer that can turn environments into
  export records, so Export keeps producing files Import can read.

## Definition of Done

- An automated test opens the Environments manager path through
  `EnvPresenter` (with dialog construction intercepted so no real modal
  blocks the suite) and asserts the dialog constructor received a
  `serialize_export_records` callable.
- Calling that callable with one or more environments against a
  `FakeStorageManager` (or a minimal subclass that can serialize plaintext
  records) returns one or more export records — proving the wiring is
  end-to-end functional, not a no-op or unbound stub.
- The test lives with existing EnvPresenter tests and declares an explicit
  pytest timeout per project testing rules.
- No change to user-visible Export behavior is required when product wiring
  is already correct; if the new assertions fail against current code, that
  is treated as a real defect and fixed as part of this task.
- If an existing EnvPresenter test already meets this lock (including use
  of `FakeStorageManager` and a working serializer that reaches the dialog),
  later steps may conclude already-done without adding a duplicate test.
- Sibling verification debt (encrypted export round-trip, shared
  single-vs-list JSON helper, Export button click) remains out of scope and
  stays on its own tickets.

## Task Description

PYPOST-988 shipped environment Export and wired the Environments dialog’s
`serialize_export_records` from `EnvPresenter` when opening the manager.
Pure export helpers and list-widget Export orchestration are already
tested; the presenter-level hand-off was recorded as a gap. PYPOST-1008
closes that gap by locking the presenter → dialog → storage-backed
serializer path with one focused automated test using the shared fake
storage fixture pattern.

This is the export-side counterpart of the PYPOST-1000 import-reader
wiring lock: same seam, opposite direction.

### Scope (in)

- Automated proof that opening the Environments manager from the presenter
  supplies the dialog with a working, storage-backed export serializer.
- Use of `FakeStorageManager` (or a thin subclass) so the callable is
  exercised against the shared fake, not an unrelated double.
- Preservation of existing export and EnvPresenter coverage.

### Scope (out)

- Changing Export UX, Hidden-secrets confirmation, file format, or
  single-vs-list JSON root shaping.
- New production APIs or StorageInterface methods.
- Button-click wiring for Export… (method-level coverage already exists;
  click-level coverage is separate debt).
- Encrypted-at-rest export → import round-trip (tracked as PYPOST-1009).
- Extracting a shared single-vs-list JSON helper (tracked as PYPOST-1010).
- Broader EnvPresenter refactors unrelated to this wiring lock.
- Import-reader wiring (already locked by PYPOST-1000).

### Constraints and assumptions

- Product behavior is already believed correct; this is verification debt
  unless a new assertion reveals a defect.
- Programming language: Python (existing PyPost desktop app).
- Source: follow-up #1 in `ai-tasks/PYPOST-988/60-tech-debt.md`, ticketed
  as [PYPOST-1008](https://pypost.atlassian.net/browse/PYPOST-1008).
  Parent: [PYPOST-988](https://pypost.atlassian.net/browse/PYPOST-988).
- Approval for Step 1 artifacts is treated as granted under
  sprint-task-runner autonomy.

## Non-Functional Requirements

- The test must be fast and hermetic: no network, no real modal dialogs,
  no live key service; use fakes only.
- Must not make the EnvPresenter suite flaky or unbounded (explicit
  timeout; bounded waits only if any GUI loop is involved — prefer
  intercepting dialog construction so no event-loop wait is needed).
- No new security surface: test uses plaintext environments only (encrypted
  round-trip is PYPOST-1009).

## Main Entities

- **Environments manager** — the dialog users open to add/edit/export
  environments.
- **Export serializer** — the callable the dialog uses to turn environments
  into records written to an export file.
- **Environment presenter** — owns storage and opens the Environments
  manager, supplying the export serializer bound to that storage.
- **Fake storage manager** — test double standing in for real persistence /
  serialize so the serializer can be exercised without disk encryption
  setup.

## User scenarios

1. Developer runs the EnvPresenter suite; the test passes when the
   presenter still injects a storage-backed export serializer into the
   dialog.
2. A regression removes or stubs that injection; the test fails and CI
   blocks merge until wiring is restored.
3. The callable is present but not bound to storage correctly; invoking it
   in the test fails to produce records from valid environments, and the
   test fails.

## Q&A

**Q:** Why is this a business/quality goal, not "just more coverage"?

**A:** Export is user-facing. The presenter is the only place core export is
bound to concrete storage for the Environments manager. Without a lock,
that single integration seam can break silently and files would no longer
round-trip with Import.

**Q:** Must product behavior change?

**A:** Only if the new assertions reveal a defect. The expected happy path
is test-only when current wiring is already correct.

**Q:** Why FakeStorageManager specifically?

**A:** Named in the PYPOST-988 follow-up so the test uses the shared fake
(or a thin subclass) rather than inventing a one-off double that never
exercises storage serialization.

**Q:** Does related existing coverage already close this ticket?

**A:** A related EnvPresenter test may already assert that a storage
serializer is passed when the manager opens. This document states the
intended lock: a working serializer reaches the dialog, proven with
FakeStorageManager. Later steps compare that coverage to the lock and may
conclude already-done.

**Q:** How does this relate to PYPOST-1000?

**A:** PYPOST-1000 locked the import-reader hand-off on the same presenter
to dialog seam. This ticket locks the export-serializer hand-off.

**Q:** Are encrypted export files in scope?

**A:** No. Encrypted-at-rest export to import is PYPOST-1009.
