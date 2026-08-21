# PYPOST-1058: Durable-aligned collection import result recount after save failure

## Programming Language

Python is the implementation language for the application core, UI presentation, and test suite.

## Goals

When a user imports collections into the application, the system evaluates incoming data against existing collections and formulates an import plan (identifying which collections to add, update, skip, or rename/keep both, and tallying the number of requests to import). Following the planning phase, the system writes the affected collections to durable storage (disk) and reconciles the in-app collection list with durable storage if any write failure occurs.

However, when one or more collections fail to save to disk, the import summary dialog currently presents the counts calculated from the initial plan rather than what actually succeeded and exists in the durable collection set. For example, if a newly added collection or an updated collection fails to write to disk, the completion dialog still reports that 1 collection was added or updated, even though after the failure and reload, that collection does not exist in the collection list or was reverted to its prior state.

This mismatch creates a confusing, contradictory, and untruthful user experience: the summary dialog states that items were added/updated, while the sidebar collection tree does not contain them.

**Business goal:** Ensure that when a collection import encounters save failures, the import result summary presented to the user accurately recounts Added, Updated, Renamed, and Requests Imported totals against the actual durable collection outcome, presenting an honest reflection of what persisted to disk and matches the visible collection tree.

## User Stories

- As a **user importing collections where some saves fail**, I want the result summary dialog to report only the collections and requests that successfully persisted to durable storage, so that the numbers shown in the summary match what I actually see in my sidebar.
- As a **user whose newly added collection fails to write to disk**, I want the result summary to report 0 Added for that collection and exclude its requests from the imported request total, accompanied by the specific save failure error, so that I am not misled into believing the collection was saved.
- As a **user whose updated collection fails to write to disk**, I want the result summary to report 0 Updated for that collection and exclude its incoming requests from the imported request total, so that I clearly know the update did not persist.
- As a **user whose renamed (conflict copy) collection fails to write to disk**, I want the result summary to exclude that item from the Renamed count and the renamed collections list, so that I do not look for a renamed copy that was never saved.
- As a **user experiencing a total save failure** (where all intended writes fail), I want the result summary to report 0 Added, 0 Updated, 0 Renamed, and 0 Requests Imported alongside the detailed save errors, clearly indicating that nothing was persisted.
- As a **user whose collection import succeeds completely**, I want the result summary to continue reporting all added, updated, and renamed collections and total imported requests, preserving the happy-path behavior.

## Definition of Done

- When an import encounters one or more collection save failures, the result summary presented to the user (Added, Updated, Renamed, and Requests Imported) reflects only the collections that successfully persisted to durable storage and remain in the active collection list.
- If an "Added" collection fails to save:
  - It is not included in the "Added" count.
  - Its requests are not included in the "Requests imported" count.
- If an "Updated" (overwritten) collection fails to save:
  - It is not included in the "Updated" count.
  - Its requests are not included in the "Requests imported" count.
- If a "Renamed" (Keep Both / copy) collection fails to save:
  - It is not included in the "Renamed" count.
  - It is not listed in the "Renamed Collections" detail section.
  - Its requests are not included in the "Requests imported" count.
- Skipped collections continue to be counted accurately under the "Skipped" total.
- Collections that failed to save continue to be explicitly listed with their error messages in the error section of the result summary.
- The overall import result dialog status continues to clearly indicate an unsuccessful outcome whenever save failures occur.
- When all attempted collection writes fail, all success counts (Added, Updated, Renamed, Requests Imported) evaluate to 0, and all save errors are displayed.
- When all attempted collection writes succeed (happy path), the summary counts match the full plan without regression.
- Automated tests cover result recount accuracy across partial save failure, total save failure, and successful multi-collection import scenarios.

## Task Description

