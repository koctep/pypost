# PYPOST-954: Code Cleanup

## Changes

- Removed duplicated local `_read` from both packaging doc-lock modules.
- Centralized `assert_substring` / `assert_any_substring` / `doc_label` in
  `tests/helpers/packaging_doc_lock.py`.
- Added import contract test (mirrors PYPOST-928 CI helper pattern).

## Verification

- [x] `read_lints` clean on touched test modules and helper
- [x] No production code changes
- [x] Locked doc tokens unchanged (918 / 922 semantics preserved)

## Tests

- [x] All tests passed — focused packaging lock suite (14 passed)

```bash
make test PYTEST_ARGS='tests/test_ui_actions_mcp_packaging_doc.py tests/test_packaging_doc_lock_helper.py tests/test_agent_e2e_broader_packaging_doc.py -v'
```

## Notes

- Full `make check` not re-run — test-only / doc-only surface.
