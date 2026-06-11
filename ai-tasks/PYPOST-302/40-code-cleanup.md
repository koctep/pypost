# PYPOST-302: Code Cleanup

## Static Analysis

- No new linter warnings in `tab_header.py`, `tabs_presenter.py`, or tests.
- Removed unused imports (`QPushButton`, `QTabBar`) from `tabs_presenter.py`.

## Formatting

- All files comply with 100-character line limit.
- Trailing whitespace removed; final newlines present.

## Dead Code Removed

- Deleted from `TabsPresenter`: `_install_plus_tab`, `_on_tab_bar_clicked`, `_plus_tab_index`,
  `_is_plus_tab_index`, `_navigable_tab_indices`, and local plus-tab constants.

## Tests

- `tests/test_tab_header.py` added with module `pytestmark`.
- Existing `tests/test_tabs_presenter.py` plus-tab and rename tests retained.

## Verification

Run:

```bash
python -m pytest tests/test_tab_header.py tests/test_tabs_presenter.py -v
```
