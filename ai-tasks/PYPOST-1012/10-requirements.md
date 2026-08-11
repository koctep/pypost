# PYPOST-1012: Export all collections to a JSON list

## Programming language

Python

## Goals

PyPost already lets users export one selected collection, while collection import already
accepts a JSON list containing several collections. Users who want a complete backup or a
portable copy of all of their request collections must otherwise export each collection
separately. This task provides one deliberate bulk-export action so a user can save their
whole collection library in a single, importable file.

## User Stories

- As a **user**, I want to export all of my collections in one action, so I can make a
  complete backup without repeating a save flow for each collection.
- As a **user**, I want the bulk-exported file to import through **Import Collection…**,
  so I can restore or move my full collection library to another PyPost installation.
- As a **user**, I want to choose where the backup is saved and receive clear success or
  error feedback, so I know whether the backup was created.
- As a **user with no collections**, I want export-all to create a valid empty backup, so
  I can preserve the empty state and verify the backup flow without an error.
- As a **maintainer**, I want automated coverage of the bulk-export result and its
  user-visible outcomes, so backup compatibility does not regress.

## Definition of Done

- [ ] A clearly labelled **Export All Collections…** action is available with the other
      collection management actions; it does not require selecting a collection or request.
- [ ] The action lets the user select a destination and exports the current set of
      collections as one JSON list.
- [ ] Each exported collection includes its saved requests and the same collection/request
      information preserved by the existing single-collection export, so the list can
      round-trip through **Import Collection…** without manual repair.
- [ ] When there are no collections, the result is a valid empty JSON list and the user
      receives normal success feedback showing that zero collections were exported.
- [ ] On success, feedback identifies the saved destination and the number of exported
      collections and requests. On cancellation or a write failure, the user receives an
      appropriate clear outcome; cancellation creates no file.
- [ ] Exporting is non-destructive: it does not alter, remove, rename, reorder, or add
      collections or requests in the current PyPost workspace.
- [ ] Automated tests cover the JSON-list shape, fidelity for multiple collections,
      empty-library behaviour, and success/error user outcomes.
- [ ] User documentation explains how to create and restore a full collection backup.

## Task Description

**Problem:** A user can export a selected collection, but cannot create one complete
backup of all collections from PyPost. Repeating single-collection export is slow and can
omit collections accidentally. The import experience already accepts a list, so a
multi-collection backup has an established restore path.

**Goal:** Let a user save all currently available collections, including their requests,
to one user-chosen JSON file that PyPost's existing collection import experience accepts.

### Scope (in)

- One bulk **Export All Collections…** user action in the collections area.
- A user-chosen output file containing one JSON list representing the complete current
  collection library, including an empty library as an empty list.
- Compatibility with the existing collection-import experience for restoring the file.
- Clear completion, cancellation, and error feedback.
- Automated tests and user-facing documentation.

### Scope (out)

- Changing the import format, conflict choices, or restore behaviour.
- Changing the existing single-collection export action or file shape.
- Selective multi-collection export, filtering, or exporting only a tree selection.
- Exporting environments, history, settings, or any data outside collections and their
  saved requests.
- Postman, Insomnia, OpenAPI, or other third-party export formats.
- Scheduled, automatic, cloud, or encrypted backup management.

## Assumptions and Constraints

- The collection library visible to the user at the time export begins is the complete
  set to include; the action has no collection-selection prerequisite.
- The JSON list uses the same per-collection content that the existing single-collection
  export provides. A list file remains a PyPost-native backup rather than a new general
  interchange format.
- Existing Import Collection… conflict handling applies when a backup is restored into a
  workspace that already has collections with matching names.
- A successful backup is a copy only. It must not modify current in-app data or remove the
  source data after writing.
- Exported collection content can include request values already saved in collections.
  Users remain responsible for handling backup files according to their local data
  sensitivity policies.

## Main Entities and Interactions

- **Collection library** — the complete set of collections currently available in the
  PyPost workspace.
- **Collection** — a named group of saved requests; each collection is one entry in the
  exported list.
- **Request** — a saved HTTP request belonging to a collection; it remains associated with
  its collection in the backup.
- **Bulk export action** — the user-initiated collection-management action that starts a
  complete backup.
- **Backup file** — the user-chosen JSON file containing the collection list.
- **Collection import** — the existing restore path that reads a JSON list and reports its
  outcome.

Interaction flow: user chooses **Export All Collections…** → chooses a destination →
PyPost saves a list representing the current collection library → user receives a success,
cancellation, or error outcome. To restore, the user later chooses **Import Collection…**
and selects that backup file.

## Non-Functional Requirements

- **Fidelity:** every collection and saved request must retain the information required for
  the existing PyPost collection import to restore it faithfully.
- **Reliability:** a completed export must be valid JSON and usable by the existing import
  flow; a failed or cancelled export must not be reported as successful.
- **Non-destructive behaviour:** reading collections for backup must not alter the current
  workspace.
- **Clarity:** labels, destination choice, and completion/error feedback must make the
  action's all-collections scope and result unambiguous.
- **Consistency:** the experience should align with the existing collection export and
  import flows so users recognize the format and recovery path.

## Q&A

**Q: Why export all collections as a JSON list?**

**A:** One list gives users a single complete backup file, and **Import Collection…**
already accepts a file containing several collections in that shape.

**Q: Does the user need to select a collection first?**

**A:** No. The action backs up the complete current collection library, regardless of tree
selection.

**Q: What happens when the library is empty?**

**A:** Export succeeds with an empty JSON list and reports zero exported collections.

**Q: Does this replace Export Collection…?**

**A:** No. Single-collection export remains for sharing or backing up one collection;
export-all is an additional complete-backup action.

**Q: What happens if imported backup names conflict with existing collections?**

**A:** This task does not change import. The existing Import Collection… conflict choices
apply during restoration.

**Q: Are environments or other PyPost data included?**

**A:** No. The backup covers collections and their saved requests only.
