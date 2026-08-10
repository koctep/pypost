# PYPOST-1004: Atomic multi-collection import or recovery on mid-write save failure

## Goals

When a user imports a file that contains several collections, PyPost updates
what they see in the app and then writes each changed collection to disk.
Today, if a write fails partway through that set (for example disk full or
permission denied), the import is reported as unsuccessful and the failure is
logged — but the collections tree and in-app state can already show the imported
or updated collections even though some of them never made it to disk. There is
no rollback of that in-app view and no guided recovery. Until something else
saves successfully, what the user sees and what will survive a restart can
disagree.

That mismatch undermines trust in collection import: the user may believe their
imported collections are durable when they are not, or they may restart the app
and lose changes they thought were already applied, with no clear action offered
at failure time to restore a consistent picture.

This task closes that gap for multi-collection import. After a mid-write save
failure, the user must not be left with an unexplained or unrecoverable
divergence between what the app shows and what is durable on disk. The product
outcome is consistency the user can rely on — either the import leaves memory
and disk aligned when it finishes (success or failure), or the failure path
gives the user an explicit, actionable way to restore that alignment.

**Implementation language**: Python (this is hardening within the existing
Python codebase; no new language or stack is introduced).

## User Stories

- As a user importing a file with several collections, I want a mid-write save
  failure not to leave my sidebar looking “imported” while some of those
  collections are missing from durable storage, so that I do not trust data that
  will disappear on restart.
- As a user who hits a save failure during multi-collection import, I want a
  clear unsuccessful outcome that matches the true durable state (or an explicit
  recovery step that restores consistency), so that I know what survived and what
  to do next.
- As a user continuing to work after a failed multi-collection import, I want
  the collections I see and the collections that will load after a restart to
  agree (either because the failed import did not leave them out of sync, or
  because I completed the offered recovery), so that I am not surprised by lost
  or phantom collections later.
- As a user whose import fully succeeds, I want the happy path to behave as it
  does today — collections appear, persist, and are summarized correctly — so
  that fixing the failure path does not change successful imports.

## Definition of Done

- When a multi-collection import fails while persisting one or more collections
  mid-write, the user is not left with a lasting unexplained mismatch between
  the collections shown in the app and the collections that exist on disk.
- The product satisfies that outcome in one of these equally acceptable ways
  (choice is left to architecture; requirements only care about the result):
  - The import behaves as a consistent unit for durability: on persistence
    failure, durable storage and the user’s visible collection set remain
    aligned with a documented prior-consistent state; or
  - The failure path offers an explicit recovery action that restores alignment
    between what the user sees and what is on disk, and the user can complete
    that recovery without hunting through logs or restarting blindly.
- If the chosen approach is recovery and the user declines or dismisses that
  recovery: they must still leave the failure path knowing the import did not
  fully succeed and that visible and durable collections may disagree until they
  take a later action that restores agreement (for example completing recovery
  when offered again, or otherwise bringing the app and disk back in sync). The
  decline/dismiss path must not present the import as successfully finished, and
  must not imply that the sidebar alone is a durable save. Exact presentation is
  left to design; the business end state is an honest unfinished/inconsistent
  outcome the user can recognize and act on later — not a silent “everything is
  fine.”
- The unsuccessful import result remains user-visible and truthful about the
  failure (including which collections could not be saved, when that information
  is available today).
- A successful multi-collection import (every intended write completes) continues
  to show the imported/updated collections in the tree, persist them, and
  present a successful result summary — no regression on the happy path.
- Existing conflict handling (skip, overwrite, keep both), invalid-file handling,
  and parse-error reporting remain unchanged in intent.
- Automated tests cover at least: a multi-collection import where a mid-write
  save failure occurs, asserting that after the import (and any offered recovery
  the design requires) the visible collection set and durable storage agree for
  the collections involved; plus a successful multi-collection import regression.
- Developer-facing documentation for collection import describes the mid-write
  failure behavior and, if recovery is part of the chosen approach, how the user
  recovers.

## Task Description

**Problem:** Multi-collection import applies the planned collection set in the
running app and then persists each changed collection. If persistence fails for
some collections after the in-app set has already changed, the user sees an
unsuccessful result, but the tree can still show collections that were never
written. There is no rollback and no recovery action. Memory can stay ahead of
disk until a later successful save — a state the original import feature already
called out as undesirable (“stored collections must not contradict what the
sidebar shows”).

**Goal:** Ensure that a mid-write save failure during multi-collection import
does not leave the user with an unexplained or unrecoverable memory-vs-disk
divergence. Either the import finishes with memory and disk aligned, or the
failure path gives the user an explicit way to restore that alignment.

