# PYPOST-796: Developer Documentation

## Summary

Updated `doc/dev/ui_font_and_styles.md` to document the default tab close icon stroke colour change
(`#999999`, PYPOST-796) and revised the dark-mode troubleshooting row to reflect the fix.

## Files Updated

| File | Change |
| --- | --- |
| `doc/dev/ui_font_and_styles.md` | Close-icon colour note under `PyPostStyle` section; troubleshooting table row for dark-mode visibility |

## Documentation Highlights

### Default vs hover icons

- **`close.svg`** — `#999999` stroke, no background; default state on tab close buttons.
- **`close-hover.svg`** — `#333333` stroke on `#E0E0E0` pill; hover state unchanged.

### Unchanged policy

- QSS applies icons via `QTabBar::close-button` only (no `::tab` box-model rules — PYPOST-792).
- Close-indicator size comes from native `PM_TabCloseIndicator*` metrics via `PyPostStyle`.

## Verification

- Doc matches `pypost/ui/resources/icons/close.svg` and `main.qss` wiring.
- Tab layout regression tests continue to guard QSS/metrics policy.

## Worklog

role: execution, step: 7, step_name: Dev Docs, tokens_used: 1200
