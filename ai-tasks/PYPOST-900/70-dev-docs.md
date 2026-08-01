# PYPOST-900: Dev Docs Update

## Files Updated

| File | Change |
| --- | --- |
| `doc/dev/testing.md` | Added fixture-drive helper paragraph under GUI/helpers section |
| `doc/dev/agent_e2e.md` | Noted packaging unit tests use `fixture_drive` helper |

## Cross-Links

- Helper module: `tests/helpers/fixture_drive.py`
- Unit proof: `tests/test_fixture_drive_helper.py`
- Consumer: `tests/test_agent_e2e_packaging_logs.py`
- Agent rules mirror: `.cursor/lsr/do-testing.md` (no rule change required)

## Validation

- [x] Doc paths match repo layout
- [x] PYPOST-900 Jira ID referenced where appropriate
- [x] No user-facing doc changes (dev docs only)
