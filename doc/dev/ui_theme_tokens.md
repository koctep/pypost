# Shared UI Theme Tokens

## Overview

`pypost.ui.styles.ui_tokens` is the shared source for validation presentation colors and
autocomplete popup geometry. It keeps request editors, header tables, and body editors visually
consistent.

## Architecture

- `ui_tokens.py` defines default `QColor` values and popup dimensions.
- `ui_tokens.qss` styles named validation banners and autocomplete popups.
- `StyleManager` substitutes centralized validation color values while loading QSS.
- Validation and autocomplete widgets import the same tokens.

## API / Usage

Use the constants when adding a validation or autocomplete surface:

```python
from pypost.ui.styles.ui_tokens import AUTOCOMPLETE_POPUP_MIN_WIDTH
```

Popup dimensions are applied with the widget's `resize()` call. Validation extra selections use
the shared `QColor` values. The validation banner uses the `validationErrorBanner` object name.

## Configuration

There are no environment variables or runtime settings. To change the default validation palette,
update `ui_tokens.py`; `StyleManager` injects those values into the QSS stylesheet.

## Troubleshooting

- If a validation banner is unstyled, confirm the application stylesheet was applied by
  `StyleManager.apply_styles()` and that the label object name is `validationErrorBanner`.
- If a popup has unexpected dimensions, check that its resize path uses the constants from
  `ui_tokens.py` rather than local numeric literals.