**Problem:** During collection import, PyPost plans changes (Added, Updated, Renamed, Skipped) and attempts to persist the modified collections. Under PYPOST-1004, if any write fails, memory is reloaded from durable storage so that the visible sidebar is consistent with disk. However, the completion summary dialog still displays the planned numbers. When an item fails to save and disappears or reverts upon reload, the summary dialog displays stale, inaccurate counts that contradict what is actually present in the app.

**Goal:** Recount the import outcome based on the surviving durable membership when save failures occur, aligning the result summary dialog with the durable state.

**Scope (in):**
- Recounting the summary numbers (Added, Updated, Renamed, and Requests Imported) when an import completes with save failures.
- Ensuring the renamed collection details list only includes collections that successfully persisted.
- Presenting truthful error lines for collections that failed to save alongside the adjusted counts.
- Automated test coverage for durable-aligned summary recounting on partial, total, and zero save failure scenarios.

**Scope (out):**
- Altering the conflict resolution prompt or decision logic.
- Modifying how collection files are parsed from disk or changing the file import format.
- Modifying environment import (which uses a separate persistence model).
- Changing the underlying storage mechanisms or introducing multi-file filesystem transactions.

**Constraints and assumptions:**
- An import that experiences save failures must remain classified as unsuccessful overall.
- The summary dialog is the single source of truth for the user regarding what the import accomplished and what failed.
- The recount must accurately handle mixed outcomes (e.g., some additions succeed, some fail, some updates succeed, some fail).

## Main Entities and Interactions

- **Collection:** A named container of saved API requests.
- **Import Candidate:** A collection parsed from an external file awaiting import into the application.
- **Import Plan:** The intended modifications (additions, overwrites, copies/renames, skips) computed prior to persistence.
- **Durable Collection Set:** The set of collections successfully written and residing on disk.
- **Import Result Summary:** The user-visible dialogue presenting the outcome of the import (counts of Added, Updated, Skipped, Renamed, Requests Imported, rename mappings, and error details).
- **Save Failure:** An error encountered during the persistence of an individual collection to disk.

**Interactions:** When the user initiates an import, the system parses incoming collections and generates an import plan. The system attempts to save changed collections to durable storage. If any save failure occurs, the system reconciles with durable storage, recalculates the import summary counts to match what actually persisted, and displays the durable-aligned summary and failure details to the user.

## Non-Functional Requirements

- **Accuracy and Truthfulness:** The reported counts in the summary dialog must never contradict the actual state of collections in the application or on disk.
- **Clarity:** Error descriptions must clearly distinguish which collections failed to save without confusing the user about whether partially successful items survived.
- **Performance:** Recounting the durable outcome must execute instantaneously without introducing noticeable delay in displaying the completion dialog.
- **Safety:** Failure recounting must not alter collection data or suppress any error messages.

## Q&A

**Q: Why was this not done as part of PYPOST-1004?**
**A:** PYPOST-1004 established the core safety guarantee: ensuring that in-memory state and the sidebar tree reconcile with disk upon mid-write save failure (avoiding phantom unsaved collections in the UI). Updating the result summary dialog to recount counts (Dialog Option A) was documented as a follow-up refinement in `ai-tasks/PYPOST-1004/60-tech-debt.md` and ticketed as PYPOST-1058.

**Q: If an update (overwrite) to an existing collection fails, what should the result summary report?**
**A:** The collection was not updated in durable storage; its prior durable version remains. Therefore, the "Updated" count for that collection must be 0, its new requests must not be counted under "Requests imported", and a save failure error must be listed for that collection.

**Q: If a renamed (Keep Both) collection fails to save, what should happen to the "Renamed" section?**
**A:** Since the new copy was not saved to disk and is not retained in the collection set, it must not increment the "Renamed" count and must not appear in the renamed detail mappings (`"Old Name" -> "New Name"`).

**Q: Does this change the behavior when all writes succeed?**
**A:** No. On the happy path where all writes succeed, every planned addition, update, and rename is durable, so the summary counts will naturally match the planned counts.
