# PYPOST-374: Code Cleanup

## Application code

No production dialog code changed. Analysis-only audit plus inventory tooling.

## New files

| File | Checks |
| --- | --- |
| `scripts/audit_dialogs_inventory.py` | `scripts/lint.sh`, line length ≤100 |
| `tests/test_dialogs_audit.py` | `pytestmark = pytest.mark.timeout(30)` |

## Documentation

- All `ai-tasks/PYPOST-374/*.md` artifacts: UTF-8, LF, trailing whitespace removed, final newline.
- Audit report line length kept ≤100 where practical.

## Verification

```bash
scripts/lint.sh scripts/audit_dialogs_inventory.py tests/test_dialogs_audit.py
pytest tests/test_dialogs_audit.py -v
.venv/bin/python scripts/audit_dialogs_inventory.py --check
```
