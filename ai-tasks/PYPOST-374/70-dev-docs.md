# PYPOST-374: Dev Docs

## Updates

| File | Change |
| --- | --- |
| `doc/dev/solid_audit.md` | Added **Individual dialog audit (PYPOST-374)** section |
| `doc/dev/testing.md` | Added **Dialog audit inventory (PYPOST-374)** section |

## Key Points for Maintainers

- Full report: `ai-tasks/PYPOST-374/30-dialogs-audit-report.md`
- Inventory script: `scripts/audit_dialogs_inventory.py`
- CI guard: `tests/test_dialogs_audit.py`

## Regenerate Inventory

```bash
.venv/bin/python scripts/audit_dialogs_inventory.py --markdown
```

## Verify Audit Coverage

```bash
.venv/bin/python scripts/audit_dialogs_inventory.py --check
pytest tests/test_dialogs_audit.py -v
```

## Adding a New Dialog

1. Implement under `pypost/ui/dialogs/`.
2. Add a per-dialog section to `30-dialogs-audit-report.md` (or run a follow-up audit task).
3. Ensure `tests/test_dialogs_audit.py` passes (`--check` lists every module filename in report).
