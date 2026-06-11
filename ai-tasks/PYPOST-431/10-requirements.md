# PYPOST-431 Requirements — Migrate VariableHoverMixin off globalPos()

## 1. Problem Statement

PySide6 (Qt 6) deprecates `QMouseEvent.globalPos()` in favour of
`QMouseEvent.globalPosition()`.  `VariableHoverMixin._show_or_hide_tooltip` and
`VariableAwareTableWidget.mouseMoveEvent` call `event.globalPos()` when positioning
tooltips via `QToolTip.showText`, which emits `DeprecationWarning` during pytest runs
(e.g. `tests/test_variable_hover.py`).

## 2. Scope

| In scope | Out of scope |
|----------|--------------|
| Replace `globalPos()` with `globalPosition().toPoint()` in mixin and table hover paths | Migrating `event.pos()` to `position().toPoint()` (separate hygiene) |
| Keep tooltip behaviour unchanged | Refactoring hover architecture |
| Verify hover tests pass without new warning filters | Adding new hover features |

## 3. Functional Requirements

### FR-1 — Non-deprecated global coordinates

All `QToolTip.showText` calls in the variable-hover code path must use
`event.globalPosition().toPoint()` instead of `event.globalPos()`.

### FR-2 — Behaviour parity

Tooltip text and show/hide logic must remain identical for:
- `VariableAwareLineEdit`
- `VariableAwarePlainTextEdit`
- `VariableAwareTableWidget`

### FR-3 — Tests green

Existing tests in `tests/test_variable_hover.py` must pass without adding
`pytest.warns` filters or `filterwarnings` entries for this deprecation.

## 4. Acceptance Criteria

| ID | Criterion | Verification |
|----|-----------|--------------|
| AC-1 | No `globalPos()` in `pypost/ui/widgets/mixins.py` | `rg globalPos pypost/ui/widgets/mixins.py` → no matches |
| AC-2 | No `globalPos()` in table hover path | `rg globalPos pypost/ui/widgets/variable_aware_widgets.py` → no matches |
| AC-3 | Hover tests pass | `pytest tests/test_variable_hover.py -q` → all pass |
| AC-4 | No `globalPos` DeprecationWarning from production code | pytest hover suite without extra filters |

## 5. References

- Sprint 134 Wave 2: VariableHoverHelper (PYPOST-130/131/133)
- Prior tracking: `doc/dev/tech-debt/PYPOST-434.md` §2, sprint report TD-6
