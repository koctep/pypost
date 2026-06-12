# PYPOST-51 — Developer Documentation

> Task: PYPOST-51 — Add ExecuteRequestProtocol for request execution
> Date: 2026-06-12

---

## 1. What Changed and Why

Consumers of full request execution previously referenced the concrete `RequestService` class.
PYPOST-51 introduces `ExecuteRequestProtocol`, a structural protocol aligned with PYPOST-40
audit R9, so `RequestWorker` and `MCPServerImpl` depend on the `execute` contract instead of
the full service implementation.

`RequestWorker` and `MCPServerImpl` still construct `RequestService` by default. HTTP/MCP
transport, scripts, history, and retry behavior are unchanged.

---

## 2. New and Updated Modules

- `pypost/core/execute_request_protocol.py` (new) — `ExecuteRequestProtocol`.
- `pypost/core/worker.py` — `service: ExecuteRequestProtocol`.
- `pypost/core/mcp_server_impl.py` — `_create_request_service` return type.
- `tests/test_execute_request_protocol.py` (new) — protocol compliance tests.

---

## 3. Documentation Updated

- `doc/dev/testability.md` — `ExecuteRequestProtocol` section.
- `doc/dev/solid_audit.md` — R9 marked resolved.
- `doc/dev/tech-debt/PYPOST-40.md` — follow-up list updated.

---

## 4. Testing

```bash
pytest tests/test_execute_request_protocol.py tests/test_request_service.py -q
```
