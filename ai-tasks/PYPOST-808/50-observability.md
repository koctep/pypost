# PYPOST-808: Observability

## Scope

Version metadata unification — no application logging or metrics changes.

## Existing observability preserved

| Signal | Source | Notes |
| --- | --- | --- |
| About dialog version | `pypost.version.__version__` | Unchanged display path |
| Package metadata | setuptools dynamic attr | Same string at install time |
| Diagnostics | module import | No new runtime probes |

## N/A

- Request/MCP/metrics logging — not affected by this task.
- Version is not emitted as a metric or structured log field today.
