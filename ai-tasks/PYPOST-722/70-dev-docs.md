# PYPOST-722: Developer Documentation

## Overview

Isolates Qt global style/stylesheet state in the style manager theme tests to prevent order-dependence issues.

## Architecture

No production code changes were made. In `tests/test_style_manager_theme.py`, the `qapp` fixture was updated to:
- Back up `app.style()`, `app.palette()`, and `app.styleSheet()`.
- Clear the global stylesheet (`app.setStyleSheet("")`) to avoid wrapping of style object in a `QStyleSheetStyle`.
- On teardown, restore the global style, palette, and stylesheet.
- If restoring the style object fails with a `RuntimeError` (due to C++ side deletion by Qt), fall back to instantiating and applying `PyPostStyle`.

## API / Usage

Run tests:
```bash
pytest tests/test_style_manager_theme.py -v
```

## Configuration

None.

## Troubleshooting

None.
