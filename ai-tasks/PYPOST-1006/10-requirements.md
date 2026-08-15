# PYPOST-1006: Close collection import combinatorial/caplog test gaps

## Programming language

Python (verification/testing debt within the existing Python codebase; no new
language or stack is introduced).

## Goals

Collection import (PYPOST-987) already shows an error when a file cannot be
used, already offers "apply to all" for name conflicts, and already creates
disambiguated copy names when the user keeps both collections. Automated tests
prove those outcomes for the common cases: an invalid file leaves collections
untouched, two conflicting names prompt only once when "apply to all" is
chosen, and a first copy is named "Copy of …" (with a second numbered copy
"(2)" reached from in-file duplicates).

Three narrow proofs are still missing:

1. The shared invalid-file log event `collection_import_file_invalid` is not
   asserted via `caplog` for either invalid reason. The hard-parse-failure
   branch and the zero-usable-collections branch are covered only by the
   user-visible error and unchanged app state. Completed-import and
   save-failed events *are* locked through `caplog`. The two invalid branches
   share one event name and differ only by `reason`, so a logging regression
   that collapses or drops a reason would not fail CI.

2. "Apply to all" is only proven for exactly two conflicting names. A loop
   that stops after the second name, or that prompts again after the second,
   would not be caught.

3. Copy-name generation is not exercised past "(2)" from the collection
   import side. The helper `generate_import_copy_name` is shared with
   environment import; if later numbered copies (`(3)` and beyond) stopped
   being unique, collection import would not have a lock.

This task closes those three gaps so maintainers can trust the logs, the
apply-to-all convenience, and copy uniqueness without changing what users
see or what import does.

## User Stories

- As a **maintainer** of collection import, I want both invalid-file reasons
  (unreadable/unparseable file, and a readable file with no usable
  collections) asserted through `caplog` on `collection_import_file_invalid`,
  so a logging regression that drops or conflates those reasons fails CI the
  same way completed-import and save-failed already do.
- As a **maintainer**, I want "apply to all remaining conflicts" proven with
  three or more distinct conflicting collection names, so a prompt-loop
  regression that only appears after two names is caught.
- As a **maintainer**, I want copy-name generation from collection import
  exercised past the second numbered copy, so uniqueness continues when
  "Copy of <name>" and "Copy of <name> (2)" are already taken.
- As a **user** of Import collection, I want no change to the import
  workflow, conflict choices, copy names, or error messages — only stronger
  automated proof that those behaviors stay correct.

## Definition of Done

- [ ] When collection import rejects a file because it cannot be parsed, the
      `collection_import_file_invalid` log event is asserted via `caplog`,
      with a reason that identifies the parse failure (distinct from the
      zero-usable-collections reason).
- [ ] When collection import rejects a file because it yields no usable
      collections, the same event name is asserted via `caplog`, with
      `reason` identifying that there were no valid collections.
- [ ] Existing invalid-file user outcomes remain proven: an error is shown
      and existing collections are left untouched for both reasons.
- [ ] An import with three or more distinct names that each conflict with an
      existing collection, where the user chooses a conflict decision and
      "apply to all", prompts only once and applies that decision to every
      remaining conflicting name.
- [ ] Copy-name generation used by collection import is exercised past
      `(2)`: when earlier copy names for the same original name are already
      taken, the next copy is still unique (at least `(3)`).
- [ ] Existing two-conflict "apply to all" coverage and existing copy-name
      coverage through `(2)` remain green (no regression).
- [ ] No user-visible import behavior change is required when current
      product code already matches these proofs. If a new assertion fails
      against current code, that is treated as a real defect and fixed as
      part of this task.
- [ ] Sibling follow-ups from PYPOST-987 (rename-summary undercount,
      import atomicity, off-thread parse, mypy baseline keying) stay out of
      scope.

## Task Description

**Problem:** PYPOST-987 shipped collection import with solid behavioral
coverage, but three small verification gaps remain (Follow-up #4 in
`ai-tasks/PYPOST-987/60-tech-debt.md`):

- Invalid-file logging is not locked the way completed and save-failed
  logging already is.
- "Apply to all" is only combinatorially proven for two conflicts.
- Numbered copy names past `(2)` are not exercised from the collection
  caller.

**Goal:** Close those three test gaps so regressions in invalid-file
observability, apply-to-all sequencing, and later copy uniqueness fail CI.

### Scope (in)

- Automated proof that both invalid-file reasons emit
  `collection_import_file_invalid` via `caplog`, distinguished by `reason`.
- Automated proof that three or more conflicting collection names go
  through "apply to all" with a single prompt.
