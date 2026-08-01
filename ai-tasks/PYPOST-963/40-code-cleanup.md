# PYPOST-963: Code Cleanup

## Validation

- [x] `make test PYTEST_ARGS='tests/test_makefile_install_seed_contract.py -v'` — green
- [x] Policy constant co-located with `_seed_installable_package`
- [x] No duplicate policy literals elsewhere
- [x] Line length ≤ 100 in changed files

## Notes

Small, focused diff: one constant, one test, doc section. No refactors to seed assembly
(PYPOST-965 deferred).
