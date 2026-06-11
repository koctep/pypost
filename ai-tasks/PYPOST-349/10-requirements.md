# PYPOST-349: Extract collection-tree context-menu actions

## Goals

Improve maintainability of the collections tree UI by isolating context-menu behavior
(rename, delete, new tab) from tree loading and navigation, without changing what users
see or how actions behave.

## User Stories

- As a maintainer, I want collection context-menu logic in a focused module so I can
  change menu actions without navigating a large presenter file.
- As an API user, I want right-click actions on the collections tree to work exactly as
  before (rename, delete, new tab on requests).

## Definition of Done

- Context-menu build, dispatch, rename flow, and delete flow live in a dedicated module.
- `CollectionsPresenter` delegates to the new module; tree loading, click-to-open, and
  expand/collapse state remain in the presenter.
- All existing collections presenter tests pass without behavior changes.
- Logging and metrics for rename/delete/new-tab actions are unchanged.

## Task Description

### Problem Statement

`CollectionsPresenter` combined tree rendering with context-menu orchestration and
rename/delete flows. PYPOST-36 tech debt identified this as a maintainability risk.

### Programming Language

Python

### Functional Requirements

- Extract `_show_context_menu` and related action handlers into a focused component.
- Preserve identical menu items, confirmation dialogs, inline rename, and delete behavior.
- Keep presenter public API and signals (`collections_changed`, `request_renamed`,
  `requests_deleted`, `open_request_in_isolated_tab`) unchanged.

### Non-Functional Requirements

- No user-visible behavior change.
- Existing unit tests remain valid (patch paths updated only where imports moved).

### Constraints and Assumptions

- Refactor only; no new menu actions or validation rules.
- Observability (logs/metrics) moves with the extracted code, unchanged in content.

### System Boundaries (Scope)

- In scope: context menu, rename editor lifecycle, delete confirmation and execution.
- Out of scope: tree model building, left-click open, expand/collapse persistence.

## Q&A

- Q: Why extract now?
  A: Follow-up from PYPOST-36 technical debt to reduce presenter size.
- Q: Must behavior be identical?
  A: Yes — refactor only, no feature changes.
