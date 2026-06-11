# PYPOST-180: Code Cleanup (Step 4)

## Actions

- New modules follow project conventions: UTF-8, LF, max 100 columns, English comments.
- Explicit `pytestmark = pytest.mark.timeout(30)` on test module per `do-testing.md`.
- Reused existing overview/contract helpers instead of duplicating tool-name logic.
- No linter issues introduced in new files.

## Verification

```bash
.venv/bin/python -m pytest tests/test_mcp_test_collection.py -v
```
