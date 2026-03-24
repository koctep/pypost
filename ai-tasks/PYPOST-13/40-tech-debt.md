# PYPOST-13: Technical Debt Analysis


## Status: FIXED
Addressed in PYPOST-14 by implementing `VariableHoverMixin`.

## Shortcuts Taken

- **Variable regex scope** ([PYPOST-113](https://pypost.atlassian.net/browse/PYPOST-113)):
  A simple regex `\{\{([a-zA-Z0-9_]+)\}\}` finds variables. It can false-positive inside string
  literals and does not cover complex expressions if those are added later.
- **Default tooltip styling** ([PYPOST-114](https://pypost.atlassian.net/browse/PYPOST-114)):
  Styling is standard QSS for now; customization may be needed later.
- **One-level tooltip vars** ([PYPOST-115](https://pypost.atlassian.net/browse/PYPOST-115)):
  Resolution is one level deep. Chains like `VAR_A = {{VAR_B}}` are not expanded recursively in
  tooltips (though `TemplateEngine` may handle them elsewhere).

## Code Quality Issues

- **[FIXED] Duplication**: Variable search used `find_variable_at_index` in a helper and again in
  `mouseMoveEvent`. Replaced with `VariableHoverMixin` in `pypost/ui/widgets/mixins.py`.
- **Direct variable injection** ([PYPOST-116](https://pypost.atlassian.net/browse/PYPOST-116)):
  `set_variables` injects a dict directly; `Property` or signals could make updates more reactive
  but current scope is sufficient.

## Missing Tests

- **VariableHoverHelper tests** ([PYPOST-117](https://pypost.atlassian.net/browse/PYPOST-117)):
  Unit tests are missing for variable detection in strings and text fields.
- **Tooltip UI** ([PYPOST-118](https://pypost.atlassian.net/browse/PYPOST-118)):
  No automated UI tests for tooltip appearance on hover.

## Performance Concerns

- **Mouse move + regex** ([PYPOST-119](https://pypost.atlassian.net/browse/PYPOST-119)):
  `mouseMoveEvent` runs often; regex over full `QLineEdit` / `QPlainTextEdit` text is fine for small
  content but may matter for very large body text and many variables.
- **Mitigation: scan less text** ([PYPOST-120](https://pypost.atlassian.net/browse/PYPOST-120)):
  For `QPlainTextEdit`, scan only the current line or visible block instead of full `toPlainText()`
  (today the whole buffer is scanned for simplicity).

## Follow-up Tasks

- Write unit tests for `VariableHoverHelper`.
  — [PYPOST-121](https://pypost.atlassian.net/browse/PYPOST-121)
- Optimize `VariableAwarePlainTextEdit` for large documents (scan only line under cursor).
  — [PYPOST-122](https://pypost.atlassian.net/browse/PYPOST-122)
- Add support for recursive variable resolution in tooltips.
  — [PYPOST-123](https://pypost.atlassian.net/browse/PYPOST-123)
- Implement variable highlighting in `JsonHighlighter`.
  — [PYPOST-124](https://pypost.atlassian.net/browse/PYPOST-124)