- Automated proof that collection-side copy-name generation continues past
  `(2)`.
- Preservation of existing invalid-file, apply-to-all, and copy-name
  behavioral coverage.

### Scope (out)

- Changing import UX, conflict policy, copy-name scheme, or file format.
- New user-facing features or dialogs.
- Environment-import combinatorial gaps (tracked separately from PYPOST-986
  as PYPOST-1002); this ticket is the collection-side lock.
- Other PYPOST-987 follow-ups: rename-summary undercount (PYPOST-1003),
  import atomicity (PYPOST-1004), off-thread parse (PYPOST-1005), mypy
  baseline keying (PYPOST-1007).
- Very-large-file import tests (recorded as a separate missing-test note in
  PYPOST-987, not this follow-up).

### Constraints and assumptions

- Product behavior is already believed correct; this is verification debt
  unless a new assertion reveals a defect.
- The two invalid branches share one event name and differ only by
  `reason`; both reasons must be locked, not only the event name.
- "Apply to all" applies the first conflict decision to every remaining
  conflicting name without further prompts.
- Copy names follow the existing scheme: `Copy of <name>`, then
  `Copy of <name> (2)`, then `(3)`, and so on until unique.
- `generate_import_copy_name` is shared with environment import; this task
  only requires the collection import caller to exercise past `(2)`.

## Main entities and interactions

- **Collection** — a named group of saved requests. Name uniqueness is what
  the user sees and what conflict prompts are about.
- **Collection import** — the user action that loads collections from a
  file into the sidebar.
- **Invalid import file** — a chosen file that either cannot be parsed, or
  parses but yields no usable collections. Both cases must leave existing
  collections unchanged and tell the user; both must also be distinguishable
  in logs.
- **Name conflict** — an imported collection whose name already exists
  locally. The user chooses overwrite, keep both, or skip, optionally
  applying that choice to all remaining conflicts.
- **Copy name** — the disambiguated name used when keeping both (or when
  the file itself contains duplicate names): `Copy of <name>`, then
  numbered suffixes starting at `(2)`.
- **Invalid-file log event** — `collection_import_file_invalid`, already
  emitted for both invalid reasons; this task requires asserting it, with
  `reason`, the same way completed-import and save-failed events are
  already asserted.

Interaction: a maintainer runs the collection-import tests → the suite
fails if either invalid reason is missing from logs, if apply-to-all
prompts more than once (or skips later names) for three-plus conflicts, or
if a later numbered copy is not unique when earlier copies are taken.

## Non-functional requirements

- Proofs must be hermetic and bounded (explicit test timeout per project
  testing rules; no network; no unbounded UI waits).
- No new security surface: tests use the same local/fake import inputs the
  existing collection-import suite already uses.
- No perceptible change to import performance for users (test-only unless a
  defect is found and fixed).
- Consistency: invalid-file log assertions should match the style already
  used for `collection_import_completed` and `collection_import_save_failed`.

## Q&A

**Q:** Why is this a business/quality goal, not "just more coverage"?

**A:** Operators and maintainers already rely on `caplog` locks for
completed and save-failed import events. Invalid-file is the remaining
user-visible failure that is logged but not asserted. Apply-to-all and
later copy numbers are user-facing conveniences whose bugs would look like
"import asked me again" or "two copies share a name" — easy to miss with
only a two-name or `(2)` example.

**Q:** Must product behavior change?

**A:** No, unless a new assertion fails against current code. The expected
happy path is test-only.

**Q:** Why both invalid reasons, not just the event name?

**A:** The two branches share `collection_import_file_invalid` and differ
only by `reason`. Asserting the event name alone would still allow one
reason to be dropped or swapped.

**Q:** Why three or more conflicts, not another two-conflict case?

**A:** Two is already covered. The gap is combinatorial: a loop that works
for two names can still fail at the third.

**Q:** Why "from the collection side" for copy names past `(2)`?

**A:** The helper is shared with environment import. Environment tests
cover the free name and `(2)`. Collection import already reaches `(2)` via
in-file duplicates, but not past it. This ticket locks the collection
caller so that side is not assumed covered by the environment tests.

**Q:** Is the environment-import sibling (PYPOST-1002) in scope?

**A:** No. This ticket is the collection-import follow-up from PYPOST-987.

**Q:** Source of this debt?

**A:** Follow-up #4 in `ai-tasks/PYPOST-987/60-tech-debt.md`, ticketed as
[PYPOST-1006](https://pypost.atlassian.net/browse/PYPOST-1006). Parent:
[PYPOST-987](https://pypost.atlassian.net/browse/PYPOST-987).
