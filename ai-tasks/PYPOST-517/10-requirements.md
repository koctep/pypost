# PYPOST-517: Add unit tests for body editor fold remapping after edits

## Goals

PYPOST-511 remaps collapsed `region_id` values after debounced re-scan when region boundaries
are unchanged. Unit tests must lock in that behaviour so edits inside or outside collapsed spans
do not silently break fold state.

## Definition of Done

- Test: collapse region, edit outside span, collapse preserved when boundaries match.
- Test: collapse dropped when edit changes region start/end blocks.
- Test: nested collapse remapping after sibling paste and bracket edits inside region.
- All tests pass.

## Programming language

Python (unittest, PySide6).
