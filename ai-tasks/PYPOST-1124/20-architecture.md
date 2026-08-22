# PYPOST-1124: WebSocket support — RFC and high-level architecture

This document is the Step 2 artifact of PYPOST-1124 and the RFC called for by the story's
Jira acceptance criteria. It turns the approved requirements in
[`10-requirements.md`](10-requirements.md) into an architecture: a networking-engine decision,
a domain and persistence model, a PySide6 interaction model with wireframes, stream data
handling, a security model, a test strategy, and the engineering stories to create under Epic
PYPOST-1123.

Scope note: PYPOST-1124 itself ships **documents only**. Every design element below describes
work performed by the implementation stories in
[Implementation breakdown](#a-13-implementation-breakdown--stories-for-epic-pypost-1123), each of
which runs its own Top-Down cycle.

Citation convention: repository paths are relative to the repository root and were read while
writing this document; external claims carry a link in [References](#references).

## Research

### R-0 Verification method

Every claim below is one of three kinds, and each is marked as such:

| Kind | How it was verified |
| --- | --- |
| **Repo fact** | Read from a file in this repository; path (and line, where useful) is cited |
| **Runtime fact** | Observed by executing code against the pinned `.venv` (PySide6 6.11.1) |
| **Vendor fact** | Read from official upstream docs; URL in [References](#references) |

No version-specific behavior is asserted that was not checked in one of those three ways.
Where something could not be verified, it is recorded as an open question in
[A-15](#a-15-risks-and-open-questions) and converted into a test requirement rather than an
assumption.

### R-1 What PyPost does today that WebSocket must fit into

Repo facts that constrain the design. These extend, and do not restate, the baseline already
established in [`10-requirements.md`](10-requirements.md).

- **Layering** — `models/` stdlib-only; `core/` Qt-free; Qt glue in `core/qt/`; `ui/` on top.
  Source: `doc/dev/architecture.md`.
- **Execution** — `RequestWorker` is a **one-shot** `QThread`; a stopped instance must not be
  reused. Source: `pypost/core/qt/worker.py:23-35`.
- **Streaming precedent** — streamed body chunks are coalesced into a per-tab buffer flushed by
  a single-shot `QTimer` at **33 ms**. Source: `doc/dev/response-streaming-display.md`,
  `pypost/ui/presenters/tabs_presenter.py:118-120`.
- **Real-time precedent** — SSE is a **bounded probe**: `SSE_PROBE_MAX_EVENTS = 5`,
  `SSE_PROBE_TIMEOUT = 10.0`. Source: `pypost/core/http_client.py:28-30`.
- **Request model** — `RequestData` is documented to stay lean because tab isolation
  **deep-copies** it. Source: `pypost/models/models.py:65-72`,
  `doc/dev/request_data_copy_policy.md`.
- **Collection model** — `Collection.requests: List[RequestData]`; one JSON file per collection
  id. Source: `pypost/models/models.py:91-95`, `doc/dev/collection_storage.md`.
- **History model** — `HistoryEntry.status_code: int` and `response_time_ms: float` are
  **required**; the store caps at `DEFAULT_MAX_ENTRIES = 500`. Source:
  `pypost/models/models.py:105-115`, `pypost/core/history_manager.py:18`.
- **History UI** — the filter is URL-substring only; rows are `QListWidgetItem` built per entry.
  Source: `pypost/ui/widgets/history_panel.py:65-67,129-146`.
- **Masking** — `sanitize_text` / `sanitize_headers` with `env_vars` + `hidden_keys`, applied at
  history-write time. Source: `pypost/core/sensitive_data_masking_policy.py`,
  `doc/dev/sensitive_data_masking_policy.md`.
- **MCP contract** — `call_tool` returns `List[TextContent]` from **one** call, executed through
  `run_in_threadpool`, guarded by `DEFAULT_MAX_CONCURRENT_MCP_CALLS`. Source:
  `pypost/core/mcp_server_impl.py:105,130-183`.
- **MCP secrets** — hidden and env-only variables are stripped from `list_tools` and merged only
  at `call_tool`. Source: `pypost/core/mcp_secrets_policy.py`, `doc/dev/mcp_secrets_policy.md`.
- **MCP threading** — `MCPServerManager` runs uvicorn's asyncio loop in a plain
  `threading.Thread`. Source: `pypost/core/qt/mcp_server.py:127,222-246`.
- **Daemon** — headless mode runs a `QCoreApplication` loop; storage loads only the records
  enabled MCP servers need. Source: `doc/dev/daemon.md`.
- **Automation** — stable `objectName` identities, `pypost_` prefix, per-tab role ids scoped to
  the current tab. Source: `pypost/ui/widget_ids.py`, `doc/dev/ui_identity.md`.
- **Bounded waits** — `wait_until(...)` spins Qt events to a wall-clock deadline and raises on
  timeout. Source: `pypost/agent/ui_wait.py:54-111`, `doc/dev/ui_wait.md`.
- **GUI tests** — offscreen platform, module-scoped `qapp` fixture, no `pytest-qt`. Source:
  `doc/dev/gui_testing.md`.

#### R-1.1 Hard module-size caps (a design constraint, not a style preference)

`scripts/audit_baseline_metrics.py` defines per-file LOC caps enforced by
`tests/test_solid_audit_baseline.py` and `--check`. The caps that matter here, measured with the
same total-line count the script compares against the cap (repo facts, read 2026-08):

| Module | Current LOC | Cap | Headroom | Touched by |
| --- | ---: | ---: | ---: | --- |
| `pypost/ui/presenters/tabs_presenter.py` | 641 | 785 | 144 | WS-4 |
| `pypost/core/request_manager.py` | 260 | 260 | **0** | WS-2 |
| `pypost/core/storage.py` | 364 | 380 | 16 | WS-2 (no change needed) |
| `pypost/core/mcp_server_impl.py` | 312 | 325 | 13 | WS-9 |
| `pypost/core/qt/worker.py` | 180 | 180 | **0** | nobody — A-1.1 adds no worker |

`pypost/ui/widgets/request_editor.py` (671 LOC) is not capped but is already the largest widget
module. **Consequence:** a second protocol cannot be bolted onto `TabsPresenter` or
`RequestWidget`, and the three capped modules the epic touches have 0, 16 and 13 lines of
headroom respectively. The architecture below puts WebSocket behavior in new modules and gives
the existing ones only a narrow seam. Concretely, per story:

- **WS-2 / `request_manager.py` — 0 lines free.** The websocket index, profile CRUD and the
  kind-aware lookup go into a **new** Qt-free module `pypost/core/websocket_registry.py`, never
  into `RequestManager` (A-4.1). Because zero headroom means even a one-line hook fails
  `--check`, WS-2 first **extracts** the existing item-type dispatch
  (`delete_collection_item`, `rename_collection_item`;
  `pypost/core/request_manager.py:171-190,245-260`) into
  `pypost/core/collection_item_dispatch.py` and re-derives the `request_manager.py` cap from the
  post-extraction measurement — the move PYPOST-1071 already made for `main_window.py` and
  `env_presenter.py` (see the cap comments in `scripts/audit_baseline_metrics.py`). Both new
  modules are registered with their own caps.
- **WS-2 / `storage.py` — 16 lines free, and none are needed.** `save_collection` writes
  `collection.model_dump_json(indent=2)` and `load_collections` builds `Collection(**data)`
  (`pypost/core/storage.py:107-113,147-161`), so `Collection.websockets` round-trips through the
  code that is already there. WS-2's storage obligation is a test that proves it, not new lines
  in a nearly-full module.
- **WS-9 / `mcp_server_impl.py` — 13 lines free.** The probe tool's schema, registration and
  dispatch live in a new Qt-free `pypost/core/websocket_mcp_tools.py`; `MCPServerImpl` gains only
  a delegating call from `register_tools` (`pypost/core/mcp_server_impl.py:283-288`) and one
  dispatch branch in `call_tool`. If the measured delta does not fit the remaining 13 lines,
  WS-9 moves `_generate_schema` (`pypost/core/mcp_server_impl.py:290-297`) into the same new
  module and re-derives the cap, rather than raising a cap to make room for new code.
- **WS-4 / `tabs_presenter.py` — 144 lines free.** Three thin methods only (A-5.1); the page and
  the session live in `WebSocketPresenter`.

Each of these four obligations is acceptance criteria on the story that owns it (A-13), not
advice.

### R-2 Backward compatibility of the collection file format (runtime fact)

`Collection` and `RequestData` declare no `model_config`, so Pydantic v2's default
`extra='ignore'` applies. Executed against the pinned environment:

```python
Collection(**{"id": "x", "name": "n", "requests": [], "websocket_connections": [{"id": "a"}]})
# -> {'id': 'x', 'name': 'n', 'requests': []}   # unknown key silently dropped
RequestData(**{"name": "n", "protocol": "ws"})  # 'protocol' silently dropped
```

Two consequences drive
[D-2](#a-41-d-2--a-websocket-connection-is-a-new-persisted-object-not-a-new-method):

1. A build without WebSocket support **loads** a collection containing WebSocket entries without
   error and without corrupting the HTTP requests in it. Scenario S-6.4 holds for reading.
2. That same build **silently drops** the entries when it next saves the collection. Downgrade
   is lossy. This must be documented, not engineered away — a schema-version field cannot help,
   because an old build ignores that field too.

This also rules out a discriminated union inside `Collection.requests`: an old build would
coerce a WebSocket entry into a `RequestData` (every field has a default, `method` defaults to
`"GET"`) and produce a bogus HTTP request rather than dropping a key. A **separate list is
strictly safer than a mixed list.**

### R-3 Networking engine candidates

#### R-3.1 Qt-native `QWebSocket` (`PySide6.QtWebSockets`)

Runtime facts, observed against the pinned `.venv` (PySide6 6.11.1):

- The module ships inside the already-installed PySide6 distribution as
  `PySide6/QtWebSockets.abi3.so`. That file is listed in
  `pyside6_addons-6.11.1.dist-info/RECORD`, i.e. it arrives with **`pyside6-addons`** (not
  with `pyside6-essentials`, which ships only the `.pyi` stub) — see
  [A-16](#a-16-portability-and-platform-coverage) for why that still costs nothing.
  It exports `QWebSocket`, `QWebSocketServer`,
  `QWebSocketHandshakeOptions`, `QWebSocketProtocol`, `QWebSocketCorsAuthenticator`,
  `QMaskGenerator`.
- The bundled stub `PySide6/QtWebSockets.pyi` confirms the API surface the design relies on:
  `open(QUrl|QNetworkRequest[, QWebSocketHandshakeOptions])`, `sendTextMessage`,
  `sendBinaryMessage`, `ping(payload)`, `close(closeCode, reason)`, `closeCode()`,
  `closeReason()`, `errorString()`, `subprotocol()`, `state()`,
  `setMaxAllowedIncomingMessageSize`, `setMaxAllowedIncomingFrameSize`, `setOutgoingFrameSize`,
  `setReadBufferSize`, `setSslConfiguration`, `ignoreSslErrors`, and the signals `connected`,
  `disconnected`, `stateChanged`, `errorOccurred`, `textMessageReceived`,
  `binaryMessageReceived`, `textFrameReceived`, `binaryFrameReceived`,
  `pong(quint64, QByteArray)`, `sslErrors`, `peerVerifyError`, `handshakeInterruptedOnError`.
- `QWebSocketProtocol.CloseCode` enumerates the RFC 6455 close codes
  (`CloseCodeNormal = 1000` … `CloseCodeTlsHandshakeFailed = 1015`).

Vendor facts from the Qt 6 class reference:

- `open(url, options)` / `open(request, options)` and `subprotocol()` exist **since Qt 6.4**;
  `errorOccurred` **since Qt 6.5**. PySide6 6.11.1 wraps Qt 6.11, so all are available.
- "QWebSocket only supports version 13 of the WebSocket protocol, as outlined in RFC 6455."
- "QWebSocket currently does not support WebSocket Extensions." There is therefore **no
  `permessage-deflate`**.
- "Some proxies do not understand certain HTTP headers used during a WebSocket handshake. In
  that case, non-secure WebSocket connections fail."

Gap observed in the API surface: neither the Qt class reference member list nor the shipped
`.pyi` exposes any accessor for the **handshake HTTP response** (status line or response
headers). On rejection the only diagnostics are `errorOccurred` plus `errorString()`.

#### R-3.2 asyncio (`websockets` or `aiohttp`) plus a loop host

Vendor facts: `websockets.asyncio.client.connect()` documents `additional_headers=None`,
`subprotocols=None`, `ping_interval=20`, `ping_timeout=20`, `max_size=1048576`,
`close_timeout=10`, `compression='deflate'`, and passes remaining keyword arguments to the
loop's `create_connection()`. It therefore provides heartbeat scheduling, message-size limits
and compression out of the box — the three things Qt does not.

The blocking question is **where its event loop runs**. Three hosts exist and each was checked:

1. **`PySide6.QtAsyncio` (native, no new dependency)** — *ruled out*. Runtime fact: reading
   `PySide6/QtAsyncio/events.py` from the installed wheel, `QAsyncioEventLoop` raises
   `NotImplementedError` for `create_connection()`, `create_datagram_endpoint()`,
   `getaddrinfo()`, `getnameinfo()`, every `sock_*` method, and `add_reader()` /
   `add_writer()`. A library that opens its own TCP connection cannot run on this loop today.
2. **`qasync` (third-party)** — replaces the process-wide asyncio event loop with one driven by
   the Qt event loop. It is maintained, but it changes the loop under **every** existing test in
   a suite built on a module-scoped `QApplication` (`doc/dev/gui_testing.md`). Blast radius is
   the whole application for a feature that occupies one tab.
3. **A dedicated asyncio thread** — viable, and PyPost already does exactly this for MCP
   (`pypost/core/qt/mcp_server.py:222-246` creates a fresh loop inside a `threading.Thread`).
   The cost is that every frame crosses a thread boundary and needs a queued Qt connection, plus
   a bespoke send queue, cancellation protocol, and shutdown handshake.

All three also require a **new direct production dependency**. `websockets` is not present in
the current lock (`requirements.txt` contains `anyio`, `httpx`, `starlette`, `uvicorn` from
`mcp`, but no WebSocket client). Adding one costs a `make lock` regeneration,
`LICENSES/transitive.csv` refresh gated by `make check-license-inventory`, and additional
`pip-audit` surface (`doc/dev/licensing.md`, `doc/dev/dependencies_audit.md`).

#### R-3.3 Evidence summary

| Criterion | `QWebSocket` | `websockets`/`aiohttp` + loop host |
| --- | --- | --- |
| New production dependency | **None** (in the PySide6 wheel) | 1 direct + lock, licenses, audit |
| Event-loop host | The Qt loop that already runs | `qasync` (global) or a dedicated thread |
| Thread hops per message | 0 (signal on the owning thread) | 1 (queued connection) |
| Heartbeat scheduling | Manual (`ping()` + `pong` + `QTimer`) | Built in (`ping_interval`) |
| Message size cap | `setMaxAllowedIncomingMessageSize()` | `max_size` |
| `permessage-deflate` | **Not supported** | Default on |
| Handshake response introspection | **Not exposed** | Available |
| Subprotocol negotiation | `QWebSocketHandshakeOptions`, `subprotocol()` | `subprotocols=` |
| TLS control | `QSslConfiguration`, `sslErrors`, `peerVerifyError` | `ssl.SSLContext` |
| Local test server | **`QWebSocketServer`, same module** | Needs another library |
| Headless (`pypost-daemon`) | Works on `QCoreApplication` | Works; second loop beside MCP's |

### R-4 What the Step 1 benchmark fixes as user expectation

Carried forward from [`10-requirements.md`](10-requirements.md) without re-deriving: a
persistent connect/disconnect control distinct from per-message send; one unified timestamped
stream of sent, received and lifecycle events; a first-class multi-line composer with format
selection; and connection parameters frozen while connected. These four are treated below as
non-negotiable inputs to the interaction model, not as options.

## Implementation Plan

### P-1 Delivery shape

The epic is delivered as twelve independently mergeable stories, 79 story points, sequenced in
eight waves — wave 0 through wave 7, listed in [P-2](#p-2-sequencing). The full list, with scope,
acceptance criteria, dependencies and estimates, is in
[A-13](#a-13-implementation-breakdown--stories-for-epic-pypost-1123). The plan's three governing
rules:

1. **Test harness first.** The local `QWebSocketServer` echo fixture (WS-11) has no dependency
   on the client work and must land first or concurrently, so every later story is verifiable
   from its first commit.
2. **Non-visual foundations before UI.** Transport, models and the stream buffer (WS-1, WS-2,
   WS-3) merge without a user-facing entry point. Each keeps the application working because it
   adds no reachable surface.
3. **First visible story must be useful on its own.** WS-4 ships a minimal but complete client
   (connect, plain-text send, chronological stream). WS-5 and WS-6 then upgrade the inspector
   and the composer. No story leaves a half-built tab in the product.

### P-2 Sequencing

```text
wave 0   WS-11 test harness
wave 1   WS-1 transport + session engine      WS-2 models + persistence
wave 2   WS-3 stream buffer + model           WS-8 TLS policy
wave 3   WS-4 session tab (minimal client)
wave 4   WS-5 stream inspector                WS-6 composer/presets/seqs
wave 5   WS-7 env/templating/masking          WS-10 settings + ceiling + metrics
wave 6   WS-9 bounded MCP probe
wave 7   WS-12 user and developer docs
```

Stories inside one wave are independent of each other; a wave starts when the wave above it
has merged.

### Mandatory — Failing Repro (next Step 3)

**N/A — no behavioral change.** PYPOST-1124 is a discovery story. Its deliverables are the
documents in `ai-tasks/PYPOST-1124/` plus Jira issues created by a later phase of this run; no
production module, dependency, or runtime behavior is touched, so there is no observable defect
or missing behavior for an automated red test to assert. Step 3 for this task records `N/A` in
the roadmap with this reason.

The failing-repro obligation is **not waived — it is delegated**. Each implementation story
under PYPOST-1123 runs its own Step 3, and this document fixes the pattern each must follow so
the obligation cannot evaporate:

- **WS-1** — `tests/test_websocket_session.py`: connect to the local echo server, assert `Open`
  is reached and an echoed text frame arrives. Red because `WebSocketSessionController` does
  not exist.
- **WS-2** — `tests/test_websocket_models.py`: save, load, export and import a collection with a
  WebSocket profile and assert presets survive. Red because `Collection.websockets` does not
  exist.
- **WS-3** — `tests/test_websocket_stream.py`: push entries past the byte budget and assert
  oldest-dropped plus a drop counter. Red because the ring buffer does not exist.
- **WS-4** — `tests/test_websocket_tab.py`: open a profile, assert `pypost_ws_state_badge` reads
  `Open` after connect and that the URL input is read-only while connected.
- **WS-5** — `tests/test_websocket_stream_view.py`: filter by direction and assert the visible
  row count.
- **WS-6** — `tests/test_websocket_composer.py`: run a two-step sequence with delays and assert
  both steps land in order.
- **WS-7** — `tests/test_websocket_masking.py`: send a payload containing a hidden variable and
  assert the placeholder appears in the stream, the clipboard and the export.
- **WS-8** — `tests/test_websocket_tls.py`: a self-signed peer is rejected by default and the
  session never reaches `Open`.
- **WS-9** — `tests/test_websocket_mcp_probe.py`: `call_tool` returns a bounded masked
  transcript and the runner thread has exited.
- **WS-10** — `tests/test_websocket_metrics.py`: scrape the registry and assert the new counter
  names and label sets; `tests/test_websocket_session_limits.py`: with the ceiling at N, the
  N+1-th connect is refused with a stated reason and no socket is opened (A-12.1).

Every one of these is runnable offline against the WS-11 fixture. None requires a public
internet endpoint, satisfying the Step 1 testability NFR.

## Architecture

### A-0 Decision register

- **D-1** — Qt-native `QWebSocket` is the networking engine, behind a Qt-free transport seam.
  *Reversibility: medium* — a second transport fits behind the seam without touching session or
  UI code.
- **D-2** — A WebSocket connection is a **new persisted object** in a new `Collection.websockets`
  list, not a new `RequestData.method`. *Reversibility: low* — it changes the on-disk shape.
- **D-3** — A live session is **runtime-only** and never persisted. *Reversibility: high.*
- **D-4** — Sessions do **not** enter `HistoryEntry` history in this epic. *Reversibility: high*
  — additive later.
- **D-5** — MCP exposure is a **bounded one-shot probe**, not a persistent agent-held session.
  *Reversibility: high* — the persistent form remains addable.
- **D-6** — Sessions live in the existing tab widget as a new page type owned by a **new
  presenter**. *Reversibility: medium.*
- **D-7** — Handshake data resolves **once at connect**; payloads resolve **per send**; received
  data is **never** rendered as a template. *Reversibility: high.*
- **D-8** — The stream is a bounded ring with **two** eviction dimensions (entry count and byte
  budget), rendered through `QAbstractListModel` + `QListView`. *Reversibility: high.*
- **D-9** — Post-response scripting is **excluded**; variable capture is a stream context-menu
  action instead. *Reversibility: high.*
- **D-10** — No "Copy as cURL" equivalent; sharing is copy-profile-JSON plus transcript export.
  *Reversibility: high.*
- **D-11** — The daemon hosts the MCP probe but never long-lived sessions.
  *Reversibility: high.*
- **D-12** — `ignoreSslErrors()` is forbidden; TLS failures block by default and any override is
  per-session and never persisted. *Reversibility: high.*
- **D-13** — Connection parameters are frozen for the whole life of a session; message-,
  stream- and policy-side controls stay editable throughout (A-5.3).
  *Reversibility: high.*
- **D-14** — Concurrent live sockets are bounded process-wide by
  `ws_max_concurrent_sessions`; at the ceiling a new connect is **refused with a reason**,
  never queued and never silently dropped (A-12.1). *Reversibility: high.*

### A-1 D-1 — Networking engine: recommend Qt-native `QWebSocket`

> **Recommendation: implement the WebSocket transport with `PySide6.QtWebSockets.QWebSocket`,
> behind a Qt-free `WebSocketTransport` protocol so the choice stays reversible.**

#### A-1.1 Rationale

1. **Zero new production dependencies.** `QtWebSockets` ships in the `pyside6-addons`
   6.11.1 wheel that the pinned `PySide6==6.11.1` meta-package already installs
   (`requirements.in`, `requirements.txt:93-100`; runtime fact, R-3.1), and
   `PySide6_Addons` is already in `LICENSES/transitive.csv`. The asyncio route adds a direct
   dependency plus lock, license-inventory and `pip-audit` obligations
   (`doc/dev/licensing.md`).
2. **It fits the threading model PyPost already has, by removing a thread rather than adding
   one.** PyPost's one-shot `RequestWorker` (`pypost/core/qt/worker.py:23-35`) exists because
   `requests` blocks; a `QWebSocket` never blocks, so a long-lived session needs **no worker
   thread at all**. Messages arrive as signals on the owning thread's event loop. The asyncio
   route reintroduces a thread boundary for a feature whose whole point is a continuous flow of
   small events.
3. **The native asyncio bridge cannot host the alternative.** `QAsyncioEventLoop` raises
   `NotImplementedError` for `create_connection`, `getaddrinfo`, `sock_*`, `add_reader` and
   `add_writer` (runtime fact, R-3.2). So the asyncio option is not "PySide6's own asyncio
   support" — it is either `qasync` replacing the application's event loop globally, or a second
   dedicated loop thread. Both are larger changes than the feature warrants.
4. **The test harness comes with it.** `QWebSocketServer` is in the same module, so the local
   echo/misbehaving-peer server required by the testability NFR is buildable with no new
   dependency and no network access, under `QT_QPA_PLATFORM=offscreen`.
5. **Headless works unchanged.** QtWebSockets depends on QtCore and QtNetwork only, so the MCP
   probe runs under the daemon's `QCoreApplication` loop (`doc/dev/daemon.md`) with no display
   server and without adding a second asyncio loop beside uvicorn's.
6. **TLS is first-class and explicit.** `setSslConfiguration`, `sslErrors`, `peerVerifyError`
   and `handshakeInterruptedOnError` give the exact hooks D-12 needs.

#### A-1.2 Accepted trade-offs

- **No WebSocket Extensions, therefore no `permessage-deflate`** (vendor fact).
  *Impact:* higher bandwidth on chatty text streams; endpoints that *require* compression
  cannot be exercised. *Mitigation:* PyPost never offers the extension, so a conforming server
  must negotiate it away (RFC 6455 §9). Recorded as an epic limitation and as follow-up FU-7.
- **Handshake HTTP status and headers are not exposed.**
  *Impact:* a `401`/`403` rejection is reported as a socket error, not as a status code.
  *Mitigation:* surface `errorString()`, `closeCode()` and `closeReason()` verbatim; WS-1
  acceptance requires a *specific* reason string, not "connection failed". An optional
  pre-flight HTTP probe is FU-11.
- **No built-in heartbeat or reconnect.** *Impact:* both must be implemented.
  *Mitigation:* one small pure-policy module (`websocket_session_policy.py`) plus `QTimer`,
  which also makes the policy unit-testable without a socket — something a library built-in
  would not be.
- **The socket lives on the GUI thread.** *Impact:* a flood competes with painting.
  *Mitigation:* the whole of [A-6](#a-6-d-8--message-stream-data-handling) exists for this, and
  WS-11 includes a flood test with an explicit responsiveness bound.
- **Protocol version 13 only.** *Impact:* none in practice — that *is* RFC 6455.
  *Mitigation:* documented.
- **Less community precedent for QWebSocket in Python than for `websockets`.**
  *Impact:* slower debugging of exotic failures. *Mitigation:* the transport seam (A-1.4) keeps
  a swap cheap.

#### A-1.3 Risks of each option, stated plainly

Risks **if we adopt `QWebSocket`** (the recommendation):

- **R-A** A user's endpoint mandates `permessage-deflate` and the session cannot be established
  or is unusably slow. *Likelihood: low* (extensions are negotiated, not required, by conforming
  servers). *Detection:* WS-1 must log the negotiated subprotocol and any handshake error.
  *Response:* FU-7 (second transport behind the seam).
- **R-B** Diagnosing an auth rejection is harder than in Postman, which shows the handshake
  response. *Likelihood: high; severity: low.* *Response:* precise error text plus FU-11.
- **R-C** A high-rate stream degrades UI responsiveness because the socket shares the GUI
  thread. *Likelihood: medium.* *Response:* coalesced intake, bounded ring, drop counters, and
  a load test that fails CI if the responsiveness bound regresses.
- **R-D** An undocumented ordering difference between the `connected()` signal and
  `stateChanged(ConnectedState)` produces a wrong badge. *Response:* WS-1 must pin the observed
  ordering with a test against the local server (see [A-15](#a-15-risks-and-open-questions),
  OQ-1) rather than assume it.

Risks **if we adopt asyncio** (the rejected option):

- **R-E** `qasync` replaces the process event loop; every existing GUI test and the composition
  root in `pypost/main.py` run under a different loop. Enormous blast radius for one tab.
- **R-F** A dedicated asyncio thread means per-message cross-thread marshalling plus a bespoke
  send queue, cancellation and shutdown handshake — more code and more failure modes than the
  whole Qt implementation.
- **R-G** New direct dependency: lock regeneration, `LICENSES/transitive.csv` refresh gated by
  `make check-license-inventory`, and a wider `pip-audit` surface, for a capability already
  present in the wheel we ship.
- **R-H** Two asyncio loops in one process (uvicorn's for MCP plus the WebSocket one) with
  different lifetimes and shutdown paths.

#### A-1.4 The seam that makes D-1 reversible

The transport is defined as a Qt-free `Protocol` in `core/`, implemented once in `core/qt/`.
This mirrors the existing `HTTPClientProtocol` / `ExecuteRequestProtocol` seams
(`pypost/core/http_client_protocol.py`, `pypost/core/execute_request_protocol.py`) that already
let `RequestService` accept a substitute implementation.

```python
# pypost/core/websocket_transport_protocol.py  (stdlib + typing only, no Qt)

class WebSocketTransport(Protocol):
    """Bidirectional frame transport for one WebSocket session.

    Implementations are event-driven: they never block the caller and report every
    outcome through ``set_listener``. One instance serves one connection attempt;
    a reconnect allocates a new instance (same rule as ``RequestWorker``).
    """

    def open(self, target: HandshakeTarget) -> None: ...
    def send_text(self, message: str) -> None: ...
    def send_binary(self, payload: bytes) -> None: ...
    def ping(self, payload: bytes = b"") -> None: ...
    def close(self, code: int = 1000, reason: str = "") -> None: ...
    def abort(self) -> None: ...
    def negotiated_subprotocol(self) -> str: ...
    def set_listener(self, listener: "WebSocketTransportListener") -> None: ...


class WebSocketTransportListener(Protocol):
    def on_opened(self, subprotocol: str) -> None: ...
    def on_text(self, message: str) -> None: ...
    def on_binary(self, payload: bytes) -> None: ...
    def on_pong(self, elapsed_ms: int, payload: bytes) -> None: ...
    def on_closed(self, code: int, reason: str, peer_initiated: bool) -> None: ...
    def on_failed(self, category: str, message: str, detail: str) -> None: ...
    def on_tls_errors(self, errors: tuple[str, ...]) -> bool: ...
```

`HandshakeTarget` is a frozen dataclass of already-resolved values (`url`, `headers`,
`subprotocols`, `max_incoming_message_bytes`, `verify_tls`) — the transport performs **no**
template rendering and holds **no** reference to an `Environment`. The same module declares
`RawFrame` (`direction`, `payload_format`, `payload`, `byte_size`), the unmasked value the
session controller re-emits and the presenter converts into a `StreamEntry` (A-3.1).

Swapping engines later means writing a second class satisfying `WebSocketTransport`. Nothing in
the session controller, the stream, or the UI changes.

### A-2 Module map

```text
pypost/
  models/
    websocket.py                     # WebSocketConnection, presets, sequences,
                                     # HeartbeatPolicy, ReconnectPolicy, enums
    models.py                        # + Collection.websockets
    settings.py                      # + ws_* global bounds
  core/                              # Qt-free
    websocket_transport_protocol.py  # Protocol + HandshakeTarget (A-1.4)
    websocket_session_policy.py      # state machine, backoff, heartbeat policy
    websocket_stream.py              # bounded ring, entries, filters, drop counters
    websocket_codec.py               # text/JSON/hex/base64 encode, decode, detect
    websocket_stream_export.py       # transcript payload shaping (masked)
    websocket_sequence.py            # sequence plan expansion and step outcomes
    websocket_probe.py               # MCP probe stop conditions + transcript
    websocket_registry.py            # ws index, CRUD, kind-aware find_item (R-1.1)
    websocket_mcp_tools.py           # probe tool schema/registration/dispatch (R-1.1)
    collection_item_dispatch.py      # extracted from request_manager.py (R-1.1)
    qt/
      websocket_transport.py         # QWebSocket adapter (only QtWebSockets import)
      websocket_session.py           # WebSocketSessionController(QObject) + signals
      websocket_sequence_runner.py   # QTimer-driven step pacing
      websocket_probe_runner.py      # short-lived QThread with its own event loop
  ui/
    presenters/websocket_presenter.py  # owns sessions, wires tab pages
    widgets/websocket/
      websocket_tab.py               # page: header, detail tabs, stream, composer
      connection_editor.py           # URL, params, headers, subprotocols, settings
      state_badge.py                 # text + icon state indicator
      stream_model.py                # QAbstractListModel over the ring
      stream_view.py                 # QListView + delegate + filter bar + detail
      composer.py                    # CodeEditor + format combo + send
      presets_panel.py               # presets and sequences
    widget_ids.py                    # + WS_* identities
```

Layer compliance (`doc/dev/architecture.md`): `models/websocket.py` imports only stdlib and
`pydantic`, exactly like `pypost/models/models.py`. Every `core/websocket_*.py` module is
importable without Qt and is unit-tested without a `QApplication`. Only `core/qt/*` imports
PySide6. `ui/` depends on all three. **`pypost/core/qt/websocket_transport.py` is the only
module in the repository allowed to import `PySide6.QtWebSockets`** — enforced by a guard test
in WS-1, following the precedent of `tests/test_gateway_qapp_free_function_style.py`.

### A-3 Component interaction

```text
   Collections tree                     EnvPresenter
   (WebSocket item)                  (variables, hidden_keys)
          | open                              | snapshot
          v                                   v
  +--------------------------------------------------------------+
  | WebSocketPresenter                          (ui/presenters)   |
  |   - one WebSocketSessionController per open tab               |
  |   - resolves templates at connect and at send                 |
  |   - masks each raw frame into a StreamEntry (A-8.2)           |
  |   - owns the MessageStream ring and the 33 ms flush           |
  +---+-------------------------+------------------------+-------+
      | commands, raw frames up | masked entry batches    | page wiring
      v                         v                         v
  +---------------------------+ +--------------------+ +------------------+
  | WebSocketSessionController| | StreamListModel    | | WebSocketTab     |
  |        (core/qt)          | | (ui, virtualized)  | | header | details |
  | state machine + timers    | | sole ring writer   | | stream | composer|
  | no stream, no masking     | +---------+----------+ +------------------+
  +---------------------------+           |
      | frames                            v
      v                         +--------------------+
  +---------------------------+ | MessageStream      |
  | WebSocketTransport        | | (core, bounded)    |
  | (core/qt)  QWebSocket     | +--------------------+
  +---------------------------+

  TabsPresenter keeps owning the QTabWidget and exposes only:
      open_page(widget, title, item_id), close_page(item_id),
      set_page_badge(item_id, text)
```

#### A-3.1 Who owns the ring, and with which masking inputs

This is the seam most likely to be rewired by a later story if it is left implicit, so it is
fixed here once and every story below is written against it (FR-7.1):

1. **Transport → controller.** The transport reports frames and lifecycle callbacks. It holds no
   `Environment` and performs no rendering (A-1.4).
2. **Controller → presenter.** `WebSocketSessionController` re-emits frames **raw and unmasked**
   as `RawFrame` values (`direction`, `payload_format`, `payload`, `byte_size`) plus lifecycle
   events. It owns the state machine, the heartbeat and the reconnect timers — and **no
   `MessageStream`, no masking, no `Environment`**. That is what keeps it headlessly testable.
3. **Presenter → entry.** `WebSocketPresenter` is the only component holding `env_vars` and
   `hidden_keys` (from `EnvPresenter`, `doc/dev/variable_propagation.md`). It converts each
   `RawFrame` into a masked `StreamEntry` through the Qt-free pure function
   `build_stream_entry(frame, *, env_vars, hidden_keys, truncate_bytes)` in
   `pypost/core/websocket_stream.py`, so the masking rule (A-8.2) is one unit-testable function
   with explicit inputs rather than an ambient capability.
4. **Presenter → model → ring.** Masked entries accumulate in a pending batch flushed by the
   33 ms single-shot `QTimer` (A-6.3). The flush calls `StreamListModel.append_batch(entries)`,
   and **`StreamListModel` is the sole writer of `MessageStream` on the UI path**: one
   `beginInsertRows`/`endInsertRows` per flush, plus one `beginRemoveRows` for whatever the ring
   reports as evicted. Nothing unmasked ever reaches the ring, so Export and Copy read only safe
   values.

`RawFrame` is declared next to `HandshakeTarget` in
`pypost/core/websocket_transport_protocol.py` (WS-1), which is why WS-3 depends on WS-1 as well
as on WS-2 (A-13.3).

The MCP probe (A-10) does **not** use this path: it has no presenter and no ring, and shapes its
own bounded transcript in `pypost/core/websocket_probe.py`.

`WebSocketSessionController` signal surface (Qt signals, consumed by the presenter):

```python
class WebSocketSessionController(QObject):
    """Long-lived session: state machine, heartbeat, reconnect. Owns no stream."""

    state_changed = Signal(str, object)        # SessionState value, StateDetail | None
    frame_received = Signal(object)            # RawFrame, unmasked
    frame_sent = Signal(object)                # RawFrame, unmasked, after the socket accepted it
    lifecycle_event = Signal(str, str)         # event name, unmasked detail text
    reconnect_scheduled = Signal(int, int, int)  # attempt, max_attempts, delay_ms
    subprotocol_negotiated = Signal(str)
    session_failed = Signal(str, str)          # category, operator-facing message
    tls_errors_raised = Signal(object)         # tuple[str, ...]; decision returned by slot
```

Drop accounting is **not** a controller signal: `MessageStream.append` returns what it evicted,
`StreamListModel` turns that into row removals, and the presenter renders the notice (A-6.2).

The controller never touches widgets, never renders templates, and never reads an
`Environment`; the presenter hands it fully-resolved values. That keeps the session engine
testable headlessly and keeps secret resolution in exactly one place
([A-8](#a-8-security-and-secret-handling)).

### A-4 D-2/D-3 — Domain model, persistence and collection interchange

#### A-4.1 D-2 — A WebSocket connection is a new persisted object, not a new "method"

Rejected: adding `"WS"` to the method combo (`pypost/ui/widgets/request_editor.py:97`) and
reusing `RequestData`.

- `RequestData` is explicitly documented to stay lean because **tab isolation deep-copies it**
  (`pypost/models/models.py:65-72`, `doc/dev/request_data_copy_policy.md`). Adding presets,
  sequences, heartbeat and reconnect would inflate the copy cost of every HTTP tab.
- Its fields are HTTP-shaped: `body_type`, `retry_policy.retryable_status_codes` (`100..599`,
  `pypost/models/retry.py`), and a `method` that drives body auto-switching
  (`doc/dev/method_body_autoswitch.md`) and metric labels
  (`track_request_sent(method)`, `pypost/core/metrics_registry.py:296`). None of these are
  meaningful for a session.
- The `MCP` pseudo-method already shows the cost of overloading `method`; a second non-HTTP
  value would multiply the `if method == …` branches through `RequestService`, `HTTPClient`,
  `CurlGenerator` and the history label.
- R-2 shows a separate list is also the **safer** on-disk shape.

```python
# pypost/models/websocket.py  (stdlib + pydantic only)

class WsMessageFormat(str, Enum):
    TEXT = "text"
    JSON = "json"
    HEX = "hex"        # binary entered/displayed as hexadecimal
    BASE64 = "base64"  # binary entered/displayed as base64


class HeartbeatPolicy(BaseModel):
    enabled: bool = True
    interval_seconds: int = Field(default=30, ge=5, le=3600)
    timeout_seconds: int = Field(default=10, ge=1, le=300)


class ReconnectPolicy(BaseModel):
    enabled: bool = True
    max_attempts: int = Field(default=5, ge=0, le=100)
    initial_delay_seconds: float = Field(default=1.0, gt=0)
    backoff_multiplier: float = Field(default=2.0, ge=1.0)
    max_delay_seconds: float = Field(default=30.0, gt=0)


class WebSocketMessagePreset(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "New Message"
    format: WsMessageFormat = WsMessageFormat.JSON
    payload: str = ""            # template text; never a resolved value


class WebSocketSequenceStep(BaseModel):
    preset_id: Optional[str] = None
    inline_payload: str = ""
    format: WsMessageFormat = WsMessageFormat.JSON
    delay_ms: int = Field(default=0, ge=0, le=600_000)   # waited BEFORE this step (A-5.8)


class WebSocketSequence(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "New Sequence"
    steps: List[WebSocketSequenceStep] = Field(default_factory=list)


class WebSocketConnection(BaseModel):
    """Saved, reusable description of a real-time endpoint. Peer of RequestData."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "New WebSocket"
    url: str = ""                                  # ws:// or wss://, may contain {{ vars }}
    headers: Dict[str, str] = Field(default_factory=dict)
    params: Dict[str, str] = Field(default_factory=dict)
    subprotocols: List[str] = Field(default_factory=list)
    heartbeat: HeartbeatPolicy = Field(default_factory=HeartbeatPolicy)
    reconnect: ReconnectPolicy = Field(default_factory=ReconnectPolicy)
    presets: List[WebSocketMessagePreset] = Field(default_factory=list)
    sequences: List[WebSocketSequence] = Field(default_factory=list)
    default_format: WsMessageFormat = WsMessageFormat.JSON
    # The six MCP fields below are DEFINED AND PERSISTED BY WS-2 (this model);
    # WS-9 owns only the behavior behind them and adds no field. See A-13.2 / A-13.9.
    expose_as_mcp: bool = False                    # bounded probe only — see A-10
    mcp_description: str = ""
    mcp_params: Dict[str, McpToolParam] = Field(default_factory=dict)
    mcp_probe_preset_id: Optional[str] = None      # message the probe sends after connect
    mcp_probe_max_messages: Optional[int] = None   # None = global default
    mcp_probe_max_duration_ms: Optional[int] = None
```

`Collection` gains one field:

```python
class Collection(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "New Collection"
    requests: List[RequestData] = Field(default_factory=list)
    websockets: List[WebSocketConnection] = Field(default_factory=list)   # NEW
```

The websocket index and its CRUD **do not go into `RequestManager`**, which has zero cap
headroom (R-1.1). They go into a new Qt-free module:

```python
# pypost/core/websocket_registry.py  (stdlib + typing; no lines added to RequestManager)

class WebSocketRegistry:
    """Index and CRUD for websocket profiles inside the collections RequestManager holds."""

    def find_websocket(self, ws_id: str) -> Optional[Tuple[WebSocketConnection, Collection]]: ...
    def save_websocket(self, conn: WebSocketConnection, collection_id: str) -> None: ...
    def delete_websocket(self, ws_id: str) -> bool: ...
    def rename_websocket(self, ws_id: str, new_name: str) -> bool: ...
    def find_item(self, item_id: str) -> Optional[Tuple[str, object, Collection]]:
        """Resolve an id to ("request" | "websocket", object, owning collection)."""
```

It is constructed with the `RequestManager` (for `get_collections()`, `find_request` and the
`StorageInterface`), rebuilds its index whenever collections reload, and is the object the new
`"websocket"` entry in `DEFAULT_COLLECTION_ITEM_STRATEGIES` dispatches to. The strategy
handlers' first argument therefore becomes the dispatch context (manager plus registry) instead
of the manager alone; `pypost/core/collection_item_strategies.py` (48 LOC) is not capped, and
the dispatch itself moves out of `RequestManager` in the same story (R-1.1).

`AppSettings.open_tabs` stores plain ids (`pypost/core/qt/state_manager.py:76-81`), so restore
must go through the registry's `find_item`. **Restored WebSocket tabs open in `Idle` and never
auto-connect** — a session is a network action and must remain a deliberate one, especially on a
machine that just started.

#### A-4.2 D-3 — the live session is runtime-only

`WebSocketSession` (state, start/end, end reason, stream) has **no** persisted representation.
Only the profile survives a restart. This keeps `state_manager`'s debounced settings writes
(300 ms, `pypost/core/qt/state_manager.py:29`) free of high-churn session data and makes
"closing the app releases connections deterministically" trivially true.

#### A-4.3 Interchange and compatibility

- Export already serializes with `Collection.model_dump(mode="json")`
  (`doc/dev/collection_export.md`), so the new field is included with no export change.
- Import planning must **count** WebSocket entries in its summary, and id reservation must cover
  WebSocket ids exactly as it covers request ids (`doc/dev/collection_import.md`), so an import
  can never collide with an existing profile.
- **Downgrade is lossy and must be released as such** (R-2): a build without WebSocket support
  reads the file safely but drops `websockets` on its next save. This goes in the release notes
  and in `doc/user/collections.md`. No engineering mitigation exists, and pretending otherwise
  with a schema-version field would be theatre.

### A-5 D-6 — UI and interaction architecture (Jira AC (b))

#### A-5.1 Ownership boundaries

- **The `QTabWidget` and the tab bar** stay with `TabsPresenter`, unchanged: it already owns tab
  lifecycle and `open_tabs` persistence.
- **A WebSocket page's content and its session** belong to the new `WebSocketPresenter`.
  `tabs_presenter.py` has 144 lines of cap headroom (R-1.1), so a second protocol does not fit,
  and `doc/dev/presenter_architecture.md` prescribes a presenter per domain.
- **Widgets** in `ui/widgets/websocket/*` do layout and primitive events only — no core
  services, per the MVP split.
- **Collection tree rows for profiles** belong to `CollectionsPresenter` plus a `"websocket"`
  entry in `DEFAULT_COLLECTION_ITEM_STRATEGIES`
  (`pypost/core/collection_item_strategies.py`), because delete and rename already dispatch by
  `item_type`.

`TabsPresenter` grows by three thin methods only (`open_page`, `close_page`,
`set_page_badge`). Everything else about a WebSocket page lives in the new presenter.

#### A-5.2 Session lifecycle — states and transitions

Six user-visible states. `Reconnecting` and `Failed` are PyPost concepts; Qt models neither.

```text
                  +--------------------------------------------+
                  |                                            |
                  v                    connect                 |
            +----------+  ------------------------->  +---------------+
  start --> |   Idle   |                              |  Connecting   |
            +----------+  <-------------------------  +---------------+
                  ^  ^        close / give up            |        |
                  |  |                        opened     |        | handshake
                  |  |                                   v        | rejected,
                  |  |                             +----------+   | DNS, TLS
                  |  |      user disconnect        |   Open   |   |
                  |  +-----------------------------|          |   |
                  |           +----------------->  +----------+   |
                  |           |                      |    |       |
                  |           |  reconnected         |    | peer  |
                  |    +--------------+   drop or    |    | close |
                  |    | Reconnecting |<-------------+    |       |
                  |    +--------------+  heartbeat        |       |
                  |           |          timeout          |       |
                  |           | attempts exhausted        v       v
                  |           |                   +------------------+
                  |           +-----------------> |      Failed      |
                  |                               +------------------+
                  |         user closes tab / disconnect    |
                  +-----------------------------------------+

            +----------+  user disconnect while Open   +----------+
            |   Open   | ----------------------------> | Closing  | --> Idle
            +----------+                               +----------+
```

- **Idle → Connecting** on Connect (button or `Ctrl+Shift+Enter`). The badge reads
  `Connecting…`, the control becomes **Cancel**, and connection fields become read-only.
- **Connecting → Open** when the transport reports opened. The badge reads `Open`, the
  negotiated subprotocol appears in the stream and the header, and the composer is enabled.
- **Connecting → Failed** on a rejected handshake, a DNS failure or a refused TLS peer. The
  badge reads `Failed`, a stream event carries the verbatim reason, and fields become editable.
- **Connecting → Idle** on Cancel, with the stream event `cancelled by user`.
- **Open → Closing → Idle** on user Disconnect. The badge reads `Closing…`, then
  `Closed (1000 normal)`.
- **Open → Idle** on a peer close frame, with the stream event
  `closed by peer: <code> <reason>`.
- **Open → Reconnecting** (or **Failed**, if reconnect is disabled) on a transport error or an
  unanswered heartbeat. The badge reads `Reconnecting 2/5 — retrying in 4 s` and a gap marker
  is written into the stream.
- **Reconnecting → Open** on reconnection, with a stream event stating how long the gap lasted
  and that messages during it were not received.
- **Reconnecting → Failed** when attempts are exhausted. The badge reads
  `Failed — 5/5 attempts`, and there is **no silent retrying**.
- **Failed or Idle → Connecting** on Connect. The stream is retained across reconnects and
  re-connects unless the user clears it.
- **Any state → terminated** when the tab is closed or the application exits: `close(1000)`,
  then `abort()` after a bounded grace period.

Two implementation rules follow:

- The authoritative Open transition is the transport's *opened* callback (`connected`), not
  `stateChanged`. `stateChanged` drives at most a transient "Connecting" hint. OQ-1 requires
  WS-1 to pin the observed ordering with a test rather than assume it.
- The stream **survives** a reconnect by design (S-5.3 requires the gap to be visible); only
  **Clear** empties it.

#### A-5.3 D-13 — editing while connected

| Setting | `Idle` / `Failed` | Connecting, Open, Closing, Reconnecting |
| --- | --- | --- |
| URL, params, headers, subprotocols, TLS | Editable | **Read-only**, hint: `Disconnect to edit` |
| Heartbeat interval/timeout | Editable | Editable — applies from the next tick |
| Reconnect policy | Editable | Editable — applies at the next drop |
| Composer, presets, sequences | Editable | Editable |
| Stream filters, pause, clear, export | Editable | Editable |

This matches Postman's documented behavior (Step 1 benchmark) and removes the "I changed the
header but nothing happened" failure class.

#### A-5.4 Wireframe — session tab, connected

```text
+- pypost_request_tabs -----------------------------------------------------------+
| [ GET /users ] [ (*) ws Order Book ] [ (~) ws Chat ] [ (x) ws Telemetry ] [ + ]  |
+---------------------------------------------------------------------------------+
| pypost_ws_url_input                                                             |
| +--------------------------------------------+ +------------+ +-----------+     |
| | wss://{{host}}/v2/stream?token={{API_TOKEN}}| | Disconnect | | Actions v |     |
| +--------------------------------------------+ +------------+ +-----------+     |
| (*) Open . json.v2 . 00:14:07 . 1 284 msgs . 3.1 MB  [pypost_ws_state_badge]     |
+- pypost_ws_detail_tabs ---------------------------------------------------------+
| | Params | Headers | Subprotocols | Settings | Messages | MCP |                  |
| +-----------------------------------------------------------------------------+ |
| |  read-only while connected - "Disconnect to edit connection settings"        | |
| |  Key                    Value                                               | |
| |  Authorization          Bearer {{API_TOKEN}}   <- hover shows ********       | |
| |  X-Client               pypost                                              | |
+---------------------------------------------------------------------------------+
| +- Stream - pypost_ws_stream_view --------------------------------------------+ |
| | [Search...    ] Dir:[All v] Kind:[All v] [Pause] [Clear] [Export v] 1284/5000| |
| | (!) 412 messages dropped (capacity)                                         | |
| +-----------------------------------------------------------------------------+ |
| | 12:04:01.220  (i)  handshake accepted . subprotocol json.v2                 | |
| | 12:04:01.221   ->  {"op":"subscribe","channel":"orders","token":"********"}  | |
| | 12:04:01.402   <-  {"type":"ack","channel":"orders"}                   38 B | |
| | 12:04:02.004   <-  {"type":"delta","seq":18841,"px":"70112.5"}         96 B | |
| | 12:04:31.000  (i)  heartbeat ok (18 ms)      [hidden unless "Show events"]  | |
| | 12:05:02.771  (!)  connection lost - reconnecting 1/5 in 1 s                | |
| | 12:05:03.902  (i)  reconnected after 1.1 s - messages in the gap were lost  | |
| +- pypost_ws_stream_detail ---------------------------------------------------+ |
| | <- incoming . text . 96 B . 12:04:02.004                                    | |
| |    [Copy] [Set as variable...] [Wrap] [Hex]                                 | |
| | {                                                                           | |
| |   "type": "delta", "seq": 18841, "px": "70112.5", "qty": "0.42"             | |
| | }                                                                           | |
| +-----------------------------------------------------------------------------+ |
+- Composer - pypost_ws_composer_edit --------------------------------------------+
| Format:[JSON v]  Preset:[subscribe v][Save...]  Sequence:[login+sub v][Run][Stop]|
| +-----------------------------------------------------------------------------+ |
| | {"op":"subscribe","channel":"{{channel}}"}                                  | |
| +-----------------------------------------------------------------------------+ |
|                                                  [ Send message (Ctrl+Enter) ]  |
+---------------------------------------------------------------------------------+
```

#### A-5.5 Wireframe — tab-strip state indicators (never colour alone)

```text
[ (o)  ws Order Book ]   Idle / closed        (o) = hollow circle
[ (~)  ws Chat       ]   Connecting or Reconnecting (marker animates)
[ (*)  ws Telemetry  ]   Open                 (*) = filled circle
[ (x)  ws Legacy     ]   Failed
[ (*)  ws Feed  (12) ]   Open, 12 unread since the tab last had focus
```

Every state is carried by a **marker plus text** in the tooltip and in the in-page badge, so
the accessibility NFR ("state conveyed by more than colour alone") holds. Colour is
decoration; in the shipped UI these markers are icons, and the ASCII forms above stand in for
them.

#### A-5.6 Wireframe — first-run and error states

```text
Idle, never connected                  Handshake rejected
+-------------------------------+      +------------------------------------------+
|  No session yet.              |      | (x) Failed                               |
|  Enter a ws:// or wss:// URL  |      | Handshake rejected by the server.        |
|  and choose Connect.          |      | Qt reported: "Connection closed"         |
|                               |      | (HTTP status is not available for a      |
|  Ctrl+Shift+Enter connects.   |      |  WebSocket handshake - see docs)         |
+-------------------------------+      | [Edit connection]     [Retry]            |
                                       +------------------------------------------+

Filter matches nothing                 Reconnect exhausted
+-------------------------------+      +------------------------------------------+
| No messages match "orderId".  |      | (x) Failed after 5/5 reconnect attempts. |
| 1 284 hidden by the current   |      | Last error: the peer did not answer the  |
| filter.  [Clear filter]       |      | heartbeat within 10 s.  [Connect]        |
+-------------------------------+      +------------------------------------------+
```

#### A-5.7 Automation identities and keyboard access

New constants in `pypost/ui/widget_ids.py`, following the `pypost_` snake_case rule and the
per-tab role convention (`doc/dev/ui_identity.md`):

`pypost_ws_tab_page`, `pypost_ws_url_input`, `pypost_ws_connect_button`,
`pypost_ws_state_badge`, `pypost_ws_detail_tabs`, `pypost_ws_params_table`,
`pypost_ws_headers_table`, `pypost_ws_subprotocols_input`, `pypost_ws_stream_view`,
`pypost_ws_stream_search_input`, `pypost_ws_stream_direction_filter`,
`pypost_ws_stream_kind_filter`, `pypost_ws_stream_pause_button`,
`pypost_ws_stream_clear_button`, `pypost_ws_stream_export_button`,
`pypost_ws_stream_drop_notice`, `pypost_ws_stream_detail`, `pypost_ws_composer_edit`,
`pypost_ws_composer_format_combo`, `pypost_ws_send_message_button`,
`pypost_ws_preset_combo`, `pypost_ws_sequence_combo`, `pypost_ws_sequence_run_button`,
`pypost_ws_sequence_stop_button`.

The presets and sequences surface (A-5.8) adds `pypost_ws_messages_tab`,
`pypost_ws_presets_list`, `pypost_ws_preset_name_input`, `pypost_ws_preset_format_combo`,
`pypost_ws_preset_payload_edit`, `pypost_ws_preset_new_button`,
`pypost_ws_preset_duplicate_button`, `pypost_ws_preset_delete_button`,
`pypost_ws_preset_load_button`, `pypost_ws_preset_send_button`,
`pypost_ws_preset_save_button`, `pypost_ws_sequences_list`,
`pypost_ws_sequence_new_button`, `pypost_ws_sequence_duplicate_button`,
`pypost_ws_sequence_delete_button`, `pypost_ws_sequence_steps_table`,
`pypost_ws_sequence_step_add_button`, `pypost_ws_sequence_step_remove_button`,
`pypost_ws_sequence_step_up_button`, `pypost_ws_sequence_step_down_button`.

The key ones join `KEY_WIDGET_IDS` and the spot-check in
`tests/test_ui_identity_spotcheck.py`. Each story extends that spot-check for the ids it
introduces — WS-4 for the tab, connection and state ids, WS-5 for the stream ids, WS-6 for
the composer, preset and sequence ids — so no story inherits another's identity debt
(A-14).

Hotkeys — a new `"WebSocket Session"` section in `SECTION_ORDER`
(`pypost/ui/hotkeys.py:17`), reusing the existing scheme wherever the analogy holds:

| Action | Shortcut | Analogy |
| --- | --- | --- |
| Send message | `Ctrl+Enter` / `F5` | Send Request |
| Connect / Disconnect | `Ctrl+Shift+Enter` | new; deliberately distinct from Send |
| Focus URL | `Ctrl+L` / `Alt+D` | Focus URL Bar |
| Params / Headers sub-tab | `Ctrl+P` / `Ctrl+H` | identical to the request editor |
| Composer sub-pane | `Ctrl+B` | Body |
| Focus stream search | `Ctrl+F` | response search (`doc/dev/response_search.md`) |
| Focus stream | `Ctrl+M` | new (free) |
| Clear stream | `Ctrl+K` | new (free) |

None of these collide with the shortcuts listed in `doc/user/hotkeys.md`.

#### A-5.8 Wireframe and interaction — presets and sequences surface (FR-5.6)

Presets and sequences live in the **`Messages`** sub-tab of `pypost_ws_detail_tabs` (the tab
strip shown in A-5.4), so they travel with the profile, stay reachable while the stream runs,
and remain editable in every session state (A-5.3). The composer's combos are shortcuts into
this surface, not a second home for the data.

```text
+- pypost_ws_detail_tabs > Messages -----------------------------------------------+
| Saved messages                                     Preset detail                 |
| +- pypost_ws_presets_list ------+ +---------------------------------------------+|
| | subscribe              json   | | Name   [ subscribe                        ] ||
| | ping                   text   | | Format [ JSON v ]  (pypost_ws_preset_*)     ||
| | auth                   json   | | Payload                                     ||
| | replay-frame           hex    | | {"op":"subscribe","channel":"{{channel}}"}  ||
| |                               | |                                             ||
| +-------------------------------+ +---------------------------------------------+|
| [New] [Duplicate] [Delete]          [Load into composer] [Send now] [Save]       |
+----------------------------------------------------------------------------------+
| Sequences                                          Steps of "login+sub"          |
| +- pypost_ws_sequences_list ----+ +---------------------------------------------+|
| | login+sub          3 steps    | | # | Message         | Format | Delay before ||
| | replay-bug-412     7 steps    | | 1 | auth (preset)   | json   |        0 ms  ||
| |                               | | 2 | subscribe       | json   |      250 ms  ||
| |                               | | 3 | <inline>        | text   |    1 000 ms  ||
| +-------------------------------+ +---------------------------------------------+|
| [New] [Duplicate] [Delete]   [Add step][Remove][Up][Down]   [Run] [Stop]         |
+----------------------------------------------------------------------------------+

Empty states
+-------------------------------------+ +--------------------------------------+
| No saved messages yet. Compose one  | | No sequences yet.                    |
| and choose Save... in the composer, | | [New sequence] builds one from saved |
| or [New].                           | | messages or inline payloads.         |
+-------------------------------------+ +--------------------------------------+
```

Interaction rules:

- **Creation.** The primary path is the composer: `Save…` next to `pypost_ws_preset_combo`
  stores the composer's current text and format as a new preset on the profile and selects it.
  `[New]` in the `Messages` sub-tab is the secondary path and starts from an empty payload.
- **Editing.** Single-selection master/detail. Edits apply to the in-memory profile immediately
  and are persisted through WS-2's profile CRUD (`WebSocketRegistry.save_websocket`), the same
  write path as a rename — so a preset created mid-session survives a restart.
- **Running one message.** `Send now` sends the selected preset directly and is enabled only
  while the session is `Open`, with the same refusal message as WS-6 AC 7. `Load into composer`
  puts the preset in the composer for editing and works in every state.
- **Sequence steps.** Each step is either a **preset reference** or an **inline payload** with
  its own format, plus `delay_ms` applied **before** that step
  (`WebSocketSequenceStep.delay_ms`, A-4.1). A step whose preset was deleted is shown as
  `<missing preset>` and blocks `Run` with a named reason rather than being skipped silently.
- **Running a sequence.** `Run` (also `pypost_ws_sequence_run_button` in the composer strip) is
  enabled only while `Open`; every step appears in the stream as an ordinary outgoing entry; a
  failing step stops the run and writes a lifecycle entry naming the step index and the reason;
  `Stop` halts before the next step and leaves the session open (A-13.6 AC 3-5).
- **Templating and masking.** Preset and step payloads are stored as templates and resolved per
  send (A-7); what reaches the stream is masked exactly like any other outgoing frame (A-3.1),
  so a preset containing `{{ API_TOKEN }}` is safe to save, export and screenshot.
- **Keyboard.** The surface is reached with the detail-tab navigation already defined in A-5.7;
  it adds no new global shortcut, because `Ctrl+Enter` must keep meaning "send the composer".

### A-6 D-8 — Message stream data handling

#### A-6.1 The entry and the bound

```python
@dataclass(frozen=True)
class StreamEntry:
    seq: int                 # monotonic within a session; the model's stable row identity
    ts_utc: str              # ISO-8601 with milliseconds
    kind: str                # "message" | "lifecycle"
    direction: str           # "in" | "out" | "none"
    payload_format: str      # WsMessageFormat value
    payload: str             # already masked; truncated to display_truncate_bytes
    byte_size: int           # true wire size, even when payload is truncated
    truncated: bool
    detail: str = ""         # lifecycle reason, close code, error text
```

`MessageStream` is a Qt-free bounded ring built on `collections.deque` with **two** eviction
dimensions, because either alone is insufficient: an entry cap does not bound memory when
messages are large, and a byte budget alone does not bound the row count a view must manage.

```python
class MessageStream:
    """Bounded, append-only session record with drop accounting.

    Eviction is oldest-first and happens when either bound is exceeded:
      * ``max_entries``          — default 5 000
      * ``memory_budget_bytes``  — default 64 MiB of retained payload
    Every eviction increments a counter keyed by the bound that caused it, so the
    UI can state exactly how much was lost and why.
    """

    def append(self, entry: StreamEntry) -> tuple[int, str | None]: ...
    def snapshot(self) -> Sequence[StreamEntry]: ...
    def matching(self, query: StreamQuery) -> Sequence[int]: ...
    def clear(self) -> None: ...
    @property
    def dropped(self) -> Mapping[str, int]: ...   # {"capacity": n, "memory_budget": m}
```

Worst case is therefore bounded at `min(5 000 entries, 64 MiB)` per session, independent of
peer behavior. With the defaults, an adversarial peer sending 256 KiB messages fills the budget
after 256 entries and then evicts steadily — memory is flat, and the UI says so.

A per-session bound is not a process bound: ten open tabs would be ten rings. The
process-wide ceiling that closes that gap is `ws_max_concurrent_sessions` (D-14), specified
in [A-12.1](#a-121-d-14--the-concurrent-session-ceiling); the retained-payload worst case
for the whole application is `ws_max_concurrent_sessions × ws_session_memory_budget_bytes`
— 8 × 64 MiB = 512 MiB with the defaults.

#### A-6.2 Three limits, three different jobs

- **`ws_max_incoming_message_bytes`** — default 8 MiB, enforced by
  `QWebSocket.setMaxAllowedIncomingMessageSize()`. At the bound Qt aborts the connection;
  PyPost writes a lifecycle entry (`message exceeded 8 MiB — connection closed by client`) and
  moves to `Failed`.
- **`ws_display_truncate_bytes`** — default 256 KiB, enforced in `MessageStream.append`. At the
  bound the entry retains the first 256 KiB with `truncated=True`, the detail pane shows a
  marker, and `byte_size` still reports the true wire size.
- **`ws_session_memory_budget_bytes`** — default 64 MiB, enforced by `MessageStream` eviction.
  At the bound the oldest entries are dropped, `dropped["memory_budget"]` increments, and a
  banner shows the running total.

Precedent for the shape of this: HTTP already caps bodies at
`max_response_bytes = 52_428_800` and counts `response_body_truncated`
(`pypost/models/settings.py:64`, `pypost/core/metrics_registry.py:123`).

#### A-6.3 Rendering strategy for high-rate streams

- **Model/view, not item widgets.** `StreamListModel(QAbstractListModel)` over the ring, shown
  in a `QListView` with a custom delegate. Qt instantiates delegates only for visible rows, so
  a 5 000-entry stream costs a constant number of paint calls. This is deliberately **not** the
  `QListWidget` approach used by `HistoryPanel`
  (`pypost/ui/widgets/history_panel.py:72,129-146`), which rebuilds a `QListWidgetItem` per
  entry on every filter keystroke — acceptable for 500 history rows, not for a live stream.
- **Coalesced intake.** Incoming frames append to a pending batch; a single-shot `QTimer` at
  **33 ms** flushes the batch with one `beginInsertRows`/`endInsertRows` pair. This is the same
  interval and the same reasoning as the streamed-HTTP chunk buffer
  (`doc/dev/response-streaming-display.md`, `_chunk_flush_ms = 33`). At any incoming rate the
  view performs ≈ 30 model transactions per second.
- **Front eviction as a model operation.** Dropping the oldest N entries is one
  `beginRemoveRows(0, n-1)`; `seq` keeps row identity stable for the selected entry.
- **Auto-follow, not auto-scroll.** The view follows the tail only while it is *at* the tail.
  Scrolling up detaches following and shows `↓ 128 new messages` as a click-to-return control.
- **Filtering** through a `QSortFilterProxyModel` whose `filterAcceptsRow` delegates to the
  Qt-free `StreamQuery` predicate, so filter semantics are unit-tested without Qt.
- **Lifecycle noise control.** Heartbeat entries are recorded but hidden behind a
  `Show lifecycle events` toggle, defaulting to showing only non-routine lifecycle events
  (handshake, close, reconnect, error). This satisfies S-7.2 ("keeps the session open without
  flooding the stream with noise").

#### A-6.4 Backpressure — the honest answer

RFC 6455 defines **no application-level flow control**. A client cannot ask a peer to slow
down. The design therefore states plainly what each lever does:

- **`setReadBufferSize()`** bounds the transport read buffer. It helps memory; it does not
  throttle a peer that keeps sending.
- **Pause display** *(offered)* stops the view following the tail. The socket keeps reading and
  the ring keeps evicting, so nothing is lost beyond normal eviction.
- **Pause intake** *(deliberately not offered)* would only mean "stop draining the socket",
  inflating OS and Qt buffers until the connection dies unpredictably. Refusing to offer it is a
  design decision, not an omission.
- **Drop-oldest with visible counters** is the real memory guarantee, and the user is told the
  exact count and its cause.
- **Disconnect** is the only true backpressure a WebSocket client has, and it is one button.

#### A-6.5 Export

Two formats, both fully masked ([A-8](#a-8-security-and-secret-handling)):

- **JSON transcript** — a JSON array of entry objects, written through the existing
  `pypost/core/export_file_writer.py::write_json_export_file` so error wrapping and directory
  creation stay identical to collection and environment export (`doc/dev/collection_export.md`).
  Reusing the existing writer is the reason for a JSON array rather than NDJSON.
- **Plain-text transcript** — `ts direction size payload` lines, for pasting into a defect
  report.

Export writes what the ring **retained**, and the header records `dropped` counts so a
transcript never silently pretends to be complete.

### A-7 D-7 — Environments and templating

- **URL, query params, headers, subprotocols** — resolved **once, at connect**. The handshake
  happens once; re-resolving mid-session would misrepresent what was actually sent.
- **Message payloads** (composer, preset, sequence step) — resolved **per send**, so a value
  captured mid-session (S-3, FR-2.5) takes effect on the next message.
- **Received payloads** — **never** resolved. Rendering server-controlled text through Jinja2
  would be a template-injection vector. This is explicit non-behavior and a required test.

Resolution goes through the injected `TemplateService` (`doc/dev/template_service.md`), the same
instance the presenters already propagate, so expression functions and hidden-key semantics are
identical to HTTP. `WebSocketPresenter` receives variables and hidden keys from `EnvPresenter`
through the existing propagation chain (`doc/dev/variable_propagation.md`) and pushes them to
the variable-aware widgets in the connection editor using `VariableHoverMixin`
(`doc/dev/ui_mixins.md`), so `{{ API_TOKEN }}` hovers show `********` exactly as in the request
editor.

FR-2.5's "capture values received from the stream back into the environment" is served by a
**Set as variable…** action in the stream detail pane, reusing the `variable_set_requested`
signal already implemented on `ResponseView`
(`pypost/ui/widgets/response_view.py:273`) — no new mechanism, and no scripting
([A-11](#a-11-coexistence-decisions-fr-6)).

### A-8 Security and secret handling

#### A-8.1 What is stored

`WebSocketConnection` stores **templates only** — the same rule and the same risk profile as
`RequestData` in collection JSON, which is plaintext by design
(`doc/dev/collection_storage.md`). Secrets belong in hidden environment variables, which are
the only values encryptable at rest (`doc/dev/environment_encryption_at_rest.md`). The user
documentation for WebSocket must repeat that guidance verbatim.

#### A-8.2 Masking, in two tiers

The distinction matters because over-masking destroys the data the user is debugging, while
under-masking leaks a token.

- **Live stream view, outgoing entries and handshake events** — exact replacement of
  hidden-variable values with `HIDDEN_PLACEHOLDER` before the entry is appended. The user sees
  the shape of what they sent, never the secret.
- **Live stream view, incoming entries** — exact hidden-value replacement only. No heuristic
  pass: a server payload is the artefact under inspection and must not be mangled.
- **Clipboard copy, file export, MCP transcript** — full
  `sanitize_text(value, env_vars=…, hidden_keys=…)`, the same heuristic pass used for history
  and MCP results (`pypost/core/sensitive_text_sanitizer`,
  `doc/dev/sensitive_data_masking_policy.md`).
- **Logs** — no payload text at any level. See [A-8.4](#a-84-what-must-never-be-logged).
- **Metrics labels** — fixed low-cardinality values only (`direction`, `kind`, `outcome`,
  `reason`); never a URL, host, header or payload.

Masking happens in `WebSocketPresenter` **before** the entry reaches `MessageStream`,
through the pure `build_stream_entry(frame, *, env_vars, hidden_keys, truncate_bytes)`
function of A-3.1 — the presenter is the only component that holds `env_vars` and
`hidden_keys`, and `StreamListModel` is the only writer of the ring. No unmasked secret is
ever retained in the buffer that Export and Copy read from. This is the same "mask at write
time, consumers handle only safe values" invariant that history already enforces
(`doc/dev/sensitive_data_masking_policy.md`, "Invariants").

`hidden_value_masks_applied_total{surface="websocket"}` reuses the existing counter and its
`surface` label (`pypost/core/metrics_registry.py:160`).

#### A-8.3 D-12 — TLS for `wss://`

- The session uses Qt's **default** `QSslConfiguration`: full certificate-chain and hostname
  verification.
- **`QWebSocket.ignoreSslErrors()` is forbidden in production code.** WS-8 ships a guard test
  that fails if the symbol appears anywhere under `pypost/`, following the precedent of the
  existing style-guard tests.
- On `sslErrors` / `peerVerifyError`, the session stops and shows the specific errors. Any
  override is **per session, defaulted to reject, and never written to disk**. Persisted
  certificate exceptions are follow-up FU-6, deliberately excluded so that no trust decision can
  outlive the window it was made in.
- `ws://` to any non-loopback host renders a persistent `plaintext` warning next to the state
  badge, because a token in a header on a plaintext socket is a credential on the wire.
- Authentication is expressed as ordinary handshake headers or query parameters sourced from
  hidden environment variables — no bespoke auth store, so the existing MCP secrets policy and
  masking apply unchanged.

#### A-8.4 What must never be logged

Never, at any level: message payloads (incoming or outgoing), handshake header **values**,
resolved URLs containing query strings, close reasons echoed from a peer, preset or sequence
payload text, `pong` payloads.

Logged instead, as `snake_case key=value` per `doc/dev/logging.md`:

```text
websocket_connect_initiated  session_id=… profile_id=… url_masked=… subprotocols=2
websocket_connected          session_id=… subprotocol=json.v2 handshake_ms=142
websocket_handshake_failed   session_id=… category=tls detail_len=57
websocket_closed             session_id=… close_code=1000 peer_initiated=false duration_s=847
websocket_reconnect_scheduled session_id=… attempt=2 max_attempts=5 delay_ms=4000
websocket_reconnect_exhausted session_id=… attempts=5
websocket_heartbeat_timeout  session_id=… timeout_s=10
websocket_stream_overflow    session_id=… dropped=412 reason=capacity
websocket_session_refused    profile_id=… reason=max_concurrent active=8 limit=8
websocket_probe_completed    tool=order_book outcome=success messages=7 duration_ms=2411
```

`url_masked` is produced by `sanitize_text`, never the raw resolved URL. This mirrors the
existing rule "Never log chunk body text" (`doc/dev/response-streaming-display.md`).

### A-9 D-4 — History (FR-6.5)

**Decision: WebSocket sessions do not enter request history in this epic.**

- `HistoryEntry` requires `status_code: int` and `response_time_ms: float`
  (`pypost/models/models.py:105-115`). A session has neither. Filling them with sentinels would
  make `[404] …` and `[0] …` rows indistinguishable in a panel whose label format is
  `[method] timestamp status\nurl` (`pypost/ui/widgets/history_panel.py:136-140`).
- `HistoryManager` retains `DEFAULT_MAX_ENTRIES = 500` (`pypost/core/history_manager.py:18`).
  One busy session would evict a user's entire HTTP history within seconds if messages were
  recorded, and would rewrite `history.json` continuously.
- The panel's filter is URL-substring only (`pypost/ui/widgets/history_panel.py:129-136`), and
  `Copy as cURL` is offered on every history row (`doc/dev/copy_curl.md`) — meaningless for a
  session.
- No FR-2 journey needs it. The user need behind "what happened in that session" is served by
  the retained stream and by transcript export ([A-6.5](#a-65-export)).

**Deferred, recorded as FU-2:** one *session summary* entry (opened at, closed at, end reason,
message counts) written on close. That requires `HistoryEntry` to gain an entry kind and to make
status/time optional — a change to a persisted model that `HistoryPanel`, `CurlGenerator` and
the masking tests all depend on. It is additive and can land later without reopening any
decision here.

### A-10 D-5 — MCP and agents (FR-6.7)

**Decision: a WebSocket connection profile is MCP-exposable as a bounded, one-shot probe tool.
A persistent, agent-held session is explicitly out of scope.**

#### A-10.1 How a long-lived stream fits a request/response tool call

It does not — so it is not made to. Instead, PyPost reuses the shape it already applies to the
other streaming protocol it supports: Server-Sent Events are handled as a bounded probe of at
most `SSE_PROBE_MAX_EVENTS = 5` events over `SSE_PROBE_TIMEOUT = 10.0` seconds, summarized into
a single body (`pypost/core/http_client.py:28-30`, `doc/dev/request_execution.md`). The
WebSocket probe is the same pattern with WebSocket semantics:

```text
call_tool(name, arguments)
  → resolve environment variables + agent-supplied mcp.request.* parameters
  → connect (handshake headers/subprotocols from the profile)
  → send the designated probe preset, if the profile names one
  → collect incoming messages until the FIRST of:
        max_messages          (profile override, else ws_mcp_probe_max_messages = 10)
        max_duration_ms       (profile override, else ws_mcp_probe_max_duration_ms = 10 000)
        a stop_when substring match supplied as a tool argument
  → close(1000, "probe complete")
  → return ONE masked transcript as List[TextContent]
```

This fits `MCPServerImpl.call_tool`'s existing contract exactly: one call, one
`List[TextContent]`, executed off the loop thread, already bounded by
`DEFAULT_MAX_CONCURRENT_MCP_CALLS` (`pypost/core/mcp_server_impl.py:105,130-183`).

#### A-10.2 Where it runs

The MCP tool call happens on uvicorn's asyncio loop inside `MCPServerManager`'s thread
(`pypost/core/qt/mcp_server.py:222-246`), where no Qt event loop exists. `WebSocketProbeRunner`
is therefore a short-lived `QThread` that starts a `QWebSocket` and calls `exec()` on its own
event loop, with a hard-deadline `QTimer` that quits the loop unconditionally. The calling
thread waits with a bounded `wait()`; on expiry the runner is aborted.

This is safe **because the probe is bounded by construction** — which is precisely the property
a persistent session would lack, and the core reason the persistent form is excluded.

#### A-10.3 Why not a persistent agent-held session

- It requires server-side session state keyed by a handle, plus a reaper: MCP gives no guarantee
  that a client will ever call `ws_close`, and an abandoned handle is an open socket and an
  unbounded buffer.
- Under `pypost-daemon` there is no GUI, so no human can see or stop such a session
  (`doc/dev/daemon.md`). That contradicts the "bounded resource use" NFR and the trust posture
  in `doc/dev/mcp_trust_model.md`.
- No FR-2 journey requires it. Recorded as **FU-3**; the probe tool and the transport seam are
  both compatible with adding it later.

#### A-10.4 Agent-visible contract

`list_tools` reuses `McpSecretsPolicy` unchanged: only `mcp.request.*` placeholders become tool
parameters; environment and hidden variables are stripped from the schema and merged only at
call time (`doc/dev/mcp_secrets_policy.md`). The WebSocket editor's MCP sub-tab shows the same
`format_mcp_tool_contract_preview` output as the request editor
(`pypost/core/mcp_tool_contract.py`), so the "what will my agent see" affordance is identical.

Transcript sanitization goes through the same `sanitize_text` path used by
`format_structured_tool_result` (`pypost/core/mcp_server_impl.py:55-88`).

**Daemon integration item:** `pypost.core.daemon_storage`'s strict snapshot loaders return only
the records enabled MCP servers need (`doc/dev/daemon.md`). They must be extended to include
`Collection.websockets`, or WebSocket tools will silently disappear in headless mode. This is
explicit acceptance criteria on WS-9.

### A-11 Coexistence decisions (FR-6)

- **FR-6.1 Collections — in scope.** A new `Collection.websockets` list; profiles appear in the
  same tree under the same collection with a distinct icon and item type.
  *For the user:* related HTTP and real-time surfaces stay in one place.
- **FR-6.2 Import/export — in scope.** Export is automatic through `model_dump`; import counts
  and id-reserves profiles. *For the user:* a round trip preserves profiles, presets and
  sequences, but **downgrading to a build without WebSocket support is lossy** (R-2) and is
  release-noted.
- **FR-6.3 Environments and templating — in scope.** Handshake at connect, payloads per send,
  received data never rendered ([A-7](#a-7-d-7--environments-and-templating)).
  *For the user:* one profile serves local, staging and production.
- **FR-6.4 Hidden values — in scope.** Two-tier masking (A-8.2), applied before the buffer.
  *For the user:* debugging a live session cannot leak a token.
- **FR-6.5 History — excluded from the epic**, FU-2 recorded ([A-9](#a-9-d-4--history-fr-65)).
  *For the user:* sessions are not in the History panel; transcript export replaces it.
- **FR-6.6 Scripting — excluded from the epic**, FU-4 recorded. `ScriptExecutor` is a
  post-**response** hook running exactly once (`pypost/core/script_executor.py`,
  `doc/user/scripts.md`); a stream has no single response, and user Python per message on the
  GUI thread is untenable. *For the user:* variable capture is a stream context-menu action.
- **FR-6.7 MCP and agents — in scope as a bounded probe**; persistent sessions excluded, FU-3
  recorded ([A-10](#a-10-d-5--mcp-and-agents-fr-67)). *For the user:* agents can sample a
  real-time endpoint; they cannot hold a socket open.
- **FR-6.8 Headless daemon — in scope only for the probe**; the daemon never holds long-lived
  sessions. *For the user:* headless MCP works and nothing runs unattended forever.
- **FR-6.9 Copy as cURL — excluded.** `CurlGenerator` is HTTP-specific
  (`pypost/core/curl_generator.py`, `doc/dev/copy_curl.md`). Sharing is **Copy connection as
  JSON** (masked) plus transcript export; a `websocat`/`wscat` snippet is FU-5.
  *For the user:* the Actions menu offers the two affordances that need no external tool.
- **FR-6.10 Settings — in scope.** Global bounds and defaults in `AppSettings`; per-profile
  overrides on `WebSocketConnection` ([A-12](#a-12-settings-split)); a process-wide
  concurrent-session ceiling (D-14,
  [A-12.1](#a-121-d-14--the-concurrent-session-ceiling)) so the operator bound covers the
  application and not only one session.
  *For the user:* operators bound the app and users tune one endpoint.
- **FR-6.11 Observability — in scope.** New counters and log events following existing
  conventions (A-13.10, A-8.4). *For the user:* sessions are diagnosable and countable.

### A-12 Settings split

New `AppSettings` fields, all default-valued so existing `settings.json` files load unchanged
(`pypost/models/settings.py`):

| Field | Default | Meaning |
| --- | ---: | --- |
| `ws_max_stream_entries` | 5 000 | Ring entry cap per session |
| `ws_session_memory_budget_bytes` | 67 108 864 | Retained payload budget per session (64 MiB) |
| `ws_max_incoming_message_bytes` | 8 388 608 | Passed to `setMaxAllowedIncomingMessageSize` |
| `ws_display_truncate_bytes` | 262 144 | Per-entry retained payload cap (256 KiB) |
| `ws_default_heartbeat` | enabled, 30 s / 10 s | Default `HeartbeatPolicy` for new profiles |
| `ws_default_reconnect` | on, 5, 1 s, ×2, 30 s max | Default `ReconnectPolicy` for new profiles |
| `ws_mcp_probe_max_messages` | 10 | Hard ceiling for the MCP probe |
| `ws_mcp_probe_max_duration_ms` | 10 000 | Hard ceiling for the MCP probe |
| `ws_max_concurrent_sessions` | 8 | Live sockets allowed process-wide (D-14, A-12.1) |

Per-profile overrides: `heartbeat`, `reconnect`, `mcp_probe_*`. Global values are **ceilings**
for the MCP probe (a profile may lower them, never raise them), so an agent-reachable tool
cannot be configured past the operator's bound.

The same downgrade caveat as R-2 applies to `settings.json`, with negligible impact: an old
build drops the `ws_*` keys and the user re-enters preferences.

#### A-12.1 D-14 — the concurrent-session ceiling

Every other bound in this design is *per session*. Without a ceiling on the number of
sessions, ten tabs are ten rings and the operator NFR "bounded resource use" is only half
served, so FR-6.10 gets one more global control:

- **What it counts.** Live sockets process-wide: connected or connecting GUI sessions,
  **plus** in-flight MCP probes (A-10), so an agent cannot walk around the operator's bound.
  Probes remain additionally bounded by `DEFAULT_MAX_CONCURRENT_MCP_CALLS = 4`
  (`pypost/core/mcp_server_impl.py:38`).
- **Where it is enforced.** A slot counter in the Qt-free `websocket_session_policy.py`
  (`SessionSlots.acquire()` / `release()`), so the rule is unit-testable without a socket
  and identical in GUI and headless mode. A slot is taken when a connect is initiated and
  released on any terminal transition (`Idle`, `Failed`) or on probe completion.
- **Thread safety.** GUI-thread connects and MCP-threadpool probes (`run_in_threadpool`, R-1)
  both call `acquire()`/`release()` on the same process-wide `SessionSlots` instance, so it
  guards its counter with a `threading.Lock` around every mutation — the same idiom
  `McpActivityLog` already uses for a counter shared across those two threads
  (`pypost/core/mcp_activity_log.py:87-95`). `acquire()` returns the refusal outcome inside the
  locked section so the check-and-increment is atomic; no `asyncio` primitive is involved.
- **What the user sees at the ceiling.** Opening a profile in a tab is always allowed —
  editing is not a network action. **Connect** is refused: the badge stays `Idle`, a
  lifecycle entry and an inline message read `8 of 8 WebSocket sessions are already open —
  disconnect one to start another`, and the Connect control stays enabled so the user can
  retry after freeing a slot. Nothing is queued; there is no hidden retry.
- **What an agent sees at the ceiling.** `call_tool` returns a normal (non-crashing) result
  stating the ceiling was reached, so the agent can retry later.
- **Observability.** `websocket_session_start_refused_total{reason="max_concurrent"}` and
  the `websocket_session_refused` log event (A-8.4); the new
  `websocket_active_sessions` gauge, introduced by WS-10 alongside these counters
  (A-13.10), makes the current occupancy visible.
- **Value 0** disables WebSocket connecting entirely — the deliberate lockdown setting for a
  managed deployment; the UI states that reason rather than showing a generic refusal.

Assigned to **WS-10** (A-13.10), which already owns the `ws_*` settings surface, the gauge
and the metrics.

### A-13 Implementation breakdown — stories for Epic PYPOST-1123

Twelve stories, 79 story points in eight waves (P-2). Each is independently mergeable,
independently reviewable, and leaves the application working when merged alone. Estimates are
Fibonacci story points. This list is the input for the Jira-creation phase; each entry is
written to be implementable without reading anything else in this document.

#### A-13.1 WS-1 — WebSocket transport seam and Qt-native session engine

- **Points: 8** · **Depends on:** none (verified against WS-11's fixture) ·
  **Parallel with:** WS-2, WS-11
- **Goal.** Give PyPost a working, testable WebSocket session engine with no user interface, so
  every later story builds on a proven foundation.
- **Scope.** `pypost/core/websocket_transport_protocol.py` (Qt-free `WebSocketTransport` /
  `WebSocketTransportListener` protocols and `HandshakeTarget`);
  `pypost/core/websocket_session_policy.py` (pure state machine, reconnect backoff schedule,
  heartbeat policy); `pypost/core/qt/websocket_transport.py` (the sole `QtWebSockets` adapter);
  `pypost/core/qt/websocket_session.py` (`WebSocketSessionController(QObject)` with the signal
  surface in A-3, re-emitting `RawFrame` values **unmasked** and owning no `MessageStream`
  — the ownership rule in A-3.1). No widgets, no persistence, no MCP.
- **Acceptance criteria.**
  1. Connecting to the local echo server reaches `Open` and reports the negotiated subprotocol.
  2. Text and binary messages round-trip in both directions.
  3. A server-initiated close surfaces the numeric close code and the reason text verbatim.
  4. A rejected handshake surfaces a specific reason (not a generic "connection failed") and
     ends in `Failed`.
  5. Heartbeat sends `ping` on the configured interval; an unanswered `pong` within the timeout
     ends the session with reason `heartbeat_timeout`.
  6. A dropped connection retries with the configured bounded backoff, emits attempt progress,
     and ends in `Failed` with `reconnect_exhausted` when attempts run out — with no further
     retrying.
  7. `ws_max_incoming_message_bytes` is applied to the socket; an oversize message ends the
     session with an explanatory reason instead of allocating.
  8. Closing a controller releases the socket and leaves no live `QObject` or thread (asserted).
  9. A guard test fails if `PySide6.QtWebSockets` is imported anywhere under `pypost/` other
     than `pypost/core/qt/websocket_transport.py`.
  10. The observed ordering of the transport's opened callback relative to socket state changes
      is pinned by a test (OQ-1).
  11. The controller holds no stream and no masking inputs: a test asserts that
      `pypost/core/qt/websocket_session.py` imports neither `websocket_stream` nor any
      environment type, and that frames reach listeners unmodified (A-3.1).
- **Out of scope.** UI, persistence, templating, masking, the stream ring (WS-3), MCP.

#### A-13.2 WS-2 — Connection profile model, persistence and collection interchange

- **Points: 8** · **Depends on:** none · **Parallel with:** WS-1, WS-11
- **Goal.** Let a WebSocket endpoint be saved next to HTTP requests and travel through
  export/import without touching existing data.
- **Scope.** `pypost/models/websocket.py` (all models in A-4.1, **including the six MCP
  fields `expose_as_mcp`, `mcp_description`, `mcp_params` and `mcp_probe_*` — this story is
  their single owner; WS-9 adds no field**);
  `Collection.websockets`; the new `pypost/core/websocket_registry.py` (index, CRUD,
  kind-aware `find_item`); the R-1.1 extraction of item-type dispatch into
  `pypost/core/collection_item_dispatch.py` with the `request_manager.py` cap re-derived;
  a `"websocket"` entry in `DEFAULT_COLLECTION_ITEM_STRATEGIES`;
  `collection_export` / `collection_import` support including id reservation and summary counts.
  **No change to `pypost/core/storage.py`** — the existing `model_dump_json` /
  `Collection(**data)` path already carries the new list (R-1.1).
- **Acceptance criteria.**
  1. A profile with presets and sequences survives save → load → export → import unchanged.
  2. The import summary reports WebSocket entries separately from requests.
  3. An imported profile whose id already exists is given a fresh id before any write.
  4. A collection file written by an older build (no `websockets` key) loads with an empty list
     and is unchanged on re-save.
  5. No resolved variable value is ever written into a collection file.
  6. `WebSocketRegistry.find_item` resolves an id to its kind, object and owning collection
     in O(1), and existing `RequestManager` request lookups are unaffected.
  7. Rename and delete work for profiles through the existing item-type strategy dispatch.
  8. `scripts/audit_baseline_metrics.py --check` passes with `pypost/core/request_manager.py`
     back under a re-derived cap, and `websocket_registry.py` and
     `collection_item_dispatch.py` registered with their own caps (R-1.1).
  9. `pypost/core/storage.py` is unchanged, proven by a save/load round trip of a collection
     containing profiles.
  10. The six MCP fields exist, persist and round-trip here, with no MCP behavior attached
      (that is WS-9) — the FR-7.1 story boundary.
- **Out of scope.** Any UI; the tree row itself is WS-4; MCP behavior (WS-9).

#### A-13.3 WS-3 — Bounded message stream, codecs and export

- **Points: 5** · **Depends on:** WS-1 (`RawFrame`), WS-2 (`WsMessageFormat`) ·
  **Parallel with:** WS-8
- **Goal.** Guarantee that a session's memory is bounded and that its record can leave the app.
- **Scope.** `pypost/core/websocket_stream.py` (ring with dual eviction, drop accounting,
  `StreamQuery` predicate); `pypost/core/websocket_codec.py` (text/JSON/hex/base64 encode,
  decode, and received-payload presentation detection); `pypost/core/websocket_stream_export.py`
  (JSON array + plain text through `export_file_writer`);
  `pypost/ui/widgets/websocket/stream_model.py` (`QAbstractListModel` over the ring, with
  `append_batch(entries)` as the **sole** ring writer on the UI path); the pure
  `build_stream_entry(frame, *, env_vars, hidden_keys, truncate_bytes)` that turns a
  `RawFrame` into a masked `StreamEntry` (A-3.1, A-8.2).
- **Acceptance criteria.**
  1. Exceeding `max_entries` evicts oldest-first and increments `dropped["capacity"]`.
  2. Exceeding the byte budget evicts oldest-first and increments `dropped["memory_budget"]`.
  3. A payload larger than `ws_display_truncate_bytes` is retained truncated, flagged, and still
     reports its true wire size.
  4. Codec round trips hold for text, JSON, hex and base64; invalid hex/base64 input is rejected
     with a specific message.
  5. Presentation of a received binary payload defaults to hexadecimal and the user override
     persists for the session.
  6. The model keeps stable row identity across front eviction and emits correct
     insert/remove signals (verified with `QAbstractItemModelTester` or an equivalent check).
  7. Both export formats are byte-identical for the same input and include the drop counts.
  8. `build_stream_entry` replaces hidden values using only the `env_vars` / `hidden_keys`
     passed to it, imports no environment type, and is unit-tested without Qt; a frame whose
     payload contains a hidden value never yields an unmasked `StreamEntry`.
  9. `append_batch` is the only code path that mutates the ring from the UI, verified by a
     test that appends a batch and asserts one insert transaction plus the eviction removals.
- **Out of scope.** The view, filters and the detail pane (WS-5).

#### A-13.4 WS-4 — WebSocket session tab and minimal client

- **Points: 8** · **Depends on:** WS-1, WS-2, WS-3 · **First user-visible story**
- **Goal.** A user can open a saved endpoint, connect, send a plain-text message, and read the
  replies — a complete if minimal client.
- **Scope.** `pypost/ui/presenters/websocket_presenter.py`;
  `pypost/ui/widgets/websocket/{websocket_tab,connection_editor,state_badge}.py`; a plain
  `QListView` over the WS-3 model and a single-format composer; `TabsPresenter.open_page` /
  `close_page` / `set_page_badge`; collection-tree rows for profiles; `WS_*` widget ids;
  tab-strip badges; restore-disconnected behavior. **The ingestion path of A-3.1 in full**:
  raw frames from the controller → `build_stream_entry` with `env_vars`/`hidden_keys` taken
  from `EnvPresenter` through the existing propagation chain → 33 ms batched
  `StreamListModel.append_batch`. `tests/test_agent_e2e_websocket.py` and the WS-4 share of
  the `tests/test_ui_identity_spotcheck.py` extension (A-14).
- **Acceptance criteria.**
  1. Double-clicking a profile in the tree opens it in a tab of the existing tab widget.
  2. Connect/Disconnect is a distinct control from Send message.
  3. State is shown in the page badge and on the tab by glyph **and** text, never colour alone.
  4. Connection fields are read-only whenever the session is not `Idle`/`Failed`, with a visible
     reason.
  5. Sent and received messages and lifecycle events appear in one chronological, timestamped
     list with a direction indicator.
  6. Closing the tab or quitting the application closes the socket deterministically.
  7. A tab restored at startup opens `Idle` and does not connect.
  8. `tabs_presenter.py` stays under its regression cap (144 lines of headroom, R-1.1) and
     every new capped module is added to `scripts/audit_baseline_metrics.py`.
  9. A hidden environment value used in a handshake header or a sent message is **already**
     masked in the stream at this story; WS-7 extends the masking rule and rewires nothing
     (A-3.1).
  10. `tests/test_agent_e2e_websocket.py` opens a profile, connects, sends and asserts a
      stream row entirely through widget ids, and passes under `make test-agent-e2e`.
  11. `tests/test_ui_identity_spotcheck.py` resolves every id this story introduces on a
      live tab, scoped to the current tab.
- **Out of scope.** Search, filters, pause, detail pane, export (WS-5); formats, presets,
  sequences (WS-6); template resolution and the heuristic egress tier (WS-7).

#### A-13.5 WS-5 — Stream inspector

- **Points: 8** · **Depends on:** WS-3, WS-4 · **Parallel with:** WS-6
- **Goal.** Keep a busy stream readable while it keeps arriving.
- **Scope.** `stream_view.py` (delegate, filter bar, drop notice, follow-tail logic), detail
  pane with copy/expand/wrap/hex toggle and **Set as variable…**, export actions, proxy-model
  filtering, lifecycle-noise toggle.
- **Acceptance criteria.**
  1. A 5 000-entry stream scrolls smoothly with no per-row widget allocation.
  2. Filter by direction and by message kind; text search reports a match count.
  3. Pause stops the view following the tail while the session keeps receiving; resuming jumps
     to the tail; the control states which behavior it has.
  4. Clear empties the stream and resets counters while the session stays open.
  5. Dropped-message counts are visible with their cause.
  6. A single entry can be expanded, copied (masked), and turned into an environment variable.
  7. Export writes both formats and includes drop counts.
  8. An empty filter result shows the count hidden and a way to clear the filter.
  9. `tests/test_ui_identity_spotcheck.py` is extended with the stream ids this story adds
     (A-5.7).
- **Out of scope.** Composer behavior.

#### A-13.6 WS-6 — Composer, saved presets and sequence runner

- **Points: 8** · **Depends on:** WS-3, WS-4 · **Parallel with:** WS-5
- **Goal.** Stop users retyping payloads and let a multi-step exchange be reproduced identically.
- **Scope.** Composer on `CodeEditor` with the existing `BodyFormat` selector and validators
  (`doc/dev/body_format_selector.md`, `doc/dev/body_editor_validation.md`); **the presets
  and sequences surface exactly as specified in A-5.8** — the `Messages` sub-tab with the
  preset master/detail list and its CRUD, `Load into composer` / `Send now`, the sequence
  list with its step table (preset-reference or inline payload, per-step pre-delay,
  reorder), `Run`/`Stop`, both empty states, and the composer-strip `Preset:` / `Sequence:`
  combos with `Save…`; `pypost/core/websocket_sequence.py` (pure plan/step outcomes) and
  `pypost/core/qt/websocket_sequence_runner.py` (`QTimer` pacing).
- **Acceptance criteria.**
  1. Text, JSON, hexadecimal and base64 payloads can be composed and sent, with per-format
     validation before send.
  2. A preset is saved on the profile, persists through export/import, and is resent in one
     action.
  3. A sequence runs its steps in order with per-step delays, and each step lands in the stream.
  4. A failing step reports which step and why, and the run stops.
  5. A running sequence can be stopped mid-run and leaves the session open.
  6. The same sequence runs unmodified against a second environment.
  7. Sending while the session is not `Open` is refused with a clear message rather than queued.
  8. The `Messages` sub-tab matches A-5.8: master/detail editing, `Save…` from the composer
     creating a preset, a step referencing a deleted preset blocking `Run` with a named
     reason, and both empty states.
  9. `tests/test_ui_identity_spotcheck.py` is extended with the composer, preset and
     sequence ids of A-5.7/A-5.8.
- **Out of scope.** Masking specifics and per-send template resolution (WS-7).

#### A-13.7 WS-7 — Environments, templating and secret masking

- **Points: 5** · **Depends on:** WS-4, WS-5
- **Goal.** Make the differentiator real: real-time sessions inherit PyPost's environments and
  secret handling exactly.
- **Scope.** This story **extends the ingestion path WS-4 already built and rewires none of
  it** (A-3.1): connect-time resolution of URL/params/headers/subprotocols; per-send payload
  resolution; the second (heuristic) masking tier of A-8.2 on everything leaving the process
  — clipboard, export file, MCP transcript; variable-aware hover on WebSocket fields; the
  `hidden_value_masks_applied_total{surface="websocket"}` increment. The exact hidden-value
  replacement on the live stream is WS-4's and stays where it is.
- **Acceptance criteria.**
  1. A hidden variable used in a header or payload never appears unmasked in the stream, the
     clipboard, an export file, a log record or a metric label.
  2. Handshake values resolve once at connect; a variable changed mid-session does not silently
     alter the handshake shown in the stream.
  3. A payload placeholder resolves at send time, so a value captured mid-session applies.
  4. A received payload is never rendered as a template (explicit test with `{{` in the payload).
  5. Hovering a `{{ VAR }}` in a WebSocket field shows the value, or `********` when hidden.
  6. Switching the active environment and reconnecting uses the new values with no edit.
  7. Ring ownership is unchanged by this story: the presenter still masks and
     `StreamListModel.append_batch` is still the sole writer (asserted, so the seam cannot
     drift).
- **Out of scope.** TLS (WS-8).

#### A-13.8 WS-8 — TLS and connection-security policy

- **Points: 5** · **Depends on:** WS-1 · **Parallel with:** WS-3
- **Goal.** Make `wss://` secure by default and make insecure choices visible and temporary.
- **Scope.** Default `QSslConfiguration`; `sslErrors` / `peerVerifyError` handling with a
  per-session, non-persistent, reject-by-default decision; plaintext warning for non-loopback
  `ws://`; the `ignoreSslErrors` guard test.
- **Acceptance criteria.**
  1. A self-signed or hostname-mismatched peer is rejected by default and the session never
     reaches `Open`.
  2. The specific certificate errors are shown to the user, not a generic failure.
  3. An accepted exception applies to that session only and is never written to disk (asserted
     by inspecting settings and collection files after the session).
  4. `ws://` to a non-loopback host shows a persistent plaintext warning.
  5. A guard test fails if `ignoreSslErrors(` appears under `pypost/`.
- **Out of scope.** Certificate management UI (FU-6).

#### A-13.9 WS-9 — Bounded MCP WebSocket probe tool

- **Points: 8** · **Depends on:** WS-1, WS-2, WS-7, WS-10
- **Goal.** Give agents a safe, bounded way to sample a real-time endpoint.
- **Scope.** The **behavior** behind the MCP fields WS-2 already defined on
  `WebSocketConnection` — this story adds no model field (FR-7.1);
  `pypost/core/websocket_probe.py` (stop conditions, transcript shaping);
  `pypost/core/qt/websocket_probe_runner.py` (short-lived `QThread` with its own event loop
  and hard deadline); the new `pypost/core/websocket_mcp_tools.py` holding the tool schema,
  registration and dispatch, with `MCPServerImpl.register_tools` gaining only a delegating
  call (R-1.1 — 13 lines of headroom); MCP sub-tab preview in the WebSocket editor;
  `daemon_storage` snapshot loaders extended to carry profiles.
- **Acceptance criteria.**
  1. `list_tools` lists an exposed profile with a schema containing only `mcp.request.*`
     parameters; hidden and environment-only variables are absent.
  2. `call_tool` connects, sends the designated preset, collects until the first of max
     messages, max duration or a `stop_when` match, closes with 1000, and returns one transcript.
  3. Global ceilings cannot be exceeded by a per-profile override.
  4. The transcript is sanitized with the same helper used for HTTP MCP results.
  5. The runner thread always terminates and never outlives the call, including on error and on
     deadline expiry (asserted).
  6. The tool works under `pypost-daemon` with no display server.
  7. The call is recorded in the MCP activity log and in the MCP metrics.
  8. A probe takes a `SessionSlots` slot and releases it on every exit path, so probes count
     against `ws_max_concurrent_sessions` (A-12.1); at the ceiling `call_tool` returns a
     stated refusal instead of opening a socket.
  9. `pypost/models/websocket.py` is unchanged by this story, and
     `scripts/audit_baseline_metrics.py --check` passes with `mcp_server_impl.py` under its
     cap (R-1.1).
- **Out of scope.** Any persistent agent-held session (FU-3); the MCP model fields (WS-2).

#### A-13.10 WS-10 — Settings, session ceiling, metrics and logging

- **Points: 8** · **Depends on:** WS-1, WS-3, WS-4, WS-5
- **Goal.** Make sessions boundable by an operator — per session *and* in total — and
  diagnosable from logs and metrics.
- **Scope.** The `ws_*` fields in A-12 plus a Settings dialog section
  (`doc/dev/settings_dialog.md`); **the D-14 concurrent-session ceiling of A-12.1**:
  `ws_max_concurrent_sessions`, the `SessionSlots` counter in
  `pypost/core/websocket_session_policy.py`, slot acquire/release on every connect and every
  terminal transition, the refusal message and lifecycle entry, and the `0 = locked down`
  case; metrics
  `websocket_sessions_opened_total{outcome}`, `websocket_sessions_closed_total{reason}`,
  `websocket_messages_total{direction,kind}`, `websocket_message_bytes_total{direction}`,
  `websocket_stream_entries_dropped_total{reason}`,
  `websocket_reconnect_attempts_total{outcome}`, `websocket_active_sessions` (gauge),
  `websocket_session_start_refused_total{reason}`,
  `websocket_probe_duration_seconds{outcome}` (histogram); the log events in A-8.4;
  documentation updates to `doc/prometheus_monitoring.md` and `doc/dev/logging.md`.
- **Acceptance criteria.**
  1. Every bound in A-12 is editable and takes effect for the next session without a restart.
  2. All new metrics scrape with the documented names and label sets and use only fixed
     low-cardinality label values.
  3. No payload, header value or unmasked URL appears at any log level, verified by a test that
     sends a known secret and asserts its absence from `caplog`.
  4. The regression snapshot is regenerated and `scripts/audit_baseline_metrics.py --check`
     passes.
  5. With `ws_max_concurrent_sessions = N`, the `N+1`-th connect is refused with the message
     of A-12.1, the badge stays `Idle`, nothing is queued, and the refusal counter and log
     event fire; freeing a slot lets the next connect succeed.
  6. `SessionSlots` is unit-tested without Qt, including release on failure, on peer close
     and on probe deadline expiry, so a leaked slot cannot wedge the ceiling.
  7. `ws_max_concurrent_sessions = 0` blocks connecting entirely and says so.
- **Out of scope.** Alerting rules.

#### A-13.11 WS-11 — WebSocket test harness

- **Points: 5** · **Depends on:** none · **Must land first or concurrently with WS-1**
- **Goal.** Make every other story verifiable offline, deterministically, and headlessly.
- **Scope.** `tests/websocket_echo_server.py` — a `QWebSocketServer` fixture bound to
  `127.0.0.1:0` with scripted behaviors: echo, reject handshake, negotiate/refuse a subprotocol,
  close with a chosen code and reason, go silent (heartbeat testing), flood at a chosen rate,
  send an oversize message, drop the connection mid-stream. Bounded-wait helper built on
  `pypost/agent/ui_wait.py`. Registration in `tests/conftest.py`. A responsiveness/flood test.
- **Acceptance criteria.**
  1. The fixture starts and stops per test with a bounded wait and never leaks a port or thread.
  2. No test in the suite contacts a public internet endpoint.
  3. Every test declares an explicit `pytest.mark.timeout` per the project rule.
  4. The whole suite passes under `QT_QPA_PLATFORM=offscreen`.
  5. The flood test asserts the retained-byte budget holds and that a GUI-thread responsiveness
     probe stays within a documented latency bound; it is marked `slow` if it exceeds the fast
     suite's budget.
- **Out of scope.** TLS server mode (WS-8 supplies its own fixture).

#### A-13.12 WS-12 — User and developer documentation

- **Points: 3** · **Depends on:** WS-4 … WS-10
- **Goal.** Ship the capability documented to PyPost's existing standard.
- **Scope.** `doc/user/websocket.md`; updates to `doc/user/interface.md`, `doc/user/hotkeys.md`,
  `doc/user/collections.md`, `doc/user/settings.md`, `doc/user/mcp-tools.md`;
  `doc/dev/websocket_architecture.md`; updates to `doc/dev/ui_identity.md`,
  `doc/dev/testing.md`, `doc/dev/architecture.md`.
- **Acceptance criteria.**
  1. The user guide covers connecting, composing, presets, sequences, the stream inspector,
     limits, reconnect, masking and the MCP probe.
  2. The downgrade caveat (A-4.3) is documented in `doc/user/collections.md` and the release
     notes.
  3. The known limitations (no compression, no handshake-response introspection) are stated in
     the user documentation, not only here.
  4. The release checklist gains a per-platform `wss://` smoke step (OQ-4, A-16) alongside
     the existing platform matrix in `doc/dev/licensing.md`.
  5. `make lint-docs` and `make check-docs-links` pass.

#### A-13.13 Summary and parallelism

| Story | Points | Depends on | Can run in parallel with |
| --- | ---: | --- | --- |
| WS-11 test harness | 5 | — | WS-1, WS-2 |
| WS-1 transport + engine | 8 | — | WS-2, WS-11 |
| WS-2 models + persistence | 8 | — | WS-1, WS-11 |
| WS-3 stream + codecs + export | 5 | WS-1, WS-2 | WS-8 |
| WS-8 TLS policy | 5 | WS-1 | WS-3 |
| WS-4 session tab (minimal client) | 8 | WS-1, WS-2, WS-3 | — |
| WS-5 stream inspector | 8 | WS-3, WS-4 | WS-6 |
| WS-6 composer/presets/sequences | 8 | WS-3, WS-4 | WS-5 |
| WS-7 env/templating/masking | 5 | WS-4, WS-5 | WS-10 |
| WS-10 settings/ceiling/metrics | 8 | WS-1, WS-3, WS-4, WS-5 | WS-7 |
| WS-9 MCP probe | 8 | WS-1, WS-2, WS-7, WS-10 | — |
| WS-12 documentation | 3 | WS-4…WS-10 | — |
| **Total** | **79** | | |

#### A-13.14 Follow-ups deliberately excluded from the epic (FR-7.7)

- **FU-1 Socket.IO client** — a framing layer on top of WebSocket; a separate product decision.
- **FU-2 Session summary entry in history** — requires changing the persisted `HistoryEntry`
  shape ([A-9](#a-9-d-4--history-fr-65)).
- **FU-3 Persistent agent-held session over MCP** — unbounded resource exposure with no
  supervising user (A-10.3).
- **FU-4 On-message scripting hook** — needs a rate cap and an execution model `ScriptExecutor`
  does not have.
- **FU-5 `websocat` / `wscat` command export** — assumes an external tool on the user's machine.
- **FU-6 Persisted TLS certificate exceptions** — a trust decision that outlives its window;
  needs its own design.
- **FU-7 `permessage-deflate` support** — requires a second transport implementation behind the
  seam (A-1.4).
- **FU-8 MQTT, gRPC streaming, SSE as a live session** — different protocols; separate epics.
- **FU-9 Record and replay a captured session as a fixture** — a test-tooling product of its
  own.
- **FU-10 Per-message timing comparison (Postman parity)** — an inspection nicety; no FR-2
  journey needs it.
- **FU-11 Pre-flight HTTP probe to recover handshake status** — mitigation for R-B; only worth
  it if R-B proves painful.

### A-14 Test strategy for the implementation

Following `doc/dev/testing.md`, `doc/dev/gui_testing.md` and the project's mandatory per-test
timeout rule.

**Pure unit (no Qt)** — `tests/test_websocket_stream.py`, `_codec`, `_session_policy`,
`_sequence`, `_probe`, `_stream_export`. Covers ring eviction on both dimensions, drop
accounting, the filter predicate, codecs, truncation, the reconnect backoff schedule, heartbeat
policy, sequence plan expansion, probe stop conditions and transcript shaping. These import
`pypost.core.websocket_*` without a `QApplication` and declare
`pytestmark = pytest.mark.timeout(30)`.

**Qt integration** — `tests/test_websocket_session.py`, `tests/test_websocket_transport.py`.
Covers the handshake, subprotocol negotiation, text and binary echo, close code and reason,
handshake rejection, heartbeat and its timeout, drop to reconnect to exhaustion, oversize abort
and deterministic teardown. Runs against the WS-11 `QWebSocketServer` on `127.0.0.1:0` with
bounded waits via `wait_until` (`pypost/agent/ui_wait.py`) — never `sleep` loops.

**GUI and widget** — `tests/test_websocket_tab.py`, `tests/test_websocket_stream_view.py`,
`tests/test_websocket_composer.py`. Covers state badge text per state, frozen-field
enforcement, filter and search results, pause-display semantics, drop-notice visibility, empty
and error states, and restore-disconnected. Offscreen platform, shared module-scoped `qapp`
fixture, widgets closed in a `finally` block.

**Identity** — `tests/test_ui_identity_spotcheck.py`, extended so every `WS_*` id resolves on a
live tab, scoped to the current tab, following the existing spot-check pattern. The
extension is **split across the stories that add the ids**: WS-4 for the tab, connection
and state ids (A-13.4 AC 11), WS-5 for the stream ids (A-13.5 AC 9), WS-6 for the composer,
preset and sequence ids (A-13.6 AC 9). No story inherits another's identity debt.

**Security** — `tests/test_websocket_masking.py`, `tests/test_websocket_tls.py`. Asserts the
secret is absent from the stream, the clipboard, the export, `caplog` and metric labels; that a
self-signed peer is rejected by default; that an exception is never persisted; and that the
`ignoreSslErrors` guard fires. `caplog` assertions follow the project logging contract.

**MCP** — `tests/test_websocket_mcp_probe.py`. Covers `list_tools` schema exclusions, the
bounded transcript, runner termination and daemon snapshot inclusion. Reuses
`pypost/fixtures/mcp_test_fixtures.py`; `make check-mcp-fixtures` stays green.

**Performance and responsiveness** — `tests/test_websocket_flood.py`. Asserts model transactions
stay near 30/s regardless of arrival rate, that retained bytes stay within budget, and that the
GUI-thread latency bound holds. Precedent: `tests/test_env_storage_responsiveness.py`; mark
`slow` if it exceeds the fast-suite budget.

**Regression guards** — `tests/test_solid_audit_baseline.py`. Every new capped module is
registered and `tabs_presenter.py` stays under 785 lines; the snapshot is regenerated in the
story that adds a module. The zero- and single-digit-headroom modules of R-1.1 are covered
by named acceptance criteria on WS-2 (AC 8-9) and WS-9 (AC 9).

**Agent e2e** — `tests/test_agent_e2e_websocket.py`, **owned by WS-4** (A-13.4 AC 10), the
first story with a reachable UI. Opens a profile, connects, sends, and asserts a stream row,
driven by widget ids. Run with `make test-agent-e2e` / `-m agent_e2e`.

Suite-wide invariants that must hold at the end of the epic: `make check` green; coverage stays
at or above `--cov-fail-under=70`; no test reaches a public network; every test declares an
explicit timeout.

### A-15 Risks and open questions

- **OQ-1 — exact ordering of the transport's opened callback versus socket state changes in
  Qt 6.11.** *Impact:* a wrong `Open` badge, or a race in tests. *Handling:* **not assumed** —
  WS-1 must pin the observed ordering with a test against the local server and treat the opened
  callback as authoritative.
- **OQ-2 — whether a specific rejection reason (401 vs 403 vs TLS) is distinguishable from
  `errorString()` alone.** *Impact:* weaker diagnostics than Postman (R-B). *Handling:* WS-1
  records the observed strings for the fixture's rejection modes; if they are indistinguishable,
  raise FU-11.
- **OQ-3 — the real-world throughput ceiling of a GUI-thread socket in PySide6.**
  *Impact:* R-C, responsiveness under a flood. *Handling:* WS-11's flood test establishes the
  number and makes it a CI-enforced bound.
- **OQ-4 — whether the packaged Windows and macOS artifacts behave like the verified Linux
  one: `QtWebSockets` present in the shipped wheel, and the platform certificate store and
  system proxy settings picked up identically by the Qt build inside it.**
  *Impact:* a `wss://` endpoint that validates on one platform and not another, or a
  proxy-related handshake failure (the vendor proxy caveat in R-3.1). *Handling:* CI runs
  Linux only (`.github/workflows/test.yml`), so WS-8 asserts reject-by-default against the
  local fixture on CI, and WS-12 adds a per-platform `wss://` smoke to the release checklist
  ([A-16](#a-16-portability-and-platform-coverage)).
- **R-1 — an endpoint that requires `permessage-deflate`.** *Impact:* unusable for that
  endpoint. *Handling:* documented limitation, with the FU-7 escape hatch behind the transport
  seam.
- **R-2 — silent data loss when a WebSocket-bearing collection is saved by an older build.**
  *Impact:* the user loses profiles. *Handling:* release note plus user documentation (A-4.3);
  no engineering fix exists.
- **R-3 — scope creep from Socket.IO requests once raw WebSocket ships.** *Impact:* the epic
  slips. *Handling:* FU-1 is recorded as a separate decision, not an extension.
- **R-4 — `tabs_presenter.py` cap pressure as WS-4 adds the page seam.** *Impact:* a CI cap
  failure. *Handling:* the seam is limited to three methods, new behavior lives in
  `WebSocketPresenter`, and the cap check is explicit acceptance criteria on WS-4.
- **R-5 — the two masking tiers (A-8.2) are misapplied and either leak or mangle.**
  *Impact:* a security or usability defect. *Handling:* the tier boundary is a single function
  in the presenter, covered by WS-7 tests on both sides.
- **R-6 — an agent configures a probe that outlives its bound.** *Impact:* resource exposure.
  *Handling:* global ceilings are ceilings, not defaults; the runner has a hard-deadline timer;
  asserted in WS-9.
- **R-7 — reconnect masks real instability and the user believes they saw a continuous stream.**
  *Impact:* wrong debugging conclusions. *Handling:* the gap and the recovery are both written
  into the stream (S-5.3), and the wording states that messages may have been missed.

### A-16 Portability and platform coverage

The Step 1 NFR is "behavior must hold on the desktop platforms PyPost already supports, with no
new mandatory system service". PyPost's supported desktop targets are macOS, Windows and Linux
(`doc/dev/licensing.md`, platform matrix G7). The design meets the NFR as follows.

- **No new mandatory system service, on any platform.** The transport runs in-process on the Qt
  event loop that already exists (A-1.1); the MCP probe runs in a short-lived thread inside the
  same process (A-10.2); the only server introduced is the test fixture `QWebSocketServer` bound
  to `127.0.0.1:0` during tests (WS-11). No broker, no helper daemon, no privileged port, no
  firewall exception beyond the outbound connection the user asks for.
- **No new dependency to port.** Runtime fact, checked against the installed `.venv`:
  `PySide6/QtWebSockets.abi3.so` is listed in `pyside6_addons-6.11.1.dist-info/RECORD`, so the
  binding arrives with **`pyside6-addons`** — not with `pyside6-essentials`, which ships only
  `QtWebSockets.pyi`. That matters only for accuracy, not for cost: `pyside6-addons==6.11.1` is
  already a locked transitive dependency of the pinned `PySide6==6.11.1`
  (`requirements.in`, `requirements.txt:93-100`) and is already inventoried as `PySide6_Addons`
  in `LICENSES/transitive.csv`. The lock pins that same wheel on every platform, so no
  per-platform install step, lock regeneration or license-inventory change is needed. Wheel
  *contents* were read on the installed Linux environment; the packaged macOS and Windows
  artifacts are covered by the release smoke of OQ-4 rather than by assumption.
- **No platform-conditional code.** The design adds no `sys.platform` branch; today the only
  such branch in the product is in `curl_generator.py` (`doc/dev/testing.md:95`), and this epic
  does not touch it. GUI tests keep running under `QT_QPA_PLATFORM=offscreen`
  (`doc/dev/gui_testing.md`), which is the same on all three targets, and the headless probe
  needs only `QCoreApplication` (A-1.1), so it works on a machine with no display server.
- **No new persisted-state location.** Profiles ride inside existing collection files and the
  `ws_*` settings inside the existing `settings.json`, both already resolved through
  `platformdirs`. Nothing new needs a per-platform path.
- **Residual platform risk is TLS and proxy behavior**, because those are the parts Qt delegates
  to the host: certificate-store integration and system proxy handling. That is recorded as
  **OQ-4** in [A-15](#a-15-risks-and-open-questions) rather than asserted away — WS-8 pins
  reject-by-default on CI (Linux, `.github/workflows/test.yml`), and WS-12 adds a per-platform
  `wss://` smoke to the release checklist.

### A-17 Requirements traceability

FR-6.x is answered item by item in [A-11](#a-11-coexistence-decisions-fr-6) and FR-7.x in
[A-13](#a-13-implementation-breakdown--stories-for-epic-pypost-1123), both already cited by ID.
FR-1, FR-2 and FR-3 describe this discovery's own deliverables and are satisfied by
[`10-requirements.md`](10-requirements.md) plus this document. The two remaining families are
traced here so completeness is checkable without re-reading the whole RFC.

#### A-17.1 FR-4 — protocol and functional scope

| FR | Where it is specified | Story |
| --- | --- | --- |
| FR-4.1 endpoint | A-4.1 `url`; A-7 connect-time resolution; A-8.3 plaintext warning | WS-2, WS-4 |
| FR-4.2 handshake config | A-1.4 `HandshakeTarget`; A-4.1; A-5.2 negotiation | WS-1, WS-4 |
| FR-4.3 states | A-5.2 state machine; A-5.6 error states | WS-1, WS-4 |
| FR-4.4 directions and kinds | A-6.1 `StreamEntry.kind` / `.direction`; A-5.4 | WS-3, WS-5 |
| FR-4.5 encodings | A-4.1 `WsMessageFormat`; A-13.3 AC 4-5 | WS-3, WS-6 |
| FR-4.6 heartbeat | A-5.2; A-6.3 noise control; A-12 `ws_default_heartbeat` | WS-1, WS-10 |
| FR-4.7 reconnect | A-5.2; A-12 `ws_default_reconnect`; stream survives the gap | WS-1, WS-4 |
| FR-4.8 presets | A-4.1 `WebSocketMessagePreset`; A-5.8 | WS-2, WS-6 |
| FR-4.9 sequences | A-4.1 `WebSocketSequence`; A-5.8; `websocket_sequence.py` | WS-2, WS-6 |
| FR-4.10 limits | A-6.1, A-6.2, A-12, A-12.1 (process-wide) | WS-3, WS-10 |
| FR-4.11 editing while connected | A-5.3 (D-13) | WS-4 |

#### A-17.2 FR-5 — UI/UX and desktop ergonomics

| FR | Where it is specified | Story |
| --- | --- | --- |
| FR-5.1 where a session lives | A-5.1 ownership; A-5.4 wireframe; A-5.5 tab strip | WS-4 |
| FR-5.2 connection controls | A-5.2; A-5.4 (Connect distinct from Send) | WS-4 |
| FR-5.3 state indicators | A-5.5 marker+text on the tab; A-5.4 badge | WS-4 |
| FR-5.4 stream inspector | A-5.4; A-6.3 rendering; A-13.5 | WS-5 |
| FR-5.5 composer | A-5.4 composer strip; A-13.6 | WS-6 |
| FR-5.6 presets and sequences surface | A-5.8 wireframe and interaction rules | WS-6 |
| FR-5.7 long-session ergonomics | A-6.3; A-6.4; A-13.11 flood test | WS-5, WS-11 |
| FR-5.8 keyboard access | A-5.7 hotkey table | WS-4, WS-6 |
| FR-5.9 automation identity | A-5.7 and A-5.8 id lists; A-14 identity split | WS-4, WS-5, WS-6 |
| FR-5.10 errors and empty states | A-5.6; A-5.8 empty states; A-12.1 refusal | WS-4, WS-5 |

#### A-17.3 Non-functional requirements imposed on the capability

| NFR | Where it is addressed | Story |
| --- | --- | --- |
| Security and privacy | A-8.1-A-8.4; A-3.1 masking ownership | WS-4, WS-7, WS-8 |
| Responsiveness | A-6.3, A-6.4; A-14 flood test | WS-5, WS-11 |
| Bounded resource use | A-6.1-A-6.2 per session; A-12.1 process-wide (D-14) | WS-3, WS-10 |
| Reliability | A-5.2 transitions; A-13.1 AC 8; A-13.4 AC 6 | WS-1, WS-4 |
| Backward compatibility | R-2; A-4.3; A-12 defaults; A-13.2 AC 4 | WS-2 |
| Observability | A-8.4 log events; A-13.10 metrics | WS-10 |
| Testability | A-14; WS-11 offline fixture | WS-11 |
| Accessibility and ergonomics | A-5.5 marker+text; A-5.7 hotkeys | WS-4 |
| Portability | [A-16](#a-16-portability-and-platform-coverage); OQ-4 | WS-8, WS-12 |

## Q&A

**Q: Why Qt-native `QWebSocket` and not the `websockets` library, which is the Python default?**
A: Three reasons, in order of weight. (1) `QtWebSockets` is already inside the PySide6 6.11.1
wheel we pin, so the feature costs zero new dependencies, while `websockets` costs a direct
dependency plus lock, license-inventory and audit obligations. (2) The asyncio route needs an
event-loop host, and PySide6's own `QtAsyncio` cannot be one — `QAsyncioEventLoop` raises
`NotImplementedError` for `create_connection`, `getaddrinfo`, every `sock_*` method and
`add_reader`/`add_writer` (read from the installed wheel). That leaves `qasync`, which replaces
the application's event loop globally, or a second dedicated loop thread — both large changes
for one tab. (3) `QWebSocketServer` ships in the same module, so the offline test harness the
requirements demand comes free. See
[A-1](#a-1-d-1--networking-engine-recommend-qt-native-qwebsocket).

**Q: What do we give up by choosing Qt?**
A: `permessage-deflate` (Qt states it supports no WebSocket Extensions), introspection of the
handshake HTTP response, and built-in heartbeat scheduling. The first is a documented epic
limitation with an escape hatch; the second degrades a diagnostic, not a capability; the third
is roughly one small pure-policy module that is easier to unit-test than a library's built-in.

**Q: Is the decision reversible if one of those hurts?**
A: Yes, and that is why the transport is a Qt-free `Protocol` implemented in exactly one Qt
module ([A-1.4](#a-14-the-seam-that-makes-d-1-reversible)). A second implementation backed by
`websockets` on a dedicated thread satisfies the same interface; the session controller, the
stream and the whole UI are untouched.

**Q: Is a WebSocket connection a new request kind or a new object?**
A: A new object. `RequestData` is documented to stay lean because tabs deep-copy it, its fields
are HTTP-shaped, and `method` drives body auto-switching and metric labels. A separate
`Collection.websockets` list is also the safer on-disk shape: Pydantic's default `extra='ignore'`
means an old build drops an unknown **key** cleanly, whereas a mixed list would coerce a
WebSocket entry into a `RequestData` with `method="GET"` and produce a bogus request.

**Q: Do sessions enter history?**
A: No, not in this epic. `HistoryEntry` requires a status code and a round-trip time, the store
caps at 500 entries, and the panel filters by URL only — one busy session would evict a user's
entire HTTP history. The need is served by the retained stream and transcript export. A single
session-summary entry is recorded as follow-up FU-2.

**Q: Can an agent use a WebSocket endpoint over MCP?**
A: Yes, as a **bounded probe**: connect, send a designated message, collect until the first of
max messages / max duration / a stop-match, close, return one masked transcript. That is exactly
the shape `call_tool` already has, and it reuses the pattern PyPost already applies to SSE
(5 events / 10 s). A persistent agent-held session is excluded: MCP gives no guarantee that a
client closes a handle, and under `pypost-daemon` no human could see or stop it.

**Q: How does a long-lived stream avoid eating memory or freezing the UI?**
A: A bounded ring with two eviction dimensions (5 000 entries **and** a 64 MiB retained-payload
budget), per-entry display truncation at 256 KiB, a socket-level 8 MiB message ceiling, intake
coalesced into one model transaction every 33 ms — the same interval already used for streamed
HTTP bodies — and a virtualized `QListView` instead of the per-row widgets the history panel
uses. Worst case per session is flat and stated, and `ws_max_concurrent_sessions` (default 8)
turns that per-session bound into a process bound of 8 × 64 MiB, refusing the ninth connect
with a reason instead of quietly growing (D-14, A-12.1).

**Q: What about backpressure?**
A: RFC 6455 has none, so the design says so instead of pretending. PyPost offers *pause display*
(the socket keeps draining), drop-oldest with visible counters, and Disconnect — which is the
only real backpressure a WebSocket client has. *Pause intake* is deliberately not offered
because it only inflates buffers until something breaks unpredictably.

**Q: How are secrets handled differently from HTTP?**
A: They are not, except where a stream forces a choice. Profiles store templates only; hidden
values resolve at connect or at send and are masked before an entry enters the buffer, so Export
and Copy can never read an unmasked value. The one new rule is two tiers: the live view masks
hidden values exactly (so a server payload under inspection stays intact), while anything
leaving the process — clipboard, export file, MCP transcript, logs — also gets the full
heuristic sanitizer already used for history and MCP results.

**Q: What must never be logged?**
A: Message payloads in either direction, handshake header values, resolved URLs with query
strings, peer-supplied close reasons, preset and sequence payload text, and `pong` payloads.
Logs carry event name, session and profile ids, a sanitized URL, state, counts, sizes, close
codes and durations only.

**Q: Why is scripting excluded when users will ask for it?**
A: `ScriptExecutor` is a post-**response** hook that runs exactly once with `request`,
`response` and `pypost` in scope. A stream has no single response, and running user Python per
message on the GUI thread at high rates is untenable. The concrete need behind the request —
capturing a value from a reply into the environment — is met by a **Set as variable…** action in
the stream detail pane that reuses the signal `ResponseView` already emits. An on-message hook
with an explicit rate cap is recorded as FU-4.

**Q: Does an older PyPost build break on a collection containing WebSocket entries?**
A: It does not break — verified: unknown keys are ignored, so the file loads and its HTTP
requests are intact. But that build **drops** the WebSocket entries when it next saves. Downgrade
is lossy, no schema-version field can change that (an old build ignores that too), and the
honest mitigation is a release note plus a line in `doc/user/collections.md`.

**Q: Why twelve stories rather than four?**
A: FR-7.2 sets the floor (engine, data model, UI, test harness), not the ceiling. Splitting the
UI into a minimal client (WS-4), the inspector (WS-5) and the composer (WS-6) is what makes
FR-7.5 true — each merge leaves a working product — and lets two engineers work in parallel from
wave 4. Security, MCP, settings/observability and documentation are separated because each has a
distinct reviewer and distinct acceptance evidence.

## References

### Repository

- `doc/dev/architecture.md`, `doc/dev/presenter_architecture.md` — layering and presenter model
- `doc/dev/response-streaming-display.md` — the 33 ms coalescing precedent
- `doc/dev/request_execution.md`, `pypost/core/http_client.py:28-30` — the bounded SSE probe
- `doc/dev/collection_storage.md`, `doc/dev/collection_import.md`, `doc/dev/collection_export.md`
- `doc/dev/sensitive_data_masking_policy.md`, `doc/dev/hidden_variables.md`,
  `doc/dev/environment_encryption_at_rest.md`
- `doc/dev/mcp_secrets_policy.md`, `doc/dev/mcp_trust_model.md`, `doc/dev/daemon.md`
- `doc/dev/ui_identity.md`, `doc/dev/gui_testing.md`, `doc/dev/ui_wait.md`,
  `doc/dev/agent_e2e.md`, `doc/dev/testing.md`
- `doc/dev/logging.md`, `doc/prometheus_monitoring.md`, `doc/dev/licensing.md`
- `doc/dev/solid_audit.md`, `scripts/audit_baseline_metrics.py` — LOC caps
- `pypost/models/models.py`, `pypost/models/settings.py`, `pypost/models/retry.py`
- `pypost/core/qt/worker.py`, `pypost/core/qt/mcp_server.py`, `pypost/core/qt/state_manager.py`
- `pypost/core/mcp_server_impl.py`, `pypost/core/mcp_tool_contract.py`,
  `pypost/core/mcp_secrets_policy.py`
- `pypost/core/request_manager.py`, `pypost/core/history_manager.py`,
  `pypost/core/collection_item_strategies.py`, `pypost/core/export_file_writer.py`
- `pypost/ui/presenters/tabs_presenter.py`, `pypost/ui/widgets/request_editor.py`,
  `pypost/ui/widgets/response_view.py`, `pypost/ui/widgets/history_panel.py`,
  `pypost/ui/widget_ids.py`, `pypost/ui/hotkeys.py`
- `pypost/agent/ui_wait.py`

### External

- [Qt 6 — QWebSocket class reference](https://doc.qt.io/qt-6/qwebsocket.html) — protocol version
  13 only; "QWebSocket currently does not support WebSocket Extensions"; `open(…, options)` and
  `subprotocol()` since Qt 6.4; `errorOccurred` since Qt 6.5; proxy caveat for non-secure
  connections
- [Qt 6 — QWebSocketHandshakeOptions](https://doc.qt.io/qt-6/qwebsockethandshakeoptions.html) —
  since Qt 6.4; subprotocol list carried into the handshake
- [Qt 6 — Qt WebSockets module](https://doc.qt.io/qt-6/qtwebsockets-index.html) — module scope
  and licensing
- [`websockets` — asyncio client reference][ws-client]
  — `additional_headers`, `subprotocols`, `ping_interval=20`, `ping_timeout=20`,
  `max_size=1048576`, `close_timeout=10`, `compression='deflate'`

[ws-client]: https://websockets.readthedocs.io/en/stable/reference/asyncio/client.html
- [qasync](https://github.com/CabbageDevelopment/qasync) — Qt-driven PEP 3156 event loop
- [PySide6 QtAsyncio](https://doc.qt.io/qtforpython-6/PySide6/QtAsyncio/index.html) — the native
  bridge; its networking methods are unimplemented in the shipped 6.11.1 wheel (verified in
  `PySide6/QtAsyncio/events.py`)
- [RFC 6455 — The WebSocket Protocol](https://www.rfc-editor.org/rfc/rfc6455) — close codes,
  ping/pong, extension negotiation, absence of application-level flow control
- Competitive sources for the Step 1 benchmark are listed in
  [`10-requirements.md`](10-requirements.md#references)
