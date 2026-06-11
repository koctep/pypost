# PYPOST-492: Code Cleanup

## Changes reviewed

- `SECTION_HEADER_STYLE` and `_make_section_header()` extracted at module level — keeps
  `__init__` readable; single style constant avoids inline duplication.
- No unused imports; `QLabel` already imported.
- Line lengths within 100 characters.
- No dead code removed elsewhere.

## Lint / format

- Targeted pytest on `tests/test_settings_dialog.py` — no linter issues in touched files.

## Summary

Layout-only refactor; no API or persistence surface changes.
