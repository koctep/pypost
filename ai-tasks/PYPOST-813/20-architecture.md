# PYPOST-813: Architecture

## Problem

With `no_implicit_optional = true`, signatures like `variables: Dict[str, str] = None` produce
`assignment` errors: the default is `None` but the annotation omits `| None`.

## Protocols (source of truth)

| Protocol | Module | Optional parameters |
| --- | --- | --- |
| `HTTPClientProtocol` | `http_client_protocol.py` | `variables`, `stream_callback`, `stop_flag`, `headers_callback` |
| `ExecuteRequestProtocol` | `execute_request_protocol.py` | Same four plus `collection_name`, `request_name`, `retry_callback`, `hidden_keys` |

Implementations already used `= None` defaults and runtime `if variables is None` guards; only
annotations were wrong.

## Changes

| File | Method | Fix |
| --- | --- | --- |
| `pypost/core/http_client.py` | `send_request` | Four params: add `\| None` |
| `pypost/core/request_service.py` | `execute` | Four params: add `\| None` |

No call-site changes — runtime behavior unchanged.

## Baseline impact

| Metric | Before (PYPOST-734) | After (PYPOST-813) |
| --- | ---: | ---: |
| Total errors | 54 | 42 |
| `http_client.py` errors | 5 | 0 |
| `request_service.py` `assignment` errors | 4 | 0 |

Additional baseline drops (e.g. `truthy-function` in `http_client.py`, one `assignment` in
`qt/worker.py`) were side effects of consistent optional typing — not separate scope.

## Remaining debt in touched files

| File | Code | Count | Follow-up |
| --- | --- | ---: | --- |
| `request_service.py` | `union-attr` | 4 | Nullable `TemplateService` in `_execute_mcp` |
| `request_service.py` | `var-annotated` | 2 | Local annotations in `execute` |

Tracked under parent PYPOST-734 residual debt; not blockers for this task.
