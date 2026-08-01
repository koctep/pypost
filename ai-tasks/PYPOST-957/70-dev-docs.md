# PYPOST-957: Dev Docs Update

## Changes

Updated `doc/dev/agent_e2e_http.md`:

- Mapping multi-URL GUI module table — added caplog smoke row (957).
- Caplog matrix section — noted Mapping GUI-path smoke alongside env GET (904).
- Troubleshooting — added run command for Mapping GUI install-log caplog.

## Scope

Minimal discoverability touch; no new standalone doc file.

## Verification

- Doc references match test name
  `test_mapping_send_logs_http_stub_installed_url_router`.
- Run command documented under mapping module section.
