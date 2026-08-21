# PYPOST-1061: Optional determinate progress during collection import validation

## Programming Language

Python

## Goals

PyPost supports importing collections from shared files and backups. During collection import, incoming collection entries are validated to ensure they conform to expected structures before conflict resolution and persistence occur.

Currently, validation of collection candidates provides an indeterminate status indication. When importing large files that contain many collection records, users and integrating components have no granular visibility into how many records have been validated versus the total number of records in the file.

The business goal is to provide optional determinate progress tracking during collection candidate validation. This enables progress observers to monitor and report concrete progress (such as processed items out of total candidate items) as validation proceeds, improving transparency for multi-collection imports without modifying existing import outcomes or imposing overhead when progress tracking is not needed.

## User Stories

- As a **user importing a collection bundle**, I want to see determinate progress (such as items processed out of total items) while collection records are being validated, so that I have clear visibility into how much work has completed and how much remains.
- As a **user importing a standard or small collection file**, I want the import process to complete smoothly and quickly without unnecessary overhead when determinate progress is not required.
- As an **application component / caller**, I want to optionally supply a progress observer when initiating candidate validation, so that progress updates can be reported across application layers.
- As a **user**, if some collection records within an import file are malformed or invalid, I want those errors to be captured and reported accurately while the progress tracker continues to advance across all candidate records.
- As a **maintainer**, I want automated test coverage for determinate progress reporting during collection validation, verifying that progress counts accurately match candidate record counts.

## Definition of Done

- [ ] Collection candidate validation supports an optional progress tracking mechanism that reports the number of processed records and the total number of candidate records.
- [ ] When progress tracking is omitted or inactive, collection candidate validation functions identically to existing behavior without regressions.
- [ ] Determinate progress updates advance correctly across all candidate entries, including entries that fail individual record validation.
- [ ] File-level import failures (such as unreadable files or malformed root data) cleanly terminate validation and report appropriate errors.
- [ ] Existing collection import behaviors (conflict detection, user prompts, import summaries, and tree refreshes) remain preserved.
- [ ] Automated tests verify that determinate progress reporting accurately reflects candidate counts across valid, invalid, and mixed collection files.

## Task Description

**Problem:** When importing collection files containing numerous collection records, the system only provides indeterminate waiting feedback. Users cannot tell how many records have been checked or estimate how much time remains for candidate validation.

**Goal:** Enable optional determinate progress reporting during the candidate validation phase of collection import, allowing progress observers to receive granular progress updates without altering import semantics.

### Scope (in)

- Optional determinate progress reporting during collection candidate validation (reporting completed count and total count).
- Preservation of standard behavior when progress tracking is not requested.
- Consistent progress progression across both valid and invalid candidate entries.
- Automated tests verifying determinate progress updates for single, multi-record, and invalid collection files.

### Scope (out)

- Altering the collection file format or third-party export/import formats.
- Low-level streaming JSON byte parsers or lexical chunking.
- Modifying conflict resolution policies (overwrite, keep both, skip).
- Changing import planning, file persistence, or request identifier collision resolution.
- Modifying unrelated export or startup loading workflows.

### Constraints and assumptions

- Implementation language: Python.
- Source follow-up: [PYPOST-1005](https://pypost.atlassian.net/browse/PYPOST-1005) technical debt item #2 -> [PYPOST-1061](https://pypost.atlassian.net/browse/PYPOST-1061).
- Progress tracking applies to candidate record inspection and validation after raw file records are read.
- sprint-task-runner operates autonomously; approval gates are handled by workflow reviews.

## Main entities and interactions

| Entity | Attributes | Role |
| --- | --- | --- |
| User | Import request; file selection | Initiates import and views progress |
| Collection import file | Candidate collection records | Source file being imported |
| Candidate validator | Record validation logic | Validates candidate records and triggers progress updates |
| Progress observer | Processed count; total count | Receives incremental progress updates during validation |
| Validation outcome | Valid collections; error list | Results produced after all candidates are validated |

Interaction overview:

1. User selects a collection file for import.
2. The candidate validator determines the total candidate record count and begins validating records sequentially.
3. For each candidate record processed (valid or invalid), the progress observer is notified with the current progress count and total count.
4. Validation concludes, yielding the list of valid collection candidates and any validation errors encountered.
5. The import workflow proceeds to conflict resolution and persistence as normal.

## Q&A

**Q:** Why is determinate progress needed if collection import already runs asynchronously without locking the UI?

**A:** Asynchronous execution prevents UI lockup, but an indeterminate spinner or message does not show how much of a large bundle has been evaluated. Determinate progress allows callers and users to see exact progress counts (e.g. 45/100 collections validated).

**Q:** Is determinate progress mandatory for all collection imports?

**A:** No. It is optional. When no progress observer is provided, candidate validation runs directly as before with no extra overhead or behavior changes.

**Q:** How are invalid records in a multi-collection file handled during progress tracking?

**A:** Each invalid record is recorded in the error list, the progress count increments as that record has been evaluated, and validation proceeds to the next candidate record.

**Q:** Does this task modify conflict prompts or how imported collections are saved to disk?

**A:** No. Conflict detection, user prompts, planning, and persistence occur after candidate validation and remain untouched.
