# Developer Documentation: PYPOST-114 — Variable tooltip QSS hook

**Ticket**: PYPOST-114
**Date**: 2026-06-12

---

## Overview

Variable hover tooltips now pick up global `QToolTip` styling from `main.qss`. Theme authors
can customize colors without editing Python.

---

## Documentation Updated

| File | Change |
| --- | --- |
| `doc/dev/ui_mixins.md` | Tooltip styling section with QSS hook |
| `doc/dev/ui_font_and_styles.md` | Cross-link to tooltip QSS rules |

---

## Maintainer Notes

- Edit `pypost/ui/styles/main.qss` → `QToolTip { ... }` block.
- Use `palette(tooltip-text)`, `palette(tooltip-base)`, etc., to stay theme-aware.
- Applies to all tooltips (`setToolTip` and `QToolTip.showText`).

---

## Related

- PYPOST-13 — variable hover tooltips
- `tests/test_style_manager_font.py` — `test_load_styles_includes_tooltip_qss`
