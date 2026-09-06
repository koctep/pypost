# PYPOST-1279: Support importing collections from file and connected library

## Goals

PyPost users need a clear way to bring collections into the active workspace from
either a standalone file or a collection library they already connected. The
current Collections UI offers a single file-oriented import action, which makes
library collections harder to discover and encourages manual copying.

The business goal is to make collection reuse predictable and discoverable while
preserving the user's choice between an independent copy and an association with
the library source.

## User Stories

- As a PyPost user, I can choose whether I am importing a collection from a file
  or from a connected collection library.
- As a PyPost user, I can import collections from a standalone JSON or YAML file
  without losing the current validation, conflict handling, and result feedback.
- As a PyPost user, I can browse connected and cloned libraries and see the
  collections each library makes available.
- As a PyPost user, I can select one or more library collections and choose to
  copy them into active collections or link them to their library source.
- As a PyPost user, I receive a clear explanation when a library is unavailable,
  contains no importable collections, or an import cannot be completed.
- As a PyPost maintainer, I can rely on documented and independently testable
  behavior for both import choices and their Collections UI entry points.

## Functional Requirements

### Import choices

1. The Collections UI must expose two distinct, clearly named choices:
   `From File` and `From Library`.
2. The existing import entry points in the Collections area must route to the
   matching choice, and choosing one route must never silently invoke the other.
3. The two choices must be understandable without requiring users to know how
   collections are stored internally.

### From File

4. `From File` must allow a user to select a standalone collection file in JSON
   or YAML format, including the currently supported collection representation.
5. The file flow must continue to validate imported collection data and report
   invalid files or invalid entries in language the user can act on.
6. A file containing both valid and invalid entries must import the valid entries
   and report the entries that could not be imported.
7. If an imported collection conflicts with an active collection, the user must
   be able to choose the existing collection conflict behavior: overwrite, keep
   both under a distinct name, or skip.
8. Cancelling the file picker, validation, or a conflict decision must leave the
   active collections unchanged for the cancelled part of the operation.

### From Library

9. `From Library` must list the collection libraries currently connected to
   PyPost, including managed clones and registered local libraries.
10. The library selection experience must show each available library and the
    collections bundled by that library. A readable collection name must be
    shown; when no friendly name is available, the collection's source label
    must still identify it.
11. The user must be able to select one or more bundled collections for import.
12. The user must explicitly choose one import mode for the selection:
    - **Copy** creates an independent active collection. Later edits to the
      active copy do not alter the library source.
    - **Link** keeps the active collection associated with the selected library
      collection, making the library source authoritative when the linked
      collection is refreshed.
13. Importing from a library must add the selected collections to active
    collections without changing the library's source files or connection
    settings.
14. Library imports must preserve the selected collection's usable content,
    including its requests and collection-level data.
15. If a selected library or collection becomes unavailable before import, the
    user must receive an actionable message and no unavailable item may be
    silently imported as an empty collection.
16. If a library import conflicts with an active collection, the user must
    receive a clear choice to replace, keep both under a distinct name, or skip
    the conflicting item.
17. Cancelling the library selector, mode choice, or conflict decision must not
    add, replace, or partially link the cancelled selection.
18. When no connected library can provide an importable collection, `From
    Library` must explain why and leave active collections unchanged.

### Completion and feedback

19. After a successful import, the Collections UI must show the imported
    collections without requiring an application restart.
20. The result must distinguish successful additions, replacements, retained
    copies, skipped items, and failures when more than one outcome occurs.
21. Import controls must provide an understandable busy or progress indication
    during work that may take noticeable time and must return to an available
    state after success, failure, or cancellation.
22. User-visible errors must not expose credentials or other unrelated sensitive
    library configuration.

## Scope

### In scope

- The Collections UI choices and their menus or buttons.
- Standalone JSON and YAML collection imports, retaining and refining the
  existing behavior.
