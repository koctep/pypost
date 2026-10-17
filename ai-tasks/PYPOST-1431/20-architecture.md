# PYPOST-1431: Add IPv6 Socket Transport Coverage for Standalone MCP Servers

## Research

### 1. Existing `RawTcpWireClient` (`tests/helpers/raw_tcp_client.py`)
- **Current Socket Creation**:
  In `RawTcpWireClient.connect()`:
  ```python
  self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  self.sock.settimeout(self.timeout)
  self.sock.connect((self.host, self.port))
  ```
  The socket family is hardcoded to `socket.AF_INET`. When `self.host` is an IPv6 literal (such as `"::1"` or `"[::1]"`), attempting to connect over an `AF_INET` socket fails immediately with `socket.gaierror: [Errno -9] Address family for hostname not supported` or `OSError: [Errno 22] Invalid argument`.
- **HTTP `Host` Header Framing**:
  In `RawTcpWireClient.build_post_request()`:
  ```python
  headers = [
      f"POST {path} HTTP/1.1",
      f"Host: {self.host}:{self.port}",
      ...
  ```
  When `self.host` is `"::1"`, this generates:
  ```http
  Host: ::1:8080
  ```
  Per RFC 3986 (Uniform Resource Identifier: Generic Syntax, Section 3.2.2) and RFC 7230 (HTTP/1.1 Message Syntax and Routing, Section 5.4), IPv6 host literals in HTTP request URI and `Host` headers MUST be enclosed in brackets (e.g. `Host: [::1]:8080`). Unbracketed colons in the host field create parsing ambiguities with the port delimiter.
- **Address Resolution and Bracket Normalization**:
  When passing an address to `socket.connect((host, port))`, the C socket library and Python standard library expect the clean IP literal without square brackets (i.e. `"::1"`, not `"[::1]"`). If a caller initializes `RawTcpWireClient("[::1]", port)`, `socket.connect` will raise `socket.gaierror` if the brackets are not stripped. Conversely, the HTTP `Host` header must preserve or add brackets.

### 2. Server Binding Layer (`pypost/core/server_bind.py`)
- `pypost/core/server_bind.py` provides:
  ```python
  def detect_address_family(host: str) -> socket.AddressFamily:
      clean_host = host.strip("[]")
      try:
          ip = ipaddress.ip_address(clean_host)
          family = socket.AF_INET6 if ip.version == 6 else socket.AF_INET
      except ValueError:
          family = socket.AF_INET6 if ":" in clean_host else socket.AF_INET
      return family
  ```
- This helper already cleanly handles bracketed and unbracketed IPv6 strings (e.g. `"::1"` and `"[::1]"`), mapping them to `socket.AF_INET6`.
- `MCPServerManager` (in `pypost/core/qt/mcp_server.py`) already delegates address family detection to `detect_address_family` in `_wait_until_port_bindable()`:
  ```python
  family = detect_address_family(self._current_host)
  raw_host = self._current_host.strip("[]")
  with socket.socket(family, socket.SOCK_STREAM) as sock:
      sock.bind((raw_host, self._current_port))
  ```
- Furthermore, `uvicorn.Config(host=self._current_host, port=self._current_port)` supports `"::1"` out of the box when the OS supports IPv6 loopback.

### 3. Port Allocation Utility (`tests/helpers/port_allocation.py`)
- Inspection of `allocate_tcp_port(host="127.0.0.1")` reveals an IPv4 assumption in `_can_bind`:
  ```python
  def _can_bind(host: str, port: int) -> bool:
      with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
          sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
          try:
              sock.bind((host, port))
          except OSError:
              return False
      return True
  ```
  If `host="::1"` is passed to `allocate_tcp_port()`, `_can_bind` unconditionally instantiates `socket.AF_INET`, throwing `socket.gaierror` and failing all attempts, before falling back to `sock.bind((host, 0))` which also fails on `AF_INET`.
- Normalizing `_can_bind` and the ephemeral fallback to inspect the host's address family via `detect_address_family(host)` ensures `allocate_tcp_port("::1")` cleanly and deterministically allocates collision-free ports for IPv6 tests.

### 4. Standalone MCP Server Test Patterns (`tests/test_mcp_standalone_wire_ipc_repro.py`)
- Integration tests instantiate `MCPServerManager()` and start the server with:
  ```python
  port = allocate_tcp_port("127.0.0.1")
  manager = MCPServerManager()
  manager._impl._create_request_service = lambda: mock_service
  manager.start_server(port, [tool], host="127.0.0.1")
  wait_until(lambda: manager.is_listening, message="MCP server did not start listening")
  ```
