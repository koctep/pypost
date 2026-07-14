# PYPOST-788: Dev Docs

## Updated files

| File | Change |
| --- | --- |
| `doc/dev/setup.md` | Replaced five-item Key Dependencies with full production summary table + audit link |
| `doc/dev/dependencies_audit.md` | Marked R-P3-004 Done (PYPOST-788) |

## Key documentation points

- All 11 direct production packages from `requirements.in` appear in setup docs.
- MCP stack (`mcp` SDK) and encryption packages (`cryptography`, `keyring`) are included.
- Pinned versions and MCP transitive notes remain in `dependencies_audit.md`.
