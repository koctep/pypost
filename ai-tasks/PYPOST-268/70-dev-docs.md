# PYPOST-268: Dev Docs

## Updates

| File | Change |
| --- | --- |
| `doc/dev/testability.md` | Added `TestHTTPClientPrepareRequestKwargs` to HTTPClient coverage table |

## Rationale

Developer docs already describe HTTPClient injection seams. This task adds direct
`_prepare_request_kwargs` coverage; the testability doc is the right index for test class
discovery.

## Out of scope

- `doc/dev/request_execution.md` — already documents `rendered_url` reuse
- `doc/dev/yaml_as_json.md` — send-path tests still referenced; isolation tests complement
