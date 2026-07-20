# PYPOST-821: Dev Docs Update

## Changes

Updated `doc/dev/ui_font_and_styles.md`:

- Regression coverage bullet now includes the PYPOST-821 dark-theme `close.svg`
  stroke/path smoke check.
- Troubleshooting row for dark-mode close visibility points at
  `test_default_close_icon_dark_theme_contrast_contract`.
- Local verify note updated from seven to eight tests in
  `tests/test_tab_layout_regression.py`.

## Validation

- [x] Docs match the new test and PYPOST-796 `#999999` contract
- [x] Rationale for static vs pixel contrast lives in the test docstring and architecture
  artifact
- [x] No new standalone doc file required — existing tab/styles page is the right home
