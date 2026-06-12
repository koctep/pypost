# PYPOST-129: Split VariableHoverHelper responsibilities

## Goals

Hover support in pypost editors mixed two concerns in one helper class: finding which
`{{...}}` token is under the cursor, and resolving tokens to preview values. Separating
these makes the code easier to maintain and clarifies which path each widget uses.

## User Stories

- As a maintainer, I want token lookup and value resolution in distinct components, so I can
  change hover preview logic without touching cursor-index scanning.
- As a maintainer, I want table hover (full-cell resolve) and line-edit hover (cursor lookup)
  to call the appropriate component explicitly.
- As a developer extending hover widgets, I want existing `VariableHoverHelper` imports to keep
  working during the transition.

## Definition of Done

- `VariableHoverLocator` owns cursor-index token discovery.
- `VariableHoverResolver` owns preview value resolution (plain chains + `TemplateService`).
- `VariableHoverHelper` remains a thin facade for backward compatibility.
- Call sites updated where clarity improves (`VariableHoverMixin`, table widget, metrics).
- Existing hover tests pass; new tests cover the split classes.
- Developer docs describe the two responsibilities.

## Task Description

**Problem:** `VariableHoverHelper` combined index lookup (text fields) and full-string
resolution (tables) in one class, obscuring responsibilities and suggesting duplicated
substitution logic.

**Scope:** Refactor within `pypost/ui/widgets/mixins.py`; update direct call sites; tests and
dev docs.

**Out of scope:** Moving resolution into `EnvironmentService`; changing hover behaviour or
regex contracts.

**Constraints:**

- Implementation language: **Python**.
- No user-visible behaviour change.
- Preserve `VariableHoverHelper` public API for tests and external callers.

## Main entities (business view)

- **Hover locator** — finds the placeholder under the mouse cursor.
- **Hover resolver** — turns a placeholder (or cell text) into the tooltip preview value.
- **Variable-aware widget** — editor or table that shows hover tooltips.

## Q&A

- **Q:** Why not move resolution to `TemplateService` only?
  **A:** Plain `{{name}}` chains and hidden-key masking are hover-specific; expressions already
  delegate to `TemplateService`. Splitting locator vs resolver addresses the stated debt without
  a larger service extraction.
