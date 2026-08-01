# PYPOST-954: Dev Docs

| File | Change |
| --- | --- |
| `doc/dev/testing.md` | Extended § **Packaging doc lock strategy** with PYPOST-954 shared helper, UI-action MCP lock table row, focused pytest command, updated semantic HARDEN triggers |
| `doc/dev/testing.md` | Makefile automation table row for PYPOST-954 |
| `tests/test_ui_actions_mcp_packaging_doc.py` | Module docstring pointer to testing.md strategy section |
| `tests/test_agent_e2e_broader_packaging_doc.py` | Module docstring updated for shared helper |

## Overview

Developers editing UI-action MCP packaging docs (`ui_actions.md`, product MCP
cross-links) should preserve locked tokens listed in `doc/dev/testing.md` or
update the lock module intentionally. Hardening is via shared helper — not
semantic schema — until revisit triggers fire.

## Troubleshooting

If a doc edit fails UI-action packaging contract tests, check the token table
in `doc/dev/testing.md` § Packaging doc lock strategy before rephrasing prose.

Focused run:

```bash
make test PYTEST_ARGS='tests/test_ui_actions_mcp_packaging_doc.py tests/test_packaging_doc_lock_helper.py -v'
```

## Cross-links

- Parent packaging path: [ui_actions.md](../../doc/dev/ui_actions.md) (PYPOST-918)
- Sidecar entry: [agent_ui_actions_mcp.md](../../doc/dev/agent_ui_actions_mcp.md) (PYPOST-952)
- Runtime catalog guard: `tests/test_mcp_server_impl.py` (PYPOST-953)
