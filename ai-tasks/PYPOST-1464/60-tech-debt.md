# PYPOST-1464: Technical Debt Analysis

## Shortcuts Taken

No temporary stubs, bypasses, or hardcoded workarounds remain in the isolated proxy implementation.
Proxy selection and connection settings (`server_type`, `upstream_url`, `upstream_transport`,
copied `headers`, and `timeout`) are carried as additive primitive fields in the `START` IPC
message with local-server defaults (`"local"`, `None`, `"streamable_http"`, `{}`, `30.0`),
preserving backward compatibility for local callers without bumping `MSG_V = 1`. Enforcing IPC
version negotiation remains deferred to the dedicated sprint task
([PYPOST-1467](https://pypost.atlassian.net/browse/PYPOST-1467)), as specified in
`ai-tasks/PYPOST-1464/20-architecture.md`.

Consistent with thread-mode proxy behavior, worker startup (`STARTED`) reports that the local
proxy listener is bound and ready, while upstream reachability and request timeouts remain
per-operation outcomes inside `MCPProxyServerImpl`. Unexpected child exits transition the owning
registry entry to `failed` without automatic restart; configurable auto-restart and active
heartbeat liveness checks remain tracked under
[PYPOST-1466](https://pypost.atlassian.net/browse/PYPOST-1466) and
[PYPOST-1468](https://pypost.atlassian.net/browse/PYPOST-1468).

## Code Quality Issues

No code-quality blocker was identified in `pypost/core/mcp_process_supervisor.py`,
`pypost/core/mcp_server_runner.py`, `pypost/core/mcp_worker_process.py`, or
`tests/test_mcp_process_proxy_repro.py`:

- `ProcessServerRunner.start` retains a deep copy of `ServerStartSpec` (including proxy settings)
  for reconfiguration rollback recovery and passes a copied `headers` mapping to
  `McpProcessSupervisor.spawn_worker`, which again copies `headers` into the `START` message.
- `worker_main` selects `MCPProxyServerImpl` when `server_type == "proxy"` and `MCPServerImpl`
  otherwise, binding its owned `_SnapshotStore` suppliers (`variable_supplier`,
  `hidden_keys_supplier`, `overridable_keys_supplier`) to both implementations and registering
  decoded local tools only on `MCPServerImpl`.
- `worker_main` decodes `message.get("tools")` before the `server_type` branch; for proxy workers
  this is a trivial empty-list no-op because `MCPServerRegistry._runtime_inputs` supplies `[]` for
  proxies.
- Production and Markdown lint (`make -o lint-tests lint`) and `make typecheck` pass with zero new
  issues. Test lint has only the pre-existing `tests/test_mcp_server_registry.py:308:101` E501
  violation recorded below ([PYPOST-1509](https://pypost.atlassian.net/browse/PYPOST-1509)).
- Process-mode collection tool refresh (`refresh_collection`) applies only to local collection
  servers and remains tracked by [PYPOST-1465](https://pypost.atlassian.net/browse/PYPOST-1465).

## Missing Tests

No missing test coverage is classified as a **BLOCKER**:

- **Timeout markers**: `tests/test_mcp_process_proxy_repro.py` declares an explicit module-level
  timeout (`pytestmark = pytest.mark.timeout(60)`), satisfying project pytest timeout rules.
- **Covered scenarios**: The four acceptance cases in `tests/test_mcp_process_proxy_repro.py`
  verify end-to-end tool discovery and invocation across both supported upstream transports
  (`streamable_http` and `sse`), per-worker header template resolution (`{{ TOKEN }}`), `START`
  payload completeness and header copy isolation, registry-level process proxy reconfiguration to a
  new upstream and port, port reclamation, and `caplog` verification that lifecycle logs omit
  upstream URLs and resolved secret values.
- **Broader stress and platform CI**: Process-mode 10x multi-server stress parity and Windows
  stop-escalation CI coverage remain tracked under
  [PYPOST-1470](https://pypost.atlassian.net/browse/PYPOST-1470).

## Performance Concerns

No new performance blocker was introduced by this task:

- **Per-operation upstream sessions**: `MCPProxyServerImpl` opens upstream client sessions per MCP
  operation inside the child process, matching existing thread-mode proxy semantics without sharing
  runtime client objects across processes.
- **Process memory footprint**: Each isolated proxy worker is a spawned headless Python interpreter
  (~30–50 MB baseline RSS without Qt imports). Optional per-worker memory ceilings and spawn
  admission control for dense process-mode configurations remain tracked under
  [PYPOST-1469](https://pypost.atlassian.net/browse/PYPOST-1469).

## Follow-up Tasks

All follow-up items below are **NON-BLOCKER** and already tracked in Jira; no duplicate issues are
created by this task:

- **TD-1 — NON-BLOCKER — pre-existing**: Test lint reports
  `tests/test_mcp_server_registry.py:308:101: E501 line too long (111 > 100 characters)` when
  running `make lint` (reproduced at base commit `33d5cb1a`).
  Jira: [PYPOST-1509](https://pypost.atlassian.net/browse/PYPOST-1509).
- **TD-2 — NON-BLOCKER**: Process-mode local tool refresh (`UPDATE_TOOLS` / worker restart in
  `refresh_collection`).
  Jira: [PYPOST-1465](https://pypost.atlassian.net/browse/PYPOST-1465).
- **TD-3 — NON-BLOCKER**: Configurable auto-restart policy with exponential backoff for unexpected
  MCP worker exits.
  Jira: [PYPOST-1466](https://pypost.atlassian.net/browse/PYPOST-1466).
- **TD-4 — NON-BLOCKER**: IPC protocol version (`MSG_V`) negotiation and mismatch rejection between
  supervisor and worker.
  Jira: [PYPOST-1467](https://pypost.atlassian.net/browse/PYPOST-1467).
- **TD-5 — NON-BLOCKER**: Active supervisor `HEARTBEAT` watchdog to transition hung workers to
  `failed`.
  Jira: [PYPOST-1468](https://pypost.atlassian.net/browse/PYPOST-1468).
- **TD-6 — NON-BLOCKER**: Per-worker memory ceilings and spawn admission control for process-mode
  MCP workers.
  Jira: [PYPOST-1469](https://pypost.atlassian.net/browse/PYPOST-1469).
- **TD-7 — NON-BLOCKER**: Process-mode 10x multi-server stress parity and Windows stop-escalation
  CI coverage.
  Jira: [PYPOST-1470](https://pypost.atlassian.net/browse/PYPOST-1470).
