# PYPOST-326: Keep MainWindow free of collection delete-flow responsibilities

## Goals

`MainWindow` should remain a thin composition root. Collection delete confirmation,
telemetry, and tree context-menu handling must not accumulate in this class.

## User Stories

- As a maintainer, I want delete-flow logic in presenter/action modules so I can change
  collection behavior without editing the main window shell.
- As a user, I want collection delete to work exactly as before (context menu, confirm,
  tree refresh, tab closure).

## Definition of Done

- `MainWindow` has no delete-flow methods (`show_context_menu`, `handle_delete`, etc.).
- Delete flow is owned by `CollectionTreeActions` via `CollectionsPresenter`.
- `MainWindow` only wires `requests_deleted` to tab closure (composition).
- Regression tests pass.

## Task Description

Follow-up from PYPOST-35 tech debt: delete was initially added on `MainWindow`; later
refactors moved logic to presenters. This task verifies and finalizes that boundary.

### Programming Language

Python

## Q&A

- **Why not move tab closure into collections?** Tab lifecycle belongs to `TabsPresenter`;
  signal wiring in `MainWindow` is appropriate composition.
