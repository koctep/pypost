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

## WebSocket

Configure concurrency ceilings, buffer limits, heartbeats, reconnection, and MCP probe defaults:

| Setting | Default | Description |
| ------- | ------- | ----------- |
| `ws_max_concurrent_sessions` | `10` | Maximum simultaneous open WebSocket connections |
| `ws_max_stream_buffer_bytes` | `10485760` | Maximum stream buffer memory per tab (10 MB) |
| `ws_heartbeat_interval_sec` | `30.0` | Interval between ping heartbeat frames (seconds) |
| `ws_heartbeat_timeout_sec` | `10.0` | Timeout waiting for pong response (seconds) |
| `ws_reconnect_max_attempts` | `5` | Maximum automatic reconnect retries |
| `ws_reconnect_backoff_base_sec` | `1.0` | Initial exponential backoff delay (seconds) |
| `ws_reconnect_backoff_max_sec` | `60.0` | Maximum backoff delay cap (seconds) |
| `ws_mcp_probe_max_duration_sec` | `30.0` | Default probe duration for AI agent tools |
| `ws_mcp_probe_max_messages` | `100` | Default probe frame ceiling for AI agent tools |

## MCP and metrics servers

| Setting | Default |
| ------- | ------- |
| MCP host / port | `127.0.0.1` : `1080` conversion defaults for legacy MCP settings |
| Metrics host / port | `127.0.0.1` : `9080` |

Request-tool endpoint host and port are configured per **MCP Servers…** row, together with its
collection and environment. Saving Settings does not rebind those endpoints; their rows stay
unchanged. The global MCP host/port are retained only to prefill an explicit legacy-conversion
row. Metrics settings are separate; changing metrics host or port restarts the metrics server.

Prefer `127.0.0.1` for every MCP Servers row. Binding `0.0.0.0` exposes unauthenticated tool
execution on the network.

- Agent URL: `http://<endpoint-host>:<endpoint-port>/mcp` — create/start the row in
  **MCP Servers…**; see [MCP Tools](mcp-tools.md)
- Prometheus scrape: `http://127.0.0.1:9080/metrics` — see
  [Prometheus Monitoring](../prometheus_monitoring.md)

## Environment encryption

PyPost supports optional cryptographic protection for sensitive environment variables
(flagged as **Hidden**) stored on disk in `environments.json`:

### Encryption configuration

- **Encryption Mode:** Enable or disable encryption at rest. When disabled, hidden variables
  are stored in plaintext. Non-hidden variables are always stored in plaintext regardless of mode.
- **Key Source:** Select where the master encryption key is loaded from:
  - `Environment Variable` (`PYPOST_ENCRYPTION_KEY`)
  - `OS Keyring` (system credential manager / keychain)
  - `Secret Store File` (explicit key file path)
- **Key Identifier (KID):** Identifies the active key version for key rotation.

### Migration operations

When changing encryption modes or rotating keys in **Settings → Encryption**:

1. **Verify Key:** Tests that the configured key source and active Key ID can successfully
   decrypt currently encrypted records before applying changes.
2. **Encrypt Plaintext:** Scans all environments for hidden variables stored in plaintext
   and encrypts them using the active key. Run this immediately after enabling encryption mode.
3. **Re-encrypt (Key Rotation):** Re-encrypts all hidden records from prior key versions
   to the new active Key ID. Use this when updating your master key or rotating secrets.
4. **Export Warning:** Exporting environments containing hidden variables prompts for explicit
   confirmation because export files contain decrypted secret values (see
   [Environments](environments.md#hidden-values-in-export-files)).

## Logging and security

- **Log variable key names when hidden flag is toggled** — when enabled, toggling
  the Hidden flag may log the variable's key name (not the value)
- **Sensitive data masking** — request URLs, headers, and body payloads automatically mask
  hidden variable values in logs and terminal outputs

Prefer keeping secrets in hidden variables and enabling encryption if the machine is
shared or the data directory is backed up to an untrusted location.
