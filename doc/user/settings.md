# Settings

Open **Settings** with `Ctrl+,` or `F12`. Changes apply after you save the dialog.

## Editor and appearance

- Application font size (default `12`)
- JSON Indent Size (default `2`)
- Theme: **system**, **light**, or **dark**

## Requests

- **Timeout** — how long to wait for an HTTP response (default `60` seconds)
- **Confirm before overwrite** — ask before overwriting a saved request

## Retries and alerts

Configure default retry delay, backoff, and which HTTP status codes are retryable.

When retries are exhausted you can:

- Write to an alert log file (default under the PyPost data directory if unset)
- Post to a webhook URL, optionally with an authorization header (stored carefully; the
  field uses password echo and does not re-display the saved value)

## MCP and metrics servers

| Setting | Default |
| ------- | ------- |
| MCP host / port | `127.0.0.1` : `1080` |
| Metrics host / port | `127.0.0.1` : `9080` |

After save, servers restart with the new bind settings. Invalid host/port values block
saving until corrected.

Prefer `127.0.0.1` for MCP. Binding `0.0.0.0` exposes unauthenticated tool execution on
the network.

- Agent URL: `http://127.0.0.1:1080/mcp` — see [MCP Tools](mcp-tools.md)
- Prometheus scrape: `http://127.0.0.1:9080/metrics` — see
  [Prometheus Monitoring](../prometheus_monitoring.md)

## Environment encryption

Optional encryption for **hidden** environment variables at rest:

- Enable/disable encryption mode
- Choose key source (environment variable, OS keyring, secret store) and fallback
- Run verify / re-encrypt / encrypt-plaintext migration actions when changing modes

Non-hidden variables remain plaintext on disk even when encryption is on.

## Logging and security

- **Log variable key names when hidden flag is toggled** — when enabled, toggling
  the Hidden flag may log the variable's key name (not the value)

Prefer keeping secrets in hidden variables and enabling encryption if the machine is
shared or the data directory is backed up to an untrusted location.
