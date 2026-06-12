# PYPOST-128: Manual variable propagation in RequestWidget

## Goals

PYPOST-116 documented the intentional presenter-driven `set_variables` push chain. This
follow-up addresses the remaining debt from PYPOST-15: manual fan-out inside
`RequestWidget` is repetitive and easy to forget when new variable-aware editors are added.

The business goal is maintainability — contributors should add new request-editor fields
without re-copying the same four-line loop or risking a missed child widget.

## User Stories

- As a maintainer extending the request editor, I want a single registry of
  variable-aware children so I only update one place when adding a new field.
- As a reviewer, I want the propagation contract from PYPOST-116 preserved without a
  large DI or global-context refactor.

## Definition of Done

| ID | Criterion |
|----|-----------|
| AC-1 | `RequestWidget` fans out variables via a declared target list, not ad-hoc repeated calls |
| AC-2 | Shared helper documents and implements optional-method duck typing for composites |
| AC-3 | Tests assert `set_variables` reaches URL, params, headers, and body editors |
| AC-4 | `doc/dev/variable_propagation.md` describes the composite fan-out pattern |
| AC-5 | Existing tabs presenter and variable hover tests pass |

## Scope

**In scope:** Small refactor of `RequestWidget` fan-out; helper in UI mixins; tests; docs.

**Out of scope:** Global variable context, DI container, per-widget reactive signals
(deferred unless UI depth warrants — see PYPOST-116 rationale).

## Constraints

- No change to presenter signal boundary or tooltip/template behaviour.
- Keep push-based snapshots; widgets still do not subscribe to env signals directly.

## Programming language

Python; Markdown developer docs.
