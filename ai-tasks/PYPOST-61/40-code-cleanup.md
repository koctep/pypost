# PYPOST-61: Code Cleanup

## Summary

Single-line import move; no lint or format issues introduced.

## Checklist

| Item | Status |
|------|--------|
| `QTabWidget` in alphabetical QtWidgets import tuple | Done |
| Removed deferred import from `_build_layout` | Done |
| Line length ≤ 100 | Done |
| No unused imports | Done |

## Notes

- Import order follows existing `PySide6.QtWidgets` grouped import style.
