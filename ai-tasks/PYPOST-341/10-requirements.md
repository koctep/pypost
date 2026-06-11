# PYPOST-341: Dedicated delegate for collection inline rename

## Goals

Collection tree inline rename should use a focused Qt delegate instead of wiring
`closeEditor` on the default tree delegate. This isolates editor lifecycle and validation
from presenter wiring and keeps rename behavior consistent with other inline editors
(e.g. environment rename).

## User Stories

- As a maintainer, I want rename editor behavior in a dedicated class so tree actions stay
  testable and do not depend on default delegate signals.
- As a user, I want the same rename experience (context menu, inline edit, empty-name
  rejection, cancel) after the refactor.

## Definition of Done

- `CollectionItemRenameDelegate` owns inline editor create/populate/commit/cancel.
- `CollectionsPresenter` installs the delegate on the collections tree view.
- `closeEditor` is no longer connected on the default `itemDelegate()`.
- Existing rename logs, metrics, persistence, and incremental tree sync behave unchanged.
- Automated tests cover delegate validation and existing presenter rename paths pass.

## Task Description

PYPOST-36 tech debt: rename used `QTreeView` editor close events (originally in
`MainWindow`, later in `CollectionTreeActions` via default delegate). Replace with a
dedicated delegate class following the `EnvironmentNameDelegate` pattern.

## Q&A

- **Q:** Change user-visible rename UX? **A:** No — same flows and messages.
- **Q:** Move business logic into delegate? **A:** No — delegate validates editor input;
  `CollectionTreeActions` keeps persistence, metrics, and tree sync.
