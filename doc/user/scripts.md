# Post-Request Scripts

On the **Script** tab you can write Python that runs **after** the HTTP response
arrives. Use this for automation such as storing tokens or light checks.

## Available objects

| Object | Role |
| ------ | ---- |
| `response` | Parsed response (`json`, `text`, `body`, `status_code`, …) |
| `request` | The request data that was sent |
| `pypost` | Helpers for the active environment and script logs |

`response` exposes `.json()`, `.text`, `.body`, `.status_code`, `.headers`,
`.elapsed_time`, and `.size`.

### `pypost` helpers

- `pypost.env.set(key, value)` — set/update a variable on the active environment
  and persist it
- `pypost.env.get(key, default=None)` — read a variable from the script env snapshot
- `pypost.log(message)` — append a line to script logs

`print(...)` output is captured and appended to script logs as `[STDOUT] …`.

## Save a token to the environment

```python
token = response.json()['token']
pypost.env.set('auth_token', token)
```

Later requests can use:

```text
Authorization: Bearer {{ auth_token }}
```

Mark `auth_token` as **Hidden** in **Manage Environments** so it stays masked in the
UI (`********`). New keys created by a script are not Hidden until you mark them.

## Check status

```python
if response.status_code != 200:
    pypost.log(f"Unexpected status: {response.status_code}")
```

Script log lines may also appear in the MCP tool result envelope under `logs` when an
agent calls the request as a tool.

## Errors

If the script raises, PyPost records a script execution error (the HTTP response itself
may still have succeeded). Fix the script and send again.

## Tips

- Keep scripts short and deterministic.
- Prefer environment variables over hard-coding secrets in the script source.
- Test the request with **Send** before relying on the script in an MCP workflow.
