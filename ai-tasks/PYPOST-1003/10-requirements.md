# PYPOST-1003: Fix import rename summary undercount for duplicate names

## Goals

When a user imports a file (a collection import or an environment import)
that contains several entries sharing the same name, every duplicate is
correctly renamed and added — nothing is lost, skipped, or corrupted. However,
the result summary shown to the user after the import undercounts how many
entries were actually renamed once three or more entries share a name: it
reports fewer renames than actually happened, and the list of renamed items in
the summary is incomplete.

This erodes user trust in the import feature. A user who imports a file with
several duplicate-named collections or environments and sees "Renamed: 1"
when in fact several were renamed has no reliable way to tell, from the
summary alone, how many of their items were touched and what they were
renamed to. They may believe the import partially failed or lost data, or
they may miss that an item was renamed at all, when in reality the import
completed correctly and only the on-screen report is wrong.

This task corrects the reported count and the listed rename pairs in the
import result summary so that it always matches what was actually imported,
for both collection import and environment import. It does not change what
gets imported, renamed, or saved — only what the user is told about it.

**Implementation language**: Python (this is a bug fix within the existing
Python codebase; no new language or stack is introduced).

## User Stories

- As a user importing a collection file that contains several collections
  sharing the same name, I want the import result summary to report the
  correct number of renamed collections and list every renamed collection, so
  that I can verify the import happened as expected.
- As a user importing an environment file that contains several environments
  sharing the same name, I want the import result summary to report the
  correct number of renamed environments and list every renamed environment,
  so that I can verify the import happened as expected.
- As a user reviewing an import result summary, I want the reported "Renamed"
  count to always match the number of renamed entries actually visible in my
  collections/environments afterward, so that I can trust the summary without
  needing to manually cross-check the tree.

## Definition of Done

- Importing a file containing 3 collections named "API" (or any name) reports
  "Renamed: 2" in the collection import result summary (the first keeps its
  original name; the other two are renamed), and the summary lists both
  renamed collections with their new names.
- Importing a file containing 3 environments named "API" (or any name)
  reports "Renamed: 2" in the environment import result summary, and the
  summary lists both renamed environments with their new names.
- The same behavior holds for any number of duplicates greater than 2 (e.g.,
  4 duplicates report "Renamed: 3" and list all 3), for both collection
  import and environment import.
- The reported "Renamed" count and the listed rename entries always match the
  actual set of entries that were renamed and imported — no undercounting,
  no dropped entries, regardless of how many entries share a name.
- Existing import behavior is unchanged in every other respect: which
  entries get imported, how conflicts are resolved (skip, overwrite, keep
  both, in-file duplicate renaming), and what gets saved to disk. Only the
  reported summary count/list is corrected.
- Behavior for imports with 0, 1, or 2 duplicate names (already reported
  correctly today) continues to work as before — no regression.
- A regression test exists for both collection import and environment import
  confirming the corrected count and listing for 3+ duplicate names.

## Task Description

Collection import and environment import each produce a result summary shown
to the user (in a dialog) after the import completes, including a count and
list of entries that were renamed due to a name conflict with an existing
entry or with another entry in the same import file. Today, when an imported
file contains three or more entries that all share the same name, the
underlying import logic correctly renames and adds every duplicate (e.g.,
"API", "Copy of API", "Copy of API (2)"), but the result summary only reports
and lists the last rename pair for that name instead of all of them — so the
displayed "Renamed" count is lower than the true number of renames, and the
list omits earlier renames for that name.

This is a reporting-only defect: the actual import outcome (what is renamed,
added, and saved) is already correct. The fix must correct the summary's
count and list so they accurately reflect every rename that occurred, for
both collection import and environment import, without changing any other
import behavior.

Out of scope:
- Any change to which entries are imported, skipped, overwritten, or
  conflict-resolved.
- Any change to the naming scheme used when generating a new name for a
  duplicate (e.g., "Copy of X", "Copy of X (2)").
- Any new user-facing feature, dialog, or workflow step.
- The other follow-up items noted alongside this one in the PYPOST-987
  technical debt report (import atomicity, moving import off the UI thread,
  additional test coverage gaps, mypy baseline keying) — those are tracked
  separately and are not part of this task.

## Non-Functional Requirements

This is a narrow reporting/summary-accuracy bug fix with no new UI, no new
data volume, and no change to what is imported or saved. There are no special
performance, security, or scalability requirements beyond correctness of the
reported summary: the fix must not perceptibly slow down or otherwise
degrade the import operation, must not introduce any new security exposure
(no new inputs, permissions, or data handling are involved), and must
continue to work correctly regardless of the number of duplicate-named
entries in an import file.

## Main Entities

- **Collection** — a saved API collection a user can import; identified by
  its name, which may collide with an existing collection or with another
  collection in the same import file.
- **Environment** — a saved set of environment variables a user can import;
  identified by its name, which may collide with an existing environment or
  with another environment in the same import file, in the same way a
  Collection's name can.
- **Import Result Summary** — the outcome shown to the user after a
  collection or environment import completes, including:
  - **Renamed count** — how many entries in the import were renamed because
    their original name conflicted with an existing entry or another entry
    in the same file.
  - **Renamed items list** — the list of entries that were renamed,
    identifying each renamed entry and the new name it was given.

## Q&A

- **Q: Is this a new bug, or a known issue from a prior task?**
  A: It is a known issue identified during PYPOST-987 (collection import) and
  also present in the sibling environment import feature from PYPOST-986,
  documented as follow-up item 1 in
  `ai-tasks/PYPOST-987/60-tech-debt.md`. This task is that follow-up.

- **Q: Does this change what happens to the user's data during import?**
  A: No. Every duplicate-named entry is already renamed and imported
  correctly today; only the on-screen summary undercounts and under-lists
  the renames. This task fixes the reporting, not the import outcome.

- **Q: Does this affect both collection import and environment import, or
  just one?**
  A: Both. The same summary undercount exists in both features and must be
  fixed in both, consistently, since they share the same behavior and are
  expected to stay in sync.

- **Q: What counts as "correct" for the Definition of Done examples?**
  A: For N entries sharing one name, the first entry keeps the original name
  (no rename) and the remaining N-1 entries are renamed — so the summary
  should report N-1 renames for that name and list all N-1 renamed entries
  with their resulting names.
