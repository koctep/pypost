# PYPOST-70: Code Cleanup

## Summary

Single-purpose rename; no lint or format issues introduced.

## Checklist

| Item | Status |
|------|--------|
| Renamed shadowing `layout` attribute | Done |
| Private name `_content_layout` follows Qt/Python convention | Done |
| Regression test added | Done |
| Line length ≤ 100 | Done |
| No unused imports | Done |

## Notes

- `QVBoxLayout(self)` constructor registration unchanged — Qt ownership intact.
