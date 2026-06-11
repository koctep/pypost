# PYPOST-457: Code Cleanup

## Scope

Tests and documentation only. No production modules changed.

## Checks

- [x] `./scripts/check-line-length.sh` — no violations in changed files
- [x] Test names follow existing `test_*` conventions in target modules
- [x] Docstrings on new tests state the parity invariant clearly
- [x] No unused imports or dead code introduced

## Notes

- `test_template_service.py` accesses `_function_registry` (private) — consistent with
  needing the catalog reference after init; no public registry accessor exists yet.
- Parity assertion duplicated in two test modules by design: unit (registry) and integration
  (TemplateService init path).

## No Further Cleanup Required

Change set is minimal and ready for review.
