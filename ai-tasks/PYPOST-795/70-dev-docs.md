# PYPOST-795: Developer Documentation

## Summary

Documented the **keep** decision for `PyPostStyle.set_close_button_size` with explicit
when-to-use, when-not-to-use, and a test-only example. Expanded the method docstring in
`custom_style.py`.

## Files Updated

| File | Change |
| --- | --- |
| `doc/dev/ui_font_and_styles.md` | PYPOST-795 API section, Related link, header tasks |
| `pypost/ui/styles/custom_style.py` | Richer `set_close_button_size` docstring |

## Documentation Highlights

### Decision

Keep as opt-in override — no production caller after PYPOST-792; removal would discard a
deliberate escape hatch without simplifying production paths.

### Policy

- **Default:** `close_button_size = None` → native `PM_TabCloseIndicator*`.
- **Do not** call at startup or from `StyleManager.apply_theme`.
- **Do** call only for platform fixes, accessibility hit targets, or tests.

### Cross-references

- Close-indicator policy: same doc, "PyPostStyle and close-indicator metrics"
- Troubleshooting: tab overlap symptom row
- Tests: `tests/test_tab_layout_regression.py`

## Verification

- Doc matches `custom_style.py` implementation.
- Existing tab layout regression tests remain authoritative.
