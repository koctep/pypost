# PYPOST-692: Developer Documentation

## Overview

Moved `StyleManager` from `pypost/core/style_manager.py` to `pypost/ui/styles/style_manager.py`
to eliminate the only confirmed runtime core → ui import (audit finding R-P1-001 / D-001 /
L-004). User-visible appearance behavior is unchanged.

## Documentation Updates

| File | Change |
| --- | --- |
| `doc/dev/architecture.md` | Removed `style_manager.py` from core tree; removed known-exception note |
| `doc/dev/architecture_audit.md` | Marked R-P1-001 remediated; updated executive summary and findings |
| `doc/dev/ui_font_and_styles.md` | Added module path note under Architecture |

## Module Location

```python
from pypost.ui.styles.style_manager import StyleManager
```

`MainWindow` still constructs `StyleManager()` and calls `apply_theme` / `apply_styles` from
`apply_settings` — no wiring changes.

## Boundary Verification

After remediation, no `pypost/core/` module imports `pypost.ui` at runtime for appearance.
(`request_sync.py` retains a `TYPE_CHECKING`-only UI import — unchanged, out of scope.)

## Troubleshooting

If theme or QSS tests fail after import refactors, confirm tests import from
`pypost.ui.styles.style_manager`, not the removed `pypost.core.style_manager` path.