- The test harness interacts with the server over raw TCP:
  1. Handshake: `initialize` JSON-RPC POST request, checking `session_id` and protocol version negotiation.
  2. Notification: `notifications/initialized` POST request.
  3. Tool Discovery: `tools/list` POST request, verifying registered tool list.
  4. Tool Execution: `tools/call` POST request, verifying execution and result envelope.
  5. Shutdown & Rebind: `manager.stop_server()`, verifying socket release.

### 5. OS Environment Capability Checking
- In some restricted container environments or legacy Linux kernels, IPv6 loopback might be disabled or unconfigured (`EAFNOSUPPORT` / `EADDRNOTAVAIL`).
- To guarantee zero false-positive CI failures while strictly verifying IPv6 when available, we design an environment capability probe:
  ```python
  def is_ipv6_loopback_supported() -> bool:
      try:
          with socket.socket(socket.AF_INET6, socket.SOCK_STREAM) as sock:
              sock.bind(("::1", 0))
          return True
      except OSError:
          return False
  ```
- Any test suite exercising live IPv6 sockets marks tests or the module with:
  ```python
  pytestmark = [
      pytest.mark.timeout(30),
      pytest.mark.skipif(
          not is_ipv6_loopback_supported(),
          reason="IPv6 loopback (::1) not supported in this environment",
      ),
  ]
  ```

---

## Implementation Plan

### High-Level Phases

1. **Step 3: Automated Failing Repro Test**:
   - Create `tests/test_mcp_standalone_wire_ipv6.py`.
   - Add a repro test case `test_raw_tcp_wire_client_ipv6_connection_repro` asserting that before the fix, attempting to connect to `::1` or `[::1]` with `RawTcpWireClient` raises `socket.gaierror` / `OSError` due to the hardcoded `socket.AF_INET` family mismatch, and that `build_post_request` formats an unbracketed `Host` header.
   - Run `make test` targeting the repro test to verify it reliably captures the defect in the unpatched state.

2. **Step 4: Development & Fix**:
   - **Update `tests/helpers/raw_tcp_client.py`**:
     - Modify `RawTcpWireClient.__init__` to accept `host: str`, `port: int`, `timeout: float = 10.0`, and optional `family: socket.AddressFamily | None = None`.
     - Compute clean host via `host.strip("[]")` for socket operations, and determine address family via `detect_address_family` if not explicitly provided.
     - In `connect()`, create socket with the detected family (`socket.AF_INET6` for `::1` / `[::1]`) and connect to `(clean_host, self.port)`.
     - In `build_post_request()`, format RFC 3986 compliant `Host` header: `Host: [{clean_host}]:{self.port}` if `self.family == socket.AF_INET6`, else `Host: {clean_host}:{self.port}`.
     - Add `formatted_host` property to `RawTcpWireClient` for clean introspection.
   - **Update `tests/helpers/port_allocation.py`**:
     - Update `_can_bind` and fallback socket creation to dynamically select `AF_INET` or `AF_INET6` based on `detect_address_family(host)`.
   - **Complete IPv6 Standalone MCP Server Test Suite (`tests/test_mcp_standalone_wire_ipv6.py`)**:
     - `test_raw_tcp_client_ipv6_connect_and_host_header`: unit test for client address family detection, socket connection, and bracketed `Host` header formatting with `::1` and `[::1]`.
     - `test_mcp_standalone_server_ipv6_lifecycle_handshake`: full handshake (`initialize` and `notifications/initialized`) over IPv6 loopback.
     - `test_mcp_standalone_server_ipv6_tool_discovery_and_call`: `tools/list` and `tools/call` over IPv6 loopback verifying execution results and session persistence.
     - `test_mcp_standalone_server_ipv6_teardown_and_rebind`: immediate port reuse and server re-instantiation on `::1` after graceful shutdown.
   - Run `make test`, `make lint`, `make typecheck` to verify quality gates pass.

3. **Step 5: Code Cleanup**:
   - Refactor duplicate logic, review docstrings, clean up temporary debug artifacts.

4. **Step 6: Observability**:
   - Verify logging emissions during address family detection and server startup on IPv6.

5. **Step 7: Technical Debt**:
   - Document any future enhancements (such as multi-homed dual-stack listener support).

6. **Step 8: Dev Docs**:
   - Update developer documentation if relevant.

### Mandatory — Failing Repro (next Step 3)

