# PYPOST-1059: UI regression asserting collections tree matches durable storage after import save failure

## Goals

When importing collections into PyPost, users rely on the sidebar collections tree to accurately reflect their saved collections. If a save failure occurs partway through or during an import (for example due to disk write errors or storage failures), the application must ensure that the user interface never displays unpersisted or "ghost" collections that do not exist on disk.

While unit tests in the core application logic verify in-memory reconciliation against durable storage upon save failure, the application requires end-to-end user interface regression tests. These tests ensure that following an import save failure (whether partial or total), the collections sidebar tree component, its underlying model, and the visible collection items strictly match what is actually preserved in durable storage.

**Implementation language**: Python (hardening test coverage within the existing Python Qt codebase; no new language or framework introduced).

## User Stories

- As a user performing a collection import where one or more collections fail to save to disk, I want the sidebar collections tree to display only the collections that successfully exist in durable storage, so that I never see unsaved collections in the UI.
- As a user reviewing the application state after an import save failure, I want the visible collection hierarchy and count to match what will load if I restart the application, so that my trust in the displayed data is maintained.
- As a user whose collection import succeeds completely, I want the sidebar tree to continue displaying all imported collections as expected, so that testing or hardening failure paths does not affect normal import operations.

## Definition of Done

- When an import flow encounters a save failure for one or more collections, the visible collections sidebar tree and in-app collection list match the actual durable collections on disk.
- In a partial save failure scenario (some collections saved to disk, others failed), the sidebar tree displays only the successfully saved collections and excludes any unsaved collections.
- In a total save failure scenario (all imported collections fail to save), the sidebar tree retains only the pre-existing durable collections without any failed import additions.
- Automated UI regression test(s) in the test suite assert that after an import with save failure(s), the sidebar tree model and visible collection entries match durable storage.
- Happy-path collection imports continue to display all imported collections in the sidebar tree without regressions.

## Task Description

**Problem:**
During collection import, collections are parsed, applied, and persisted to disk. If persistence fails for one or more collections mid-write, the application marks the import as unsuccessful and reconciles in-memory data with durable storage. However, prior testing focused primarily on core data-layer reconciliation unit tests. The UI test suite needs explicit end-to-end regression assertions confirming that the sidebar tree view and presentation layer properly reflect durable storage rather than leaving unpersisted collections visible in the UI.

**Goal:**
Provide automated UI regression testing asserting that after any collection import save failure, the collections sidebar tree in the UI strictly matches durable storage.

**Scope (in):**
- UI regression test coverage verifying that the sidebar collections tree widget and its presentation model match durable storage after save failures during import.
- Testing scenarios covering both partial save failure (some collections saved, some failed) and complete save failure.
- Verifying that row counts and visible collection names in the sidebar tree model match durable storage.

**Scope (out):**
- Modifying core persistence or reconciliation algorithms (already established in PYPOST-1004).
- Changing import dialog UX or conflict resolution strategies.
- Non-UI storage engine changes or environment imports.

**Constraints and assumptions:**
- Implemented in Python using the existing PySide6 / Qt UI framework and pytest test runner.
- All test additions must adhere to project testing standards (including explicit timeouts).

## Non-Functional Requirements

- UI regression tests must run efficiently and deterministically within standard test suite execution times.
- Tests must declare required pytest timeout markers in accordance with project testing guidelines.

## Main Entities

- **Collections Sidebar Tree**: The user interface tree widget presenting the visual hierarchy of saved collections to the user.
- **Durable Storage**: The persistent file storage on disk where collections are stored and loaded across application restarts.
- **Collection Import Flow**: The UI-driven workflow through which collection files are selected, processed, persisted, and rendered.
- **Import Save Failure**: An error condition occurring during import when writing one or more collections to disk fails.

## Q&A

- **Q: Why is a dedicated UI regression test needed if core unit tests already exist?**
  A: Core unit tests verify data reconciliation in isolation. UI regression tests verify the presenter, Qt signal dispatching, and tree widget model binding together, ensuring the visual sidebar tree seen by users accurately matches disk.

- **Q: What specific failure scenarios should be validated in the UI?**
  A: Both partial save failure (where a subset of imported collections persist while others fail) and complete save failure (where all attempted saves fail). In all cases, the collections displayed in the sidebar tree must match durable storage.

- **Q: Does this task change existing import behavior or file formats?**
  A: No. It establishes automated regression verification that existing UI behavior correctly adheres to durable storage consistency after import save failures.

- **Q: Where did this requirement originate?**
  A: Follow-up item #3 from `ai-tasks/PYPOST-1004/60-tech-debt.md`, ticketed as [PYPOST-1059](https://pypost.atlassian.net/browse/PYPOST-1059).
