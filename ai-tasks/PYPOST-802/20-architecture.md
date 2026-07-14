# PYPOST-802: Architecture — shared RequestFields type

## Problem

```
http_client.py              sensitive_data_masking_policy.py
┌─────────────────────┐     ┌─────────────────────┐
│ ResolvedRequestFields│     │ MaskedRequestData   │
│  url, headers, body │     │  url, headers, body │  ← duplicate shape
└─────────────────────┘     └─────────────────────┘
```

## Target

```
request_fields.py
┌─────────────────────────────────────────┐
│ RequestFields (frozen dataclass)        │
│   url: str                              │
│   headers: Dict[str, str]               │
│   body: str                             │
├─────────────────────────────────────────┤
│ ResolvedRequestFields = RequestFields   │
│ MaskedRequestData = RequestFields       │
└─────────────────────────────────────────┘
         ▲                    ▲
         │                    │
  http_client.py    sensitive_data_masking_policy.py
  (import alias)    (import aliases)
```

## Changes

| Component | Change |
| --- | --- |
| `request_fields.py` | **New** — canonical `RequestFields` + semantic aliases |
| `http_client.py` | Remove local class; import `ResolvedRequestFields` alias |
| `sensitive_data_masking_policy.py` | Remove local class; import `MaskedRequestData` alias |

## Backward compatibility

- `from pypost.core.http_client import ResolvedRequestFields` unchanged for ~10 test/source files.
- `HTTPRequestResult.resolved` type unchanged.
- `build_history_safe_fields()` return type unchanged.
- Runtime behavior identical — aliases refer to the same dataclass.

## Out of scope

- Changing field types or adding fields
- Merging transport and masking logic
- Renaming public API symbols at call sites
