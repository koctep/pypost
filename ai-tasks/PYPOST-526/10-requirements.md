# PYPOST-526: Unify encryption migration inventory API

## Goals

Remove confusion from the unused `build_inventory(check_decrypt=True)` design. Operators and
maintainers need a single inventory path and a separate verify path for decrypt validation.

## Definition of Done

- `verify_decrypt_access()` uses `build_inventory()` for inventory (no duplicate scan logic).
- No `check_decrypt` parameter on `build_inventory()` (already absent from code).
- Developer docs state inventory vs verify responsibilities clearly.
- Tests confirm verify delegates to `build_inventory()`.

Approved via sprint-task-runner autonomous mode (2026-06-11).
