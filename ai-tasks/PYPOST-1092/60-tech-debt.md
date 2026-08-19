# PYPOST-1092: Technical Debt Analysis

## Shortcuts Taken

1. **Transient Upstream Connection Per Request**:
   - In `pypost/core/mcp_proxy_server_impl.py`, `_connect_upstream` establishes a new transient HTTP/SSE client connection and performs a full MCP `initialize()` handshake for each incoming protocol request (`list_tools`, `call_tool`, `list_prompts`, `get_prompt`, `list_resources`, `read_resource`).
   - *Rationale*: Guarantees complete connection isolation, avoids stale session leaks, and guarantees that updated environment variable headers take effect immediately without requiring session cache invalidation logic.
   - *Compromise*: Adds TCP/TLS connection handshake and MCP protocol initialization round-trip latency on every proxy call.

2. **Custom Headers UI Multiline Text Input**:
   - In `pypost/ui/dialogs/mcp_servers_dialog.py`, custom proxy headers are configured using a multiline `QPlainTextEdit` (`Key: Value` line format) rather than a dedicated interactive key-value table widget with dynamic environment variable completion.
   - *Rationale*: Kept the UI implementation lightweight and robust, relying on clean string parsing in `_parse_headers()`.
   - *Compromise*: Lacks inline syntax highlighting or interactive dropdown suggestions for environment variable placeholders (`{{ VAR }}`).

3. **Unified Timeout Application**:
   - The configured `timeout` is applied globally to the underlying `httpx.Timeout` / SSE client, but there is no separate sub-timeout distinction between initial handshake/connection establishment and lengthy tool execution payloads.

## Code Quality Issues

1. **Repetitive Protocol Dispatch Boilerplate in `MCPProxyServerImpl`**:
   - Methods `list_tools`, `call_tool`, `list_prompts`, `get_prompt`, `list_resources`, and `read_resource` share similar boilerplate structures for timer measurement, header resolution, error trapping (`httpx.TimeoutException`, `httpx.ConnectError`, `McpUnresolvedVariableError`), logging, and activity entry recording.
   - *Improvement*: Consolidate error handling, latency measurement, and activity logging into a unified async context manager or decorator (e.g. `_dispatch_proxy_operation(...)`).

2. **Lack of Shared Formal Interface for MCP Server Implementations**:
   - Both `MCPServerImpl` and `MCPProxyServerImpl` provide `create_app()`, `set_variable_supplier()`, and `set_hidden_keys_supplier()`, managed via `MCPServerManager._impl`.
   - *Improvement*: Define an explicit Python `Protocol` or abstract base class (e.g. `MCPServerEngineProtocol`) in `pypost.core` to formalize the structural subtyping contract and enforce type safety.

3. **Type Conversions in UI Transport Handling**:
   - In `_McpServerEditor.configuration()`, `upstream_transport` uses fallback casting (`Literal["streamable_http", "sse"]`) to bridge QComboBox data back to Pydantic model types.

## Missing Tests

1. **End-to-End Multi-Process Live Streamable HTTP & SSE Integration Tests**:
   - Current test suite in `tests/test_mcp_proxy_server.py` thoroughly covers protocol dispatch, header resolution, missing variable rejection, error handling, metrics tracking, and registry lifecycle using mock sessions and ASGI route checks.
   - Live end-to-end multi-process tests running a real remote secondary Uvicorn server receiving proxied HTTP requests and SSE streams over local sockets could be added to the slow integration test suite.

2. **Upstream Streaming & Chunked Resource Edge Cases**:
   - Test coverage focuses on standard tool, prompt, and resource exchanges. Edge cases involving large chunked streaming responses or non-standard HTML error payloads (e.g. HTTP 502 Bad Gateway with raw HTML from cloud load balancers) could have dedicated test fixtures.

3. **Test Timeout Declarations**:
   - All tests in `tests/test_mcp_proxy_server.py` declare module-level timeout `pytestmark = pytest.mark.timeout(60)`. Full compliance with test execution timeout guidelines is verified.

## Performance Concerns

1. **Protocol Handshake Overhead on High Concurrency**:
   - Under heavy or burst tool invocation traffic, creating fresh HTTP connections and executing `session.initialize()` per request can create connection churn and higher average response latency compared to a pooled, long-lived upstream session.
   - *Mitigation for future*: Introduce a header-aware connection pool or session cache with LRU eviction and configurable keep-alive TTL.

2. **Synchronous Header Rendering**:
   - Template header resolution is executed on each call via `TemplateService` / regex substitution. While header dictionaries are typically small (< 10 keys) and resolution takes < 1 ms, caching pre-compiled template structures would optimize extreme high-throughput scenarios.

## Follow-up Tasks

1. **PYPOST-1101** (3 SP): Implement connection pooling and session reuse in `MCPProxyServerImpl` with header hash keying and idle timeout expiration to reduce per-request handshake overhead.
   - Jira: [PYPOST-1101](https://pypost.atlassian.net/browse/PYPOST-1101)
2. **PYPOST-1102** (2 SP): Refactor `MCPProxyServerImpl` protocol methods to use a unified `_dispatch_proxy_operation` helper / decorator to eliminate error handling and metric recording duplication.
   - Jira: [PYPOST-1102](https://pypost.atlassian.net/browse/PYPOST-1102)
3. **PYPOST-1103** (2 SP): Introduce a formal `MCPServerEngineProtocol` interface in `pypost.core` unifying `MCPServerImpl` and `MCPProxyServerImpl`.
   - Jira: [PYPOST-1103](https://pypost.atlassian.net/browse/PYPOST-1103)
4. **PYPOST-1104** (3 SP): Upgrade the Custom Headers editor in `_McpServerEditor` to a rich Key-Value table widget with variable completion dropdowns and syntax validation hints.
   - Jira: [PYPOST-1104](https://pypost.atlassian.net/browse/PYPOST-1104)
5. **PYPOST-1105** (3 SP): Add slow live multi-process wire integration tests for real SSE and Streamable HTTP upstream proxying in `tests/test_mcp_proxy_live_integration.py`.
   - Jira: [PYPOST-1105](https://pypost.atlassian.net/browse/PYPOST-1105)
