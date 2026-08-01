# PYPOST-921: Dev Docs

## Updates

- [x] `doc/dev/agent_golden_e2e.md` — plus-tab create scenario when restore
  leaves no blank tab; `PLUS_TAB_BUTTON`; strip/`deleteLater` note;
  current-tab scoped settle
- [x] `doc/dev/ui_identity.md` — catalog row for `PLUS_TAB_BUTTON`
- [x] `doc/dev/request_actions.md` — plus button stable id for agents

## Verification

- [x] Docs describe blank-restore vs plus-tab create fallback
- [x] Run command for plus-tab golden remains under `make test-agent-e2e` /
  module `PYTEST_ARGS`
