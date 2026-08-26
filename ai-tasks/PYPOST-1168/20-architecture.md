# PYPOST-1168: Architecture — User documentation alignment

## Overview

Docs-only task: update user-guide files, add `doc/user/mcp-client.md`, and add pytest
contract tests. No production code changes.

## Target files

| File | Change |
| --- | --- |
| `doc/user/requests.md` | Remove HTTP method **MCP**; redirect to MCP Client guide |
| `doc/user/mcp-client.md` | **New** — outbound MCP Client workflow (connect, list, invoke) |
| `doc/user/interface.md` | MCP Client editor section; workspace mentions three editor types |
| `doc/user/mcp-tools.md` | Inbound vs outbound disambiguation at top; cross-links |
| `doc/user/README.md` | Add MCP Client guide to contents |

## Contract test module

`tests/test_mcp_tab_mode_user_docs.py` — parse user doc markdown and assert required
phrases/structure. No GUI or filesystem beyond repo `doc/user/`.

## Failing repro plan (Step 3)

| Test | Asserts (fails before Step 4) |
| --- | --- |
| `test_requests_doc_does_not_document_http_method_mcp` | `requests.md` omits choosing **MCP** as an HTTP method |
| `test_requests_doc_points_to_mcp_client_guide` | `requests.md` links to `mcp-client.md` |
| `test_interface_doc_describes_mcp_client_editor` | `interface.md` documents MCP Client editor chrome |
| `test_mcp_tools_doc_distinguishes_inbound_outbound` | `mcp-tools.md` labels inbound vs outbound surfaces |

Step 4 updates doc files until tests pass. `make test` with targeted `PYTEST_ARGS`.

## Dev docs (Step 8)

Add a short cross-link in `doc/dev/mcp_client_draft_tab.md` pointing to user guides and
contract tests.

## N/A

No runtime observability or metrics changes.
