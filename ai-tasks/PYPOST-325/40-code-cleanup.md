# PYPOST-325: Code Cleanup

## Lint and format

- No production code changes in this task.
- Existing test modules follow project conventions (100-char line limit, unittest).

## Validation

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m unittest \
  tests.test_collection_tree_delete_confirmation \
  tests.test_collection_tree_delete_metrics -v
```

Result: 10 tests, all passed.

## Notes

- Test helpers overlap between confirmation and metrics modules; acceptable until a
  third delete-test module appears (see PYPOST-339 tech-debt).
