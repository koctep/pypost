# PYPOST-1005: Responsive collection import with progress

## Programming language

Python

## Goals

PyPost already lets users import collections from a file (PYPOST-987). For a large
import file — many collections or many requests — preparing that file for import can
lock up the main window with no indication that work is underway. Users cannot tell
whether the app is busy or hung, and they cannot keep using the rest of the UI while
import preparation runs.

At startup, loading collections already keeps the window usable and gives the user a
sense of progress while data is brought in. Collection import should feel the same:
the window stays responsive, and the user can see that import preparation is making
progress.

The business goal is to stop large collection imports from freezing the desktop
experience, without changing what an import means (conflict choices, success/failure
feedback, or what ends up in the collections tree).

## User Stories

- As a **user**, I want the PyPost window to stay usable while a large collection
  file is prepared for import, so the app does not appear frozen.
- As a **user**, I want visible progress while import preparation runs, similar to
  how collections load when the app starts, so I know the action is still working.
- As a **user**, I want import results after preparation finishes to match today —
  conflict prompts when needed, then a clear summary and an updated collections tree —
  so responsiveness does not change import outcomes.
- As a **user**, I want an invalid or unreadable file to still produce a clear error
  and leave my existing collections unchanged, so a long wait does not hide failure.
- As a **maintainer**, I want automated coverage for a large import file scenario, so
  a freeze or missing progress does not return unnoticed.

## Definition of Done

- [ ] While a large collection import file is prepared, the main window remains usable
      (no prolonged freeze that makes the app look hung).
- [ ] The user sees progress feedback during that preparation, consistent in spirit with
      collection loading at application startup.
- [ ] Existing import behavior for valid files, name conflicts, invalid files, success
      summary, and sidebar refresh is preserved (same outcomes as PYPOST-987).
- [ ] Automated tests include a large-file import scenario that exercises the
      responsiveness / progress expectation above.
- [ ] User-facing collection import documentation notes that large imports stay
      responsive with progress, if the current user docs omit that.

## Task Description

**Problem:** Collection import preparation for a large file can freeze the PyPost
window with no progress indication. Users cannot continue interacting with the app and
cannot tell that import work is still running. Startup collection loading already
avoids that experience; import does not.

**Goal:** Make collection import preparation stay responsive and show progress for
large files, matching the startup collection-loading experience from the user's point
of view, without changing import semantics.

### Scope (in)

- Responsive UI during preparation of a collection import from a user-chosen file.
- Visible progress feedback during that preparation, aligned with how users already
  experience collection loading at startup.
- Preservation of current import outcomes: conflict decisions, success summary,
  errors for bad files, and immediate tree update after a successful import.
- Automated verification for a large import file scenario.
- Brief user-doc update only if needed to describe responsive import with progress.

### Scope (out)

- Changing collection import/export file format or third-party converters.
- Changing conflict policy, overwrite/keep-both/skip semantics, or identifier rules.
- Making multi-collection import transactional across files (tracked separately as
  PYPOST-1004).
- Fixing rename-summary undercounting for repeated duplicate names (PYPOST-1003).
- Broader performance work unrelated to collection import preparation.
- Redesigning the collections sidebar or inventing a new import workflow.

### Constraints and assumptions

- Programming language: Python (existing PyPost desktop app).
- Source debt: [PYPOST-987](https://pypost.atlassian.net/browse/PYPOST-987) tech-debt
  item #3 → [PYPOST-1005](https://pypost.atlassian.net/browse/PYPOST-1005).
- "Large file" means an import large enough that today's synchronous preparation would
  noticeably freeze the window (hundreds of collections or thousands of requests, or
  multi-megabyte content), not a tiny single-collection share.
- Progress feedback must be understandable to an end user; it need not invent a new
  product metaphor beyond what users already see when collections load at startup.
- Import still runs only when the user chooses **Import Collection…** and picks a
  file; this task does not add automatic or background imports.
- Approval for Step 1 artifacts is treated as granted under sprint-task-runner
  autonomy.

## Main entities and interactions

| Entity | Attributes | Role |
| --- | --- | --- |
| User | Import intent; conflict choices | Starts import; needs responsive UI |
| Collection import file | Collections; requests; size | User-chosen file to import |
| Import preparation | Progress state; planned import | Turns file into planned import |
| Progress feedback | Visibility; startup-like cue | Shows preparation is still running |
| Conflict decision | Name; overwrite / keep both / skip | Unchanged per-name policy |
| Import result | Summary or error; tree refresh | Outcome after preparation finishes |
| Startup collection load | Responsiveness; progress cue | Reference UX users already know |

Interaction overview:

1. User chooses **Import Collection…** and selects a file.
2. While the file is prepared, the window stays usable and progress is visible.
3. If names conflict, the user decides as today; preparation/progress does not skip
   those decisions.
4. On completion, the user sees the same success summary or error as today, and the
   tree reflects a successful import without a restart.

## Q&A

**Q:** Why is this needed if typical shared collection files are small?

**A:** Typical files are small, but a large backup or team bundle can still freeze the
window with no feedback. Startup already protects that case for loading collections;
import should not be the exception that freezes the UI.

**Q:** Does this change what gets imported or how conflicts work?

**A:** No. Outcomes stay as delivered in PYPOST-987. This task is about staying
responsive and showing progress during preparation.

**Q:** What does "matching startup collection loading" mean for the user?

**A:** The window remains usable and the user can see that work is in progress, the
same class of experience they already get when collections load at app start — not a
new unrelated progress metaphor, and not a silent hang.

**Q:** Is a large-file test mandatory?

**A:** Yes. The debt item and this ticket require automated coverage so a large import
cannot regress back into a freeze without progress.

**Q:** Are environment import or export in scope?

**A:** No. This task is limited to collection import preparation responsiveness and
progress.
