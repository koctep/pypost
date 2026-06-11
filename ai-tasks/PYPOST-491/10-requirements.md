# PYPOST-491: Extract HIDDEN_MASK to shared constants module

## Goals

PYPOST-448 introduced `HiddenToggleLogPolicy` in the core layer, which reused the UI mask
constant `HIDDEN_MASK` from `pypost/ui/widgets/mixins.py`. That created an improper
core → UI dependency for a single shared string value.

This task removes the layer violation by defining `HIDDEN_MASK` once in a shared core module
and updating all consumers. Behavior and the mask token (`********`) must remain unchanged.

## Programming Language

Python 3.10+

## User Stories

- As a **maintainer**, I want hidden-value masking to use one shared constant so core logging
  policy does not depend on UI widget mixins.
- As a **developer**, I want UI surfaces (environment manager, hover previews) and log
  redaction to stay visually and semantically aligned via the same constant.
- As a **reviewer**, I want the PYPOST-448 technical-debt item for the core → UI import to
  be resolved without changing product behavior.

## Definition of Done

1. `HIDDEN_MASK` is defined in `pypost/core/constants.py` (or equivalent shared core module).
2. `HiddenToggleLogPolicy` imports the constant from the shared module, not from UI mixins.
3. `pypost/ui/widgets/mixins.py` and `pypost/ui/dialogs/env_dialog.py` import from the shared
   module.
4. Existing tests pass without behavior change; mask value remains `********`.
5. No remaining production import of `HIDDEN_MASK` from `pypost.ui.widgets.mixins`.

## Out of Scope

- Changing the mask string or unifying with `SensitiveDataMaskingPolicy.HIDDEN_PLACEHOLDER`
  (`***` in request history — different surface).
- New logging, metrics, or user-facing features.

## Acceptance Criteria

| Criterion | Verification |
| --- | --- |
| Shared constant location | `pypost/core/constants.py` exports `HIDDEN_MASK` |
| Core policy decoupled | `hidden_toggle_log_policy.py` imports from `pypost.core.constants` |
| UI consumers updated | mixins and env dialog import from shared module |
| Tests green | Related unit and e2e tests pass |
| No regression | Mask display and toggle log redaction unchanged |

## Traceability

- Source: [PYPOST-448 technical-debt analysis](ai-tasks/PYPOST-448/60-tech-debt.md)
- Labels: PYPOST-448, refactoring, tech-debt
