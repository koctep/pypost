# PYPOST-64: Architecture — flexible detail pane heights

## Scope

`HistoryPanel._build_ui()` in `pypost/ui/widgets/history_panel.py` only.

## Layout changes

1. Remove `setFixedHeight(60)` and `setFixedHeight(80)` from `_detail_headers` and
   `_detail_body`.
2. Set vertical `QSizePolicy.Expanding` on both `QTextEdit` widgets.
3. Set `minimumHeight` from `fontMetrics().lineSpacing()` (×3 headers, ×4 body).
4. Set `QFormLayout.ExpandingFieldsGrow` on the detail form so expanding fields absorb
   extra space in the lower splitter pane.
5. Set `QSplitter` stretch factors (list 2, detail 1) so the list keeps more default
   space while detail remains resizable.

## Testing

- `tests/test_history_panel.py::test_detail_fields_use_expanding_layout`: assert
  Expanding vertical policy, positive minimum height, and no fixed maximum.

## Observability

No new log events.
