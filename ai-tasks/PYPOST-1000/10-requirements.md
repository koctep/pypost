# PYPOST-1000: EnvPresenter read_import_file wiring test

## Goals

When a user opens the Environments manager from the main window, Import must
be able to read an environments JSON file using the same storage-backed
parsing path the rest of the app trusts. That connection is a thin hand-off
from the environment presenter into the Environments dialog: without it,
Import either does nothing useful or uses a disconnected parser that can
drift from how environments are loaded and decrypted elsewhere.

Today the hand-off exists in product code, but automated tests do not prove
that the presenter actually gives the dialog a callable that works against
storage. A future change could drop or break that wiring and CI would still
pass, while Import would silently regress for users. This task adds a
focused verification so the wiring cannot be removed or broken unnoticed.

**Implementation language**: Python (verification/testing debt within the
existing Python codebase; no new language or stack is introduced).

## User Stories

- As a developer changing environment import or the Environments manager
  wiring, I want an automated test that fails if the presenter no longer
  passes a working import-file reader into the Environments dialog, so that
  I catch regressions before users hit a broken Import flow.
- As a maintainer of environment import, I want that test to exercise the
  reader against a fake storage manager (not only pure import helpers in
  isolation), so that the storage-bound path the presenter chooses is what
  is locked, not a look-alike stub.
- As a user of Import in the Environments manager, I want confidence that
  the dialog still receives a reader that can turn a valid import file into
  environments, so Import keeps working when I open Manage Environments.

## Definition of Done

- An automated test opens the Environments manager path through
  `EnvPresenter` (with dialog construction intercepted so no real modal
  blocks the suite) and asserts the dialog constructor received a
  `read_import_file` callable.
- Calling that callable with a small valid environments JSON file against
  a `FakeStorageManager` (or a minimal subclass that can deserialize
  plaintext records) returns one or more environment candidates and no
  parse errors — proving the wiring is end-to-end functional, not a
  no-op or unbound stub.
- The test lives with existing EnvPresenter tests and declares an explicit
  pytest timeout per project testing rules.
- No change to user-visible Import behavior is required when product wiring
  is already correct; if the new assertions fail against current code, that
  is treated as a real defect and fixed as part of this task.
- Sibling verification debt (Overwrite × ciphertext reuse, Import button
  click wiring, combinatorial conflict naming) remains out of scope and
  stays on its own tickets.

## Task Description

PYPOST-986 shipped environment Import and wired the Environments dialog’s
`read_import_file` from `EnvPresenter` when opening the manager. Pure import
helpers and list-widget Import orchestration are already tested; the
presenter-level hand-off is not. PYPOST-1000 closes that gap by locking the
presenter → dialog → storage-backed reader path with one focused automated
test using the shared fake storage fixture pattern.

Out of scope:

- Changing Import UX, conflict prompts, or on-disk formats.
- New production APIs or StorageInterface methods.
- Button-click wiring for Import… (tracked separately).
- Overwrite × encryption reuse round-trip coverage (tracked separately).
- Broader EnvPresenter refactors unrelated to this wiring lock.

## Non-Functional Requirements

- The new test must be fast and hermetic: no network, no real modal dialogs,
  no live key service; use temporary files and fakes only.
- Must not make the EnvPresenter suite flaky or unbounded (explicit timeout;
  bounded waits only if any GUI loop is involved — prefer patching dialog
  `exec` / construction so no event-loop wait is needed).
- No new security surface: test uses plaintext fixture JSON only.

## Main Entities

- **Environments manager** — the dialog users open to add/edit/import
  environments.
- **Import file reader** — the callable the dialog uses to turn a chosen
  file path into candidate environments (and optional parse errors).
- **Environment presenter** — owns storage and opens the Environments
  manager, supplying the import file reader bound to that storage.
- **Fake storage manager** — test double standing in for real persistence /
  deserialize so the reader can be exercised without disk encryption setup.

## User scenarios

1. Developer runs the EnvPresenter suite; the new test passes when the
   presenter still injects a storage-backed import reader into the dialog.
2. A regression removes or stubs that injection; the test fails and CI
   blocks merge until wiring is restored.
3. The callable is present but not bound to storage correctly; invoking it
   in the test fails to produce candidates from a valid file, and the test
   fails.

## Q&A

| Question | Answer |
| --- | --- |
| Why is this a business/quality goal, not “just more coverage”? | Import is user-facing; the presenter is the only place core import is bound to concrete storage for the Environments manager. Without a lock, that single integration seam can break silently. |
| Must product behavior change? | Only if the new assertions reveal a defect. The expected happy path is test-only when current wiring is already correct. |
| Why FakeStorageManager specifically? | Named in the PYPOST-986 follow-up so the test uses the shared fake (or a thin subclass) rather than inventing a one-off double that never exercises `deserialize_environment_records`. |
