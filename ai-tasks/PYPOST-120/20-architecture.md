# PYPOST-120: Architecture — line-scoped hover scan

Implemented in PYPOST-122; verified for PYPOST-120.

| File | Change |
| ---- | ------ |
| `pypost/ui/widgets/mixins.py` | `_hover_line_scoped_scan`, `_slice_line_at_index`, `_prepare_hover_scan_context` |
| `pypost/ui/widgets/variable_aware_widgets.py` | `_hover_line_scoped_scan = True` on `VariableAwarePlainTextEdit` |
| `tests/test_variable_hover.py` | Slice and deep-line hover tests |

`VariableAwareLineEdit` keeps full-text scan (single line). Table hover path unaffected.
