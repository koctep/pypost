# PYPOST-795: Code Cleanup

## Summary

Documentation-only task. No structural cleanup required beyond expanded docstrings.

## Checklist

- [x] No dead production code introduced or left behind
- [x] `set_close_button_size` docstring documents opt-in policy and anti-patterns
- [x] No unused imports or formatting drift in touched files
- [x] Line length within project limits

## Notes

- `close_button_size` attribute and `pixelMetric` override remain — intentional, not dead code.
- No removal of `set_close_button_size` — evaluated and kept per architecture decision.