- **Test file**: `tests/test_mcp_standalone_wire_ipv6.py`.
- **Target function**: `test_raw_tcp_wire_client_ipv6_connection_repro()`.
- **Assertion**:
  1. Instantiating `client = RawTcpWireClient("::1", port)` and calling `client.connect()` against an active IPv6 listener raises `socket.gaierror` (with code `-9` / Address family for hostname not supported) or `OSError` because `RawTcpWireClient` currently hardcodes `socket.socket(socket.AF_INET, socket.SOCK_STREAM)`.
  2. Calling `client.build_post_request({"jsonrpc": "2.0"})` currently outputs `Host: ::1:{port}` which violates RFC 3986 bracketed IPv6 syntax.
- **Isolation**:
  - The repro starts a dummy IPv6 socket listener or tests `RawTcpWireClient.connect()` against an ephemeral port on `::1`.
  - No external services or live network access required.
- **Sequencing**:
  1. Step 2 (Current): Specify repro design in architecture.
  2. Step 3: Implement `test_raw_tcp_wire_client_ipv6_connection_repro` in `tests/test_mcp_standalone_wire_ipv6.py`. Run test and record failure.
  3. Step 4: Patch `RawTcpWireClient` and `port_allocation.py`, implement full IPv6 integration suite, turn test green.

---

## Architecture

### System Module Diagram

```mermaid
flowchart TD
    subgraph Test_Layer [Test Execution Layer]
        TestRunner["Pytest Runner<br/>(tests/test_mcp_standalone_wire_ipv6.py)"]
        EnvProbe["Environment Probe<br/>is_ipv6_loopback_supported()"]
        PortAlloc["Port Allocator<br/>allocate_tcp_port('::1')"]
    end

    subgraph Client_Layer [Wire Transport Client]
        RawClient["RawTcpWireClient<br/>(tests/helpers/raw_tcp_client.py)"]
        AddrDetect["detect_address_family(host)<br/>(pypost/core/server_bind.py)"]
        HostFormatter["Host Header Formatter<br/>[::1]:port (RFC 3986)"]
        SocketAF6["socket.socket(AF_INET6, SOCK_STREAM)<br/>connect(('::1', port))"]
    end

    subgraph Server_Layer [Standalone MCP Server]
        MCPServer["MCPServerManager<br/>(pypost/core/qt/mcp_server.py)"]
        UvicornServer["Uvicorn Async Worker<br/>host='::1', port=allocated_port"]
        FastAPIApp["MCP Starlette / FastAPI App<br/>(/mcp endpoint)"]
        ToolService["RequestService Mock<br/>Tool Execution Engine"]
    end

    TestRunner -->|1. Probe OS| EnvProbe
    TestRunner -->|2. Request Port| PortAlloc
    PortAlloc -->|Bind Probe (AF_INET6)| AddrDetect
    TestRunner -->|3. Start Server| MCPServer
    MCPServer -->|Spawn Thread| UvicornServer
    UvicornServer -->|Bind to [::1]| FastAPIApp
    FastAPIApp -->|Execute Tools| ToolService

    TestRunner -->|4. Connect Client| RawClient
    RawClient -->|Detect Family| AddrDetect
    RawClient -->|Format Host Header| HostFormatter
    RawClient -->|Open IPv6 Stream| SocketAF6
    SocketAF6 <===>|Raw HTTP/1.1 + JSON-RPC| UvicornServer

    TestRunner -->|5. Teardown Server| MCPServer
    MCPServer -->|Drain & Close Socket| UvicornServer
    TestRunner -->|6. Verify Rebind| PortAlloc
```

### Module Responsibilities

1. **`tests/helpers/raw_tcp_client.py` (`RawTcpWireClient`)**:
   - Manages raw stream socket lifecycle (`AF_INET` or `AF_INET6`).
   - Resolves target host address family dynamically using `detect_address_family` or caller override.
   - Strips brackets when binding or connecting raw sockets (`clean_host = host.strip("[]")`).
   - Enforces RFC 3986 bracketed `Host` header formatting for IPv6 targets (`Host: [::1]:{port}`).
   - Formats, sends, and parses fragmented HTTP requests, pipelined bursts, and chunked responses.

2. **`tests/helpers/port_allocation.py` (`allocate_tcp_port`, `_can_bind`)**:
   - Detects address family of requested host interface.
   - Probes port availability using `socket.socket(family, socket.SOCK_STREAM)` with `SO_REUSEADDR`.
   - Prevents port collisions across parallel test workers for both IPv4 (`127.0.0.1`) and IPv6 (`::1`).