- Selection of connected, registered, or cloned collection libraries.
- Display of libraries and their bundled, importable collections.
- Copy and link outcomes for selected library collections.
- Consistent conflict, cancellation, validation, and result feedback for both
  import sources.
- Automated presenter and dialog coverage for the two choices and their key
  outcomes.
- Developer documentation describing the supported import paths and behavior.

### Out of scope

- Creating, cloning, registering, disconnecting, or otherwise managing library
  connections.
- Downloading or discovering libraries that are not already connected to PyPost.
- Changes to Git synchronization, library authentication, or library source
  editing.
- Importing Postman, Insomnia, OpenAPI, or other foreign collection formats.
- Importing environments as part of this task.
- Redesigning collection editing, request execution, or active collection
  storage beyond what is needed to support the two import outcomes.

## Non-Functional Requirements

- **Discoverability:** The two import routes and the copy/link distinction must
  use plain language and consistent labels throughout the Collections UI.
- **Safety:** No source library files may be changed by an import. Destructive
  replacement of an active collection requires an explicit user decision.
- **Consistency:** Equivalent validation, conflict, cancellation, and result
  rules should behave the same regardless of import source.
- **Responsiveness:** Users must be able to understand that an import is still
  progressing and must not be left with controls that appear permanently stuck.
- **Testability:** The behavior of each import choice, the selection dialog,
  and the main user-visible outcomes must be covered by automated tests.
- **Documentation:** Developer documentation must state supported sources,
  copy/link semantics, failure behavior, and verification guidance.

## Business Entities

| Entity | Business attributes |
| --- | --- |
| Active collection | Name, requests, collection-level data, and current workspace presence. |
| Standalone collection file | File name, JSON or YAML format, one or more collection entries, and validation outcome. |
| Collection library | Display name, connection state, source kind, and available bundled collections. |
| Bundled collection | Library identity, readable name or source label, usable collection content, and availability. |
| Import selection | Chosen source, selected collections, requested mode, conflict decisions, and final outcome. |

## Acceptance Criteria

- The Collections UI presents `From File` and `From Library` as separate import
  options, and each option opens the correct user flow.
- A user can import valid JSON and YAML collection files, receives useful
  validation feedback, and sees the imported collections in the active workspace.
- A user can open the library selection experience, see connected/cloned
  libraries and their bundled collections, select collection entries, and choose
  Copy or Link.
- Copy produces an independent active collection; Link preserves the library
  association and treats the library source as authoritative during refresh.
- Neither import route modifies the source library. Conflicts, cancellations,
  unavailable sources, and partial failures produce explicit outcomes without
  silent data loss.
- Presenter and dialog tests cover both entry points, library/collection
  selection, copy/link choice, cancellation, conflict handling, and failure
  feedback.
- Developer documentation explains both routes, their boundaries, and how to
  verify them.
- The requirements, architecture, implementation, test, cleanup, observability,
  review, and documentation work remains traceable to PYPOST-1279.

## Q&A and Resolved Assumptions

| Question | Resolution for this task |
| --- | --- |
| What does “connected/cloned” include? | Include both managed clones and registered local library directories that are currently connected and readable. Do not add connection-management behavior here. |
| Can the user select more than one library collection? | Yes. The selector supports one or more entries, and one chosen mode applies to the current selection. |
| What does Copy mean? | It creates an independent active collection whose later edits do not change the library source. |
| What does Link mean? | It preserves an association with the library collection and treats the library content as authoritative when refreshed. The task does not require editing the source through the active collection. |
| How should conflicts work? | Reuse the established user choices—replace, keep both with a distinct name, or skip—for either import source. |
| What happens when a source becomes unavailable? | Stop that item safely, explain the reason, and do not create an empty or misleading active collection. Other valid selections may complete if they are independent. |
| Is `.yml` supported? | `.json` and `.yaml` are required by this ticket. Existing `.yml` compatibility may remain, but no new foreign-format support is implied. |
| What if a connected library has no usable collections? | Show an explanatory empty or unavailable state and make no active-collection changes. |
