# PYPOST-106: Code Cleanup

## Static analysis

- `make lint` (flake8 on `pypost/`): no new issues in changed files.

## Formatting

- Line length ≤ 100 characters maintained.
- No trailing whitespace; UTF-8 LF endings.

## Cleanup actions

- Removed 12-line manual `setFont` loop and menu-bar special case from `main_window.py`.
- Added typed optional `font_size` parameter to `StyleManager.apply_styles`.
- Updated test mocks to accept `font_size` keyword in `apply_styles` side effects.

## Tests

- `make test` — full suite run after changes (see Step 3).
