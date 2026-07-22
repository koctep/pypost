# PYPOST-892 Requirements

Automate FR5 red-path for double-body lock: monkeypatch
`TabsPresenterWorkerHandlers._discard_chunk_buffer` to no-op and assert
joined response body token `count >= 2`.

## Acceptance

- [x] Automated e2e test red when discard disabled
- [x] Default green lock unchanged (`count == 1`)
- [x] Documented in `doc/dev/agent_e2e_double_response_body.md`
