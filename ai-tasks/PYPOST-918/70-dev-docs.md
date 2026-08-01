# PYPOST-918: Dev Docs

## Updates

| File | Change |
| --- | --- |
| `doc/dev/README.md` | TOC: UI Action Tools cites PYPOST-918 packaging; MCP section links packaging answer |
| `doc/dev/mcp_integration.md` | Soft “if built later” → closed packaging-path wording (still never on `MCPServerImpl`) |
| `doc/dev/mcp_trust_model.md` | Soft “would be” → packaging path documented (when built = separate trust boundary) |
| `doc/dev/agent_lifecycle.md` | Related table notes out-of-process MCP packaging (918) |
| `doc/dev/ui_actions.md` | Packaging path section already landed in Step 4 (unchanged this step) |

## Template coverage (70-dev-docs.mdc)

Packaging answer lives in `doc/dev/ui_actions.md` (Step 4); this step is
discoverability polish only.

- Overview — in-process agent API; not product MCP (`ui_actions.md`)
- Architecture — dedicated agent-UI MCP entry; never mount on `MCPServerImpl`
- API / Usage — existing primitives; packaging path is docs-only (no live bridge)
- Configuration — none for packaging docs
- Troubleshooting — deferred live bridge follows documented path when prioritized

## Validation

- [x] README indexes PYPOST-918 for UI-action out-of-process packaging
- [x] MCP + agent lifecycle docs point at the closed packaging answer
- [x] Contract lock green:
  `make test PYTEST_ARGS='tests/test_ui_actions_mcp_packaging_doc.py -v'`
- [x] STEP 8 left `[/]` pending review

## Self-Review

- [x] Docs in `doc/dev/`
- [x] English Markdown per `.cursor/lsr/do-markdown.md`
- [x] TD-4 discoverability (README index) addressed; no new Jira tickets
