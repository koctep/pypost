# PYPOST-802: Developer Documentation

## Overview

Consolidated duplicate request-field dataclasses into a single canonical type with semantic
aliases. No behavior change — transport and history-masking code paths are unchanged.

## Architecture

- **Canonical type**: `pypost.core.request_fields.RequestFields` — frozen dataclass with
  `url`, `headers`, `body`.
- **Semantic aliases** (same class):
  - `ResolvedRequestFields` — fields resolved at HTTP/MCP transport time
  - `MaskedRequestData` — fields sanitized before history persistence
- **Consumers**:
  - `HTTPClient.send_request()` → `HTTPRequestResult.resolved: ResolvedRequestFields`
  - `SensitiveDataMaskingPolicy.build_history_safe_fields()` → `MaskedRequestData`

## Usage

```python
from pypost.core.request_fields import RequestFields, ResolvedRequestFields, MaskedRequestData

# All three names refer to the same frozen dataclass:
fields = RequestFields(url="https://example.com", headers={}, body="")
assert isinstance(fields, ResolvedRequestFields)
assert isinstance(fields, MaskedRequestData)
```

Existing imports remain valid:

```python
from pypost.core.http_client import ResolvedRequestFields  # re-exported alias
```

## Configuration

None.

## Troubleshooting

| Symptom | Action |
| --- | --- |
| Type checker treats aliases as distinct | Expected — aliases are the same runtime class; use `RequestFields` for isinstance checks |

See also: [sensitive_data_masking_policy.md](../../doc/dev/sensitive_data_masking_policy.md),
[request_execution.md](../../doc/dev/request_execution.md)
