# PYPOST-1427: Code Cleanup

## Actions Performed

- [x] Audited `pypost/ui/models/collection_variables_table_model.py` and
  `tests/test_collection_variables_paged_model_repro.py` for line length ≤ 100,
  unused imports, dead code, and debug prints.
- [x] Confirmed no temporary `print` / commented-out production paths in the
  paged model change.
- [x] Ran `make lint` successfully (flake8 on `pypost/`, test-lint baseline,
  markdown / relative-link checks).
- [x] Verified every new test uses module `pytestmark = [pytest.mark.timeout(60)]`
  plus per-test `@pytest.mark.timeout(...)` overrides (do-testing contract).
- [x] Related suites green:
  - `tests/test_collection_variables_paged_model_repro.py`
  - `tests/test_variable_import_virtualization_repro.py`
  - `tests/test_import_collection_variables_module_extract_repro.py`

## Notes

- Dense `_records` list removed in favor of LRU `_chunk_cache`; public model
  APIs unchanged for dialog / delegate / view callers.
