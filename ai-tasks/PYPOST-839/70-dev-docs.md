# PYPOST-839: Dev Docs

## Created / Updated

- [x] `doc/dev/agent_e2e.md` — Overview / Architecture / API / Configuration /
  Troubleshooting umbrella for agent UI e2e
- [x] `Makefile` — `test-agent-e2e` with `##` help description
- [x] `doc/dev/README.md` — index entry for Agent UI E2E
- [x] `doc/dev/testing.md` — `make test-agent-e2e` + MCP vs agent e2e note
- [x] `doc/dev/mcp_integration.md` — distinction pointer to agent e2e
- [x] `doc/dev/gui_testing.md` — umbrella + make target
- [x] `doc/dev/setup.md` — make target list
- [x] `doc/dev/agent_lifecycle.md` — packaging complete + Related
- [x] `doc/dev/agent_golden_e2e.md` — prefer `make test-agent-e2e`
- [x] `doc/dev/ui_identity.md` / `ui_actions.md` / `ui_snapshot.md` /
  `ui_wait.md` — Related link to umbrella

## Notes

Developer docs follow Overview / Architecture / API / Configuration /
Troubleshooting. User-facing `doc/user/` unchanged. Preferred run path is
`make test-agent-e2e` (not shell-only pytest).
