# PYPOST-116: Direct variable injection via set_variables

## Goals

Environment variables power `{{placeholder}}` tooltips and template rendering across request
editor widgets. Today values reach widgets through explicit `set_variables(dict)` calls
rather than per-widget Qt signals. The pattern works but is undocumented, which makes new
UI contributors unsure whether to add signals or follow the existing push chain.

This debt item from PYPOST-13 asks to either document the intentional design or adopt a
small reactive improvement if one fits without a large refactor.

## User Stories

- As a pypost maintainer, I want a documented variable propagation contract so I know where
  to wire new variable-aware widgets.
- As a contributor adding a request editor field, I want clear guidance on implementing
  `set_variables` instead of inventing parallel signal plumbing.

## Definition of Done

| ID | Criterion |
|----|-----------|
| AC-1 | Developer docs describe the presenter signal → push `set_variables` → widget storage flow |
| AC-2 | Docs explain why widgets store a dict snapshot (hover reads on demand) vs per-field signals |
| AC-3 | Entry-point methods (`on_env_variables_changed`, `RequestWidget.set_variables`,
  `VariableHoverMixin.set_variables`) have docstrings referencing the pattern |
| AC-4 | Tests assert env variable changes propagate into at least one child widget |
| AC-5 | Existing variable hover and tabs presenter tests pass |

## Scope

**In scope:** Documentation, docstrings, test strengthening for propagation contract.

**Out of scope:** Replacing push propagation with global `Property`/observer bus (tracked as
PYPOST-128), per-widget `variables_changed` signals, DI container.

## Constraints

- No behavioural change to tooltip or template rendering.
- Keep presenter-level `env_variables_changed` signal as the single reactive entry point.

## Programming language

Python (tests and docstrings); Markdown (developer docs).
