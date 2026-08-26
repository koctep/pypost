# PYPOST-1163: Architecture — User documentation alignment

## Overview

Docs-only task: update four user-guide files and add pytest contract tests. No production
code changes.

## Target files

| File | Change |
| --- | --- |
| `doc/user/websocket.md` | Step 1: protocol picker + saved profile paths |
| `doc/user/interface.md` | Workspace: protocol picker on `Ctrl+N` / **+** |
| `doc/user/hotkeys.md` | New Tab description; WebSocket Session rows match `hotkeys.py` registration |
| `doc/user/collections.md` | WebSocket **New tab** isolated-copy behavior |

## Contract test module

`tests/test_websocket_tab_mode_user_docs.py` — parse user doc markdown and assert required
phrases/structure. No GUI or filesystem beyond repo `doc/user/`.

## Failing repro plan (Step 3)

| Test | Asserts (fails before Step 4) |
| --- | --- |
| `test_websocket_guide_step1_describes_protocol_picker` | `websocket.md` mentions protocol picker / **WebSocket** choice on new tab |
| `test_interface_doc_describes_protocol_picker_on_new_tab` | `interface.md` mentions protocol picker for `Ctrl+N` and **+** |
| `test_hotkeys_doc_matches_websocket_session_registration` | Required WS shortcut keys and section present |
| `test_collections_doc_describes_websocket_new_tab` | WebSocket **New tab** isolated copy documented |

Step 4 updates the four doc files until tests pass. `make test` with targeted `PYTEST_ARGS`.

## Dev docs (Step 8)

Add a short cross-link in `doc/dev/websocket_ui_client.md` pointing to user guides and
contract tests.

## N/A

No runtime observability or metrics changes.
