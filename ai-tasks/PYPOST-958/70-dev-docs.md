# PYPOST-958: Dev Docs Update

## Changes

Updated `doc/dev/agent_e2e_http.md`:

- Added GUI proof section after compound-key unit proof list (958).
- Documented scenario test name, inventory gate, and run commands.

Updated `doc/dev/agent_e2e.md`:

- Harness table row for `tests/test_agent_e2e_http_mapping_compound_keys.py`.

## Scope

Minimal discoverability touch; no new standalone doc file.

## Verification

- Doc references match
  `test_mapping_compound_keys_same_url_get_post_panel_outcomes`.
- Harness table guard (`tests/test_agent_e2e_harness_table_doc.py`) stays green.