3. **`pypost/core/server_bind.py`**:
   - Provides existing foundational helper `detect_address_family(host) -> socket.AddressFamily`.
   - Classifies bind errors (`PORT_IN_USE`, `ADDRESS_NOT_AVAILABLE`, `PERMISSION_DENIED`).

4. **`tests/test_mcp_standalone_wire_ipv6.py`**:
   - Dedicated integration test suite for IPv6 standalone MCP servers.
   - Provides `is_ipv6_loopback_supported() -> bool` guard fixture.
   - Tests `RawTcpWireClient` IPv6 connection and RFC 3986 `Host` header.
   - Tests standalone server lifecycle, protocol handshake, tool execution, session management, and clean teardown/rebind on IPv6.

### Architectural Patterns

- **Strategy / Adapter Pattern for Address Families**:
  `RawTcpWireClient` dynamically adapts its socket creation strategy (`AF_INET` vs `AF_INET6`) and header serialization strategy based on host syntax (`detect_address_family`), decoupling callers from transport-specific details.
- **Environment Capability Guard Pattern**:
  `is_ipv6_loopback_supported()` acts as a precondition probe. If the host platform lacks IPv6 loopback configuration, tests skip cleanly rather than failing due to environment limitations.
- **Context Manager Pattern**:
  `RawTcpWireClient` implements `__enter__` and `__exit__`, ensuring that open socket descriptors are deterministically closed even in the presence of test assertion failures.
- **Clean Room Port Isolation**:
  Leverages dynamic port locking via `allocate_tcp_port` to ensure tests execute concurrently without cross-worker interference.

### Interface Definitions

#### `RawTcpWireClient` Interface Updates
```python
class RawTcpWireClient:
    def __init__(
        self,
        host: str,
        port: int,
        timeout: float = 10.0,
        family: socket.AddressFamily | None = None,
    ) -> None:
        """Initialize wire client with target host, port, timeout, and address family.

        Args:
            host: Target hostname or IP literal (e.g. '127.0.0.1', '::1', '[::1]').
            port: Target TCP port number.
            timeout: Socket timeout in seconds for connect and read operations.
            family: Optional socket address family override (AF_INET or AF_INET6).
                    If None, automatically detected from host.
        """
        ...

    @property
    def clean_host(self) -> str:
        """Return host string stripped of bracket formatting for socket syscalls."""
        return self.host.strip("[]")

    @property
    def formatted_host_header(self) -> str:
        """Return RFC 3986 / RFC 7230 compliant Host header value."""
        if self.family == socket.AF_INET6:
            return f"[{self.clean_host}]:{self.port}"
        return f"{self.clean_host}:{self.port}"
```

#### `is_ipv6_loopback_supported` Helper Interface
```python
def is_ipv6_loopback_supported() -> bool:
    """Return True if the runtime environment allows binding to IPv6 loopback (::1)."""
    ...
```

---

## Q&A

**Q: Why should `RawTcpWireClient` automatically detect `AF_INET6` instead of requiring callers to pass `family=socket.AF_INET6`?**  
A: Automatic detection via `detect_address_family` allows existing tests and callers to pass either `"127.0.0.1"`, `"::1"`, or `"[::1]"` without having to manually manage low-level socket family flags, matching the behavior already present in `pypost/core/server_bind.py`. An optional `family` parameter is also preserved for explicit caller overrides.

**Q: Why must `clean_host` strip brackets for socket connect, but keep brackets for HTTP `Host` headers?**  
A: Low-level OS socket calls (`socket.connect((host, port))`) expect raw IP address literals (e.g. `::1`). Passing `[::1]` to `connect()` raises `socket.gaierror: Name or service not known` on many POSIX systems. However, in HTTP/1.1 message framing, RFC 3986 Section 3.2.2 and RFC 7230 Section 5.4 strictly require square brackets around IPv6 addresses in URIs and `Host` headers to disambiguate the address colons from the `:port` delimiter.

**Q: Why do we update `tests/helpers/port_allocation.py`?**  
A: `allocate_tcp_port()` currently hardcodes `socket.AF_INET`. If a test requests an ephemeral port on `"::1"`, the bind probe fails with `socket.gaierror`. Updating `_can_bind` to use `detect_address_family(host)` ensures dynamic port allocation works reliably for both IPv4 and IPv6 without port collisions.

**Q: How does this test suite avoid hanging when a test fails?**  
A: All tests specify bounded timeouts via module-level `pytestmark = pytest.mark.timeout(30)`, and `wait_until` polls utilize bounded timeouts (5 to 10 seconds). Furthermore, `manager.stop_server()` in `finally` blocks ensures that background uvicorn threads and listening sockets are promptly released.