**Scope (in):**

- Multi-collection **collection** import when one or more persistence writes
  fail after the import has begun applying changes.
- User-visible outcome and consistency guarantees for that failure case
  (including recovery UX if that approach is chosen).
- Automated coverage for the mid-write failure consistency outcome and the
  successful multi-collection import regression.
- A short update to the developer collection-import docs describing the new
  failure/recovery behavior.

**Scope (out):**

- Environment import (separate persistence model; not this debt item).
- Changing conflict resolution, file format, or the happy-path import workflow
  beyond what is needed for consistency on save failure.
- Guaranteeing that every individual collection write is immune to every
  possible OS/storage failure mode beyond the consistency/recovery outcome
  above (e.g. total disk failure mid-process is still a failure — the
  requirement is that the user is not left silently inconsistent without a path
  forward).
- Moving import parsing off the UI thread, rename-summary fixes, extra parse-log
  assertions, and mypy baseline keying — those are separate follow-ups from
  PYPOST-987.

**Constraints and assumptions:**

- Collections are persisted as part of the import action; the user expects what
  they see after import to match what will load after a restart.
- Partial success reporting (some collections saved, some not) may still be
  truthful if the chosen approach allows it — but only if memory and disk agree
  for every collection involved, or the user has completed explicit recovery to
  that agreement.
- The source debt item allows either an all-consistent import outcome or
  explicit recovery; both are valid business solutions. Architecture chooses
  which; requirements do not mandate one mechanism.

## Non-Functional Requirements

- Mid-write failure handling must not make successful imports perceptibly slower
  or more fragile for typical collection files.
- Failure and recovery messaging must not expose secrets from collection
  contents (headers, bodies, scripts); identifying failed collections by name
  (as today’s failure lines already do for the user) remains acceptable.
- Behavior must remain correct for imports of one collection and of many; the
  consistency requirement applies whenever more than one write is attempted and
  at least one fails, and must not regress the single-collection failure case.

## Main Entities

- **Collection** — a named group of saved requests the user imports; each
  changed collection is expected to appear in the sidebar and to be durable on
  disk after a successful import.
- **Multi-collection import** — one user action that brings in or updates
  several collections from a single file.
- **Import result** — the user-visible outcome after import, including success
  vs unsuccessful status and per-collection save-failure reasons when writes
  fail.
- **Durable collection set** — the collections that exist on disk and would be
  loaded after a restart.
- **Visible collection set** — the collections the user currently sees in the
  app (sidebar / in-app state).
- **Consistency** — visible collection set and durable collection set agree for
  the collections touched by the import (after the import completes, or after
  the user completes any offered recovery).

## Q&A

- **Q: Why does this matter if the failure is already logged and shown as
  unsuccessful?**
  A: Logging and an unsuccessful dialog tell the user something went wrong, but
  they do not fix the mismatch. The tree can still show imported or updated
  collections that are not on disk. Users reasonably treat “I see it in the
  sidebar” as “it is saved.” Closing that gap is the business need.

- **Q: Must the solution be fully atomic, or is recovery enough?**
  A: Either fulfills the goal. The debt item explicitly allows choosing between
  a consistent all-or-nothing-style import outcome and an explicit recovery path
  that restores alignment. Architecture picks one; this document only requires
  that memory and disk are not left unexplainedly out of sync without a
  user-facing way to restore sync. (Non-normative illustration only: recovery
  might mean restoring the visible set from what is already durable, or another
  equally clear user action — requirements do not prescribe the mechanism.)

- **Q: Does a successful import change?**
  A: No. Successful multi-collection imports must continue to apply, persist,
  refresh the tree, and show a successful summary as today.

- **Q: Is environment import in scope?**
  A: No. This follow-up is specifically about multi-collection import mid-write
  save failure from PYPOST-987.

- **Q: What about a failure writing the only collection in a one-collection
  import?**
  A: That case must not regress: the user should still get a clear unsuccessful
  outcome, and must not be left believing a collection is durable when it is
  not. The multi-collection mid-write case is the primary gap; single-collection
  failure remains covered by the same consistency principle.

- **Q: Where did this requirement come from?**
  A: Follow-up item 2 in `ai-tasks/PYPOST-987/60-tech-debt.md`, ticketed as
  [PYPOST-1004](https://pypost.atlassian.net/browse/PYPOST-1004). The parent
  import feature (PYPOST-987) already required that stored collections must not
  contradict the sidebar; this task closes the remaining mid-write save-failure
  hole.
