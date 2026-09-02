# PYPOST-1245: Centralize UI theme tokens

## Research

The existing Qt UI keeps validation colors in `ValidationController` and
`VariableAwareTableWidget`, while popup dimensions are repeated by the shared autocomplete
editor, the legacy compatibility editor, and `CodeEditor`. The application already loads all
QSS files through `StyleManager`, and QSS palette roles are appropriate for theme-dependent
colors.

## Implementation Plan

1. Add a small Python token module containing immutable validation color values and popup
   geometry values.
2. Replace duplicated literals in validation and autocomplete widgets with those tokens.
3. Add a QSS file for validation feedback and autocomplete popup selectors using palette roles,
   loaded by the existing style manager.
4. Add focused tests proving the token contract and unchanged default geometry/color behavior.

**Mandatory — Failing Repro (next Step 3):** Add `tests/test_ui_theme_tokens_repro.py` with
tests that import the planned token module, assert the shared values, and inspect affected
widget source behavior through Qt widget construction. It must fail before the module and
stylesheet integration exist, without live external dependencies.

## Architecture

```text
ui_tokens.py ──> validation_controller.py
       ├───────> variable_aware_widgets.py
       └───────> variable_autocomplete_line_edit.py

ui_tokens.py + ui_tokens.qss ──> StyleManager ──> QApplication stylesheet
```

The token module owns stable defaults and geometry constants. Runtime palette adaptation stays
in Qt: validation labels, validation marks, and popup widgets receive object names and are styled
through QSS palette roles. Existing widget behavior, compatibility classes, and public APIs stay
unchanged. The shared popup dimensions are used for all completion popup variants.

## Q&A

- Does this change validation semantics? No; it only centralizes presentation values.
- Does it redesign themes? No; it adds selectors and defaults that preserve current appearance.

