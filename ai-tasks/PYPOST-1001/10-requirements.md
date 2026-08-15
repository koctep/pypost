# PYPOST-1001: Import… button wiring lock

## Goals

Users start environment Import from the Manage Environments screen by clicking
the **Import…** button. That click is the real user path: if the button is
visible but no longer starts Import, people cannot bring environments in from
a file even though the import action itself still works when called by tests.

Today, automated tests exercise Import by invoking the import action directly.
None of them simulate a user click on **Import…**. A future change can leave
the button on screen while disconnecting it from Import, and CI would still
pass.

This task locks that click: a simulated press of **Import…** must start the
same import action the rest of the suite already covers. A broken click
handler must fail CI.

**Implementation language**: Python (verification/testing debt within the
existing Python codebase; no new language or stack is introduced).

## User Stories

- As a user of Manage Environments, I want clicking **Import…** to start
  Import (file pick and the rest of the flow), so the control I see is the
  control that actually works.
- As a developer changing the Environments manager or Import wiring, I want
  an automated test that fails if **Import…** no longer starts Import, so a
  dead button cannot merge.
- As a maintainer of environment Import, I want that lock to complement the
  existing direct-call Import tests rather than re-prove conflict handling,
  invalid files, or parse behavior, so the suite stays focused.

## Definition of Done

- An automated test finds the **Import…** control on the Environments manager
  list (the control identified as `ENV_IMPORT_BUTTON`) and simulates a real
  user click on it, in the same style other button-driven flows in this
  project already lock.
- That click must start the import action (`import_environments`). If the
  button is missing, disabled, or no longer wired to Import, the test fails.
- The test does **not** re-assert Import’s conflict, invalid-file, or parse
  logic. Existing direct-call tests remain the coverage for those behaviors.
- The test lives with the existing Environments manager list-widget Import
  tests and declares an explicit pytest timeout per project testing rules.
- No change to user-visible Import behavior is required when the button is
  already wired correctly; if the new assertion fails against current code,
  that is a real defect and is fixed as part of this task.
- Sibling verification debt (presenter import-file reader, Overwrite ×
  Hidden protection round-trip, combinatorial conflict naming) remains out
  of scope and stays on its own tickets.

## Task Description

**Problem:** PYPOST-986 shipped **Import…** on the Manage Environments list
and wired it to the import action. Tests call that action directly. They do
not prove that a user click on the button starts Import. The button can be
disconnected while every current test still passes.

**Goal:** Add a focused automated lock so a click on **Import…** must start
Import. CI then fails if the click handler is broken, missing, or pointed
somewhere else.

**Scope (in):**

- One click-level verification: **Import…** (`ENV_IMPORT_BUTTON`) starts the
  import action.
- Use of the project’s existing simulated-click approach for button-driven
  UI (a real click, not a direct method call).
- Preservation of existing direct-call Import coverage.

**Scope (out):**

- Changing Import UX, file-picker copy, conflict prompts, or on-disk formats.
- Re-testing import planning, name conflicts, Hidden protection, or invalid
  files.
- Presenter → dialog import-file reader wiring (PYPOST-1000).
- Overwrite × Hidden protection round-trip (PYPOST-999).
- Combinatorial conflict naming / copy-name sequencing (PYPOST-1002).
- Export button click coverage, collection import, or new production APIs.

**Constraints and assumptions:**

- Programming language: Python (existing PyPost desktop app).
- Source: follow-up 3 in `ai-tasks/PYPOST-986/60-tech-debt.md`, ticketed as
  [PYPOST-1001](https://pypost.atlassian.net/browse/PYPOST-1001).
  Parent: [PYPOST-986](https://pypost.atlassian.net/browse/PYPOST-986).
- Product wiring is believed correct; this is verification debt unless a new
  assertion reveals a defect.
- File-picker and import side effects may be stubbed so the test proves
  **wiring**, not a full import of a real file.
- Approval for Step 1 artifacts is treated as granted under
  sprint-task-runner autonomy.

## Non-Functional Requirements

- The new test must be fast and hermetic: no network, no live key service,
  no real disk import of production data.
- Must not make the Environments manager suite flaky or unbounded (explicit
  timeout; no unbounded GUI waits).
- Security: no new surface; the test may stub the file pick so it never
  needs real secret-bearing files.
- Focused: one click→Import wiring scenario is enough.

## Main Entities

- **Import… button** — the control users click on the Manage Environments
  list to start Import (`ENV_IMPORT_BUTTON`).
- **Import action** — the Environments manager behavior that runs after a
  successful click (file pick and import of environments).
- **Environments manager list** — the screen that already hosts Add / Import
  / other environment actions.
- **Direct-call Import tests** — existing coverage that invokes the import
  action without clicking the button; this ticket does not replace them.

## User scenarios

1. A developer runs the Environments manager Import tests. The new test
   passes when clicking **Import…** still starts the import action.
2. A regression leaves **Import…** on screen but disconnects it from Import.
   The test fails and CI blocks merge until the click starts Import again.
3. The button is renamed, hidden, or no longer findable as the Import
   control. The test fails because the user-visible click path is gone.

## Q&A

**Q:** Why is this a business/quality goal, not "just more coverage"?

**A:** Users only start Import by clicking **Import…**. Direct-call tests
cannot see a dead button. Without this lock, Import can look present and
still do nothing, and CI would not catch it.

**Q:** Must product behavior change?

**A:** Only if the new assertion reveals a defect. The expected happy path is
test-only when **Import…** already starts Import.

**Q:** Why not treat the existing `import_environments()` tests as enough?

**A:** Those tests skip the click. They prove Import works when called; they
do not prove the button calls it.

**Q:** Does this ticket re-test conflict handling or invalid files?

**A:** No. Those remain on the existing direct-call tests. This ticket only
locks click → import action.

**Q:** Why name `ENV_IMPORT_BUTTON` and `import_environments` here?

**A:** They are the product names in the parent debt item and this Jira
issue. They identify *which* control and *which* action must be connected,
not how to implement the test harness.

**Q:** How does this relate to PYPOST-999, PYPOST-1000, and PYPOST-1002?

**A:** PYPOST-1000 locks presenter → dialog reader wiring. PYPOST-999 locks
Overwrite × Hidden protection on save. PYPOST-1002 locks extra conflict
naming cases. This ticket only locks the **Import…** click.

**Q:** Is a full end-to-end import of a real file required on click?

**A:** No. The click must start the import action. File pick and import
results may be stubbed so the test stays a wiring lock.
