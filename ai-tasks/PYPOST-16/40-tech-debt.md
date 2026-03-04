# PYPOST-16: Technical Debt Analysis

## Status: FIXED
Addressed in PYPOST-32 by implementing `VariableHoverMixin`.

## Shortcuts Taken

- **Variable Parsing Logic**: A simple regex `\{\{([a-zA-Z0-9_]+)\}\}` is used to find
  variables. This works for most cases but might give false positives inside string literals if they
  accidentally contain such a pattern, or not support complex expressions (if planned in future).
- **Hardcoded Colors/Styles**: Tooltip styling is standard for now. Customization via QSS might be
  needed in future.
- **Single Level Resolution**: Variable resolution happens only one level deep. If a variable refers
  to another variable (`VAR_A = {{VAR_B}}`), this is not handled recursively for tooltip (although
  `TemplateEngine` might support it).

## Code Quality Issues

- **[FIXED] Duplication of Logic**: Variable search logic (`find_variable_at_index`) was moved to a helper
  but duplicated in `mouseMoveEvent`. Now `VariableHoverMixin` is used in `pypost/ui/widgets/mixins.py`.
- **Direct Variable Injection**: The `set_variables` method injects dictionary directly. Perhaps using
  `Property` or signal-slot mechanism for more reactive update would be better, but sufficient for
  current goals.

## Missing Tests

- **Unit Tests**: Unit tests for `VariableHoverHelper` and widgets are missing. Need to add tests to verify correctness of variable detection in string and text.
- **UI Tests**: No automatic UI tests checking tooltip appearance on mouse hover.

## Performance Concerns

- **MouseMoveEvent**: `mouseMoveEvent` processing happens frequently. Current implementation (regex search) is fast enough for small strings (URL) and visible text area, but with very large text volumes in Body and many variables, ensure `find_variable_at_index` is not called too often or doesn't scan entire text every time (currently scans entire widget text `QLineEdit` and `toPlainText` for `QPlainTextEdit`).
- *Mitigation*: For `QPlainTextEdit`, optimize search by scanning only current line or visible block, not entire `toPlainText()`. Currently entire text is taken for simplicity, which might be slow for large JSONs.

## Follow-up Tasks

- [ ] Write unit tests for `VariableHoverHelper`.
- [ ] Optimize `VariableAwarePlainTextEdit` for large documents (scan only line under cursor).
- [ ] Add support for recursive variable resolution in tooltips.
- [ ] Implement variable highlighting in `JsonHighlighter` (PYPOST-XX).
