# PYPOST-250 Requirements — VariableHoverMixin type hinting

## Goals

Improve static analysis and maintainability of the variable-hover UI mixin so
developers and tooling can reason about `self` as a `QWidget` without suppressing
type errors. This closes tech debt tracked from PYPOST-29.

## User Stories

- As a **maintainer**, I want `VariableHoverMixin` to express that host widgets are
  `QWidget` subclasses so IDEs and type checkers surface real mistakes.
- As a **contributor**, I want hover mixin code free of `type: ignore` so reviews
  focus on behaviour, not suppressed warnings.

## Definition of Done

| ID | Criterion | Verification |
|----|-----------|--------------|
| AC-1 | No `type: ignore` on mixin QWidget calls | `rg "type: ignore" pypost/ui/widgets/mixins.py` → no matches in `VariableHoverMixin` |
| AC-2 | Mixin methods annotate `self` as a QWidget host | Code review of `mixins.py` |
| AC-3 | Runtime behaviour unchanged | `pytest tests/test_variable_hover.py -q` passes |
| AC-4 | Existing consumers compile unchanged | No signature changes to public mixin API |

## Task Description

`VariableHoverMixin` is used via multiple inheritance with `QLineEdit`,
`QPlainTextEdit`, and test doubles. It calls `setMouseTracking`, `super().mouseMoveEvent`,
and passes `self` to `QToolTip.showText`, but inherits implicitly from `object`.
Static analyzers cannot verify those calls; `type: ignore` comments were added as a
workaround.

**Constraints**: No behavioural change to tooltips or mouse tracking. Minimal diff.
**Out of scope**: Typing `VariableAwareTableWidget` (separate class); broader UI typing
sweep.

## Q&A

- **Q**: Why not inherit from `QWidget`?  
  **A**: Mixins must not sit ahead of the concrete widget in MRO; generic self-typing
  preserves the existing inheritance order.
