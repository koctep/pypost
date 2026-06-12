# PYPOST-689: Performance and Scalability Audit Report

**Task:** PYPOST-689 — Audit performance and scalability
**Date:** 2026-06-12
**Scope:** Request execution hot paths, template rendering, UI responsiveness, MCP server
threading, large collection loading, memory patterns, blocking I/O on main thread
**Baseline:** PYPOST-410 (single URL render), PYPOST-455/628 (template LRU), PYPOST-486 (async
env storage), PYPOST-364 (response search large-doc), `doc/dev/request_execution.md`
**Methodology:** Hot-path tracing per `20-architecture.md`, worker/thread inventory, grep for
render/I/O patterns, cross-reference prior benchmarks. No code changes.

## Executive Summary

PyPost has a **sound threading foundation for network sends** (`RequestWorker` offloads
`RequestService.execute`) and **sub-millisecond template work** (compile LRU, PYPOST-455). Encrypted
environment load/save already uses `EnvironmentStorageWorker` (PYPOST-486). MCP inbound tools bridge
async uvicorn to sync execution via Starlette `run_in_threadpool`.

**Three areas need immediate attention:**

1. **Unbounded response buffering (P1)** — `HTTPClient` accumulates the entire response body in a
   Python list then `"".join()` with no size cap; multi-hundred-MB payloads can exhaust memory and
   freeze the worker until complete.
2. **Startup collection load on main thread (P1)** — `MainWindow` constructs `RequestManager`,
   which synchronously `load_collections()` from disk and `CollectionsPresenter.refresh_tree()` runs
   before first paint; large installs block the Qt event loop.
3. **Response display work on main thread (P2)** — `ResponseView.display_response` runs
   `json.loads` + `json.dumps(indent=…)` for every JSON body without the 100 KB guard used by
   search; large JSON causes UI jank after the worker returns.

Secondary findings: history masking **re-renders all template fields** when `hidden_keys` is set
(P2); collection reload always **full tree rebuild** (P2); MCP default threadpool size is
**unconfigured** (P2); `HistoryManager._load` reads up to 500 entries synchronously at startup
(P2).

Findings use **P1** (OOM risk or multi-second main-thread block), **P2** (noticeable latency or
missed optimization), **P3** (documented gap or minor hygiene).

---

## Thread and Worker Inventory

### QThread workers (GUI-owned)

| Class | Module | Operation |
| --- | --- | --- |
| `RequestWorker` | `worker.py` | HTTP/MCP send, retry, script, history |
| `EnvironmentStorageWorker` | `environment_storage_worker.py` | Encrypted env load/save |
| `EncryptionMigrationWorker` | `encryption_migration_worker.py` | Key migration |
| `PasteJsonFormatWorker` | `paste_json_worker.py` | Large JSON paste format |

**Count:** 4 modules.

### Daemon `threading.Thread`

| Class | Module | Operation |
| --- | --- | --- |
| `MCPServerManager` | `mcp_server.py` | uvicorn + asyncio MCP server |
| `MetricsServer` | `metrics_server.py` | uvicorn `/metrics` |
| `HistoryManager` | `history_manager.py` | Debounced history.json save |

**Count:** 3 modules.

### Assessment (PASS with gaps)

Network sends and encrypted environment I/O are correctly off the main thread. Collection loading,
history startup load, and config persistence remain synchronous on the GUI thread.

---

## Request Execution Hot Paths

### GUI → worker → service (P-001 — PASS)

```text
TabsPresenter._start_worker()
  → RequestWorker(QThread).start()
    → RequestService.execute()
      → _execute_http_with_retry() | _execute_mcp()
      → ScriptExecutor.execute() [post-script]
      → _record_execution_history()
```

Signals (`chunk_received`, `headers_received`, `retry_attempt`) marshal results to the main
thread. Cooperative cancel via `stop_flag` / `_stop_event`.

**Evidence:** `tabs_presenter.py` lines 451–478; `worker.py` lines 87–121.

### HTTPClient.send_request (P-002 — mixed)

| Stage | Thread | Notes |
| --- | --- | --- |
| URL render | Worker | Once at line 225; passed as `rendered_url` to `_prepare_request_kwargs` (PYPOST-410 PASS) |
| Header/param render | Worker | 2× `render_string` per header/param key and value |
| `session.request(stream=True)` | Worker | Blocking `requests` I/O |
| `iter_content` loop | Worker | Chunks decoded to str, appended to list |
| Body assembly | Worker | `content = "".join(content_parts)` — full body in RAM |
| SSE probe | Worker | Caps at 5 events; closes stream early (PASS) |

**Render count per typical request** (5 headers, 3 params): 1 URL + 10 header + 6 param + 1 body
= **18** `render_string` calls. At ~40 µs/render (PYPOST-455 average), template work ≈ **0.7 ms**
— negligible vs network.

**Gap (P1 — P-003):** No `max_response_bytes`. `iter_content` runs until EOF or cancel. A
gigabyte response allocates list + final string in the worker; `ResponseData` duplicates in UI
`QTextEdit`.

**Gap (P2 — P-004):** Retry backoff uses `time.sleep(0.1)` polling in the worker (lines 245–259).
Acceptable for send worker isolation; blocks that worker for the full backoff window.

### Post-request script (P-005 — P2)

`ScriptExecutor.execute` runs `exec(script, …)` synchronously in the worker. Untrusted or heavy
scripts block completion, streaming, and history recording for that tab's worker instance.

### History recording (P-006 — P2)

`_record_execution_history` → `SensitiveDataMaskingPolicy.build_history_safe_fields`:

- When `resolved` fields exist and `hidden_keys` empty: **reuses resolved** (PASS).
- When `hidden_keys` non-empty: **re-renders URL, every header key/value, and body** (up to 18+
  renders) even though wire values were already resolved in `HTTPClient`.

**Evidence:** `sensitive_data_masking_policy.py` lines 34–48 vs 49–54.

### MCP outbound (`_execute_mcp`)

Renders URL, body, and headers once each in `RequestService`; uses `MCPClientService.run`
(synchronous HTTP to remote MCP). Same worker thread as GUI sends.

---

## Template Rendering

### TemplateService (P-007 — PASS)

| Feature | Status |
| --- | --- |
| Shared `jinja2.Environment` per instance | PASS (PYPOST-146) |
| `@lru_cache(maxsize=256)` on `_compile_template` | PASS (PYPOST-628) |
| DEBUG `template_compile_cache hits/misses` | PASS |
| Render duration histogram | **Missing (P3)** |

**PYPOST-455 benchmark (local, 2026-06-11):**

| Scenario | µs/render |
| --- | ---: |
| Plain `{{host}}/{{id}}` | ~130 |
| Simulated HTTP request (URL + 5 hdr + 3 param + body) | ~708 |

Network I/O dominates. Compile cache addresses repeated identical templates (hover, resend).

### Call-site inventory

**28** `render_string` references across `pypost/` (including `curl_generator`,
`sensitive_data_masking_policy`, `http_client`, `request_service`). Highest fan-out: `HTTPClient
._prepare_request_kwargs` (7 direct calls + URL).

**Assessment:** Template rendering is **not** the current bottleneck. Missing duration metric limits
regression detection if templates grow (50+ placeholders per PYPOST-455 stress case ~1.4 ms).

---

## UI Responsiveness

### Patterns that protect the main thread (PASS)

| Pattern | Location | Threshold |
| --- | --- | --- |
| `RequestWorker` | `tabs_presenter.py` | All sends |
| `EnvironmentStorageWorker` | `env_presenter.py` (encrypted) | Env load/save |
| `PasteJsonFormatWorker` | `code_editor.py` | Paste > 100 KB |
| Search debounce | `response_view.py` | `LARGE_DOC_CHAR_THRESHOLD` 100 KB, 250 ms |
| Match count cap | `response_view.py` | 1000 matches on large docs |
| State debounce | `state_manager.py` | 300 ms before config write |

### Main-thread jank risks

| ID | Finding | Severity | Evidence |
| --- | --- | --- | --- |
| P-008 | `display_response` JSON pretty-print without size guard | **P2** | `response_view.py` 308–311 |
| P-009 | `refresh_tree` full `QStandardItemModel` rebuild | P2 | `collections_presenter.py` 108–126 |
| P-010 | `set_indent_size` re-parses entire body | P3 | `response_view.py` 268–273 |
| P-011 | Streaming chunks via `append_body` on main thread | P2 | Signal from worker; each chunk triggers QTextEdit insert |

**Note:** Streaming updates (`chunk_received` → `append_body`) keep partial UI feedback but still
marshal every chunk on the GUI thread. High-throughput streams can flood the event loop.

---

## MCP Server Threading

### Architecture (P-012 — PASS with P2 gap)

```text
MCPServerManager (daemon threading.Thread)
  → asyncio event loop + uvicorn
    → MCPServerImpl.call_tool (async)
      → run_in_threadpool(_execute_request_sync)
        → RequestService.execute()
```

**Evidence:** `mcp_server_impl.py` lines 117–118; `mcp_server.py` lines 94, 153–169.

| Aspect | Assessment |
| --- | --- |
| uvicorn off GUI thread | PASS |
| Sync execution bridged | PASS (`run_in_threadpool`) |
| Activity log + metrics on pool thread | PASS (thread-safe ring buffer) |
| Threadpool size / limit | **Not configured (P2)** — Starlette default |
| Shared `requests.Session` in `HTTPClient` | Potential contention under concurrent MCP tools |

Concurrent `call_tool` invocations share one `RequestService` / `HTTPClient` instance injected at
`MCPServerManager` construction. No explicit queue or rate limit.

---

## Large Collection Loading

### StorageManager.load_collections (P-013 — P2)

```python
for filename in os.listdir(self.collections_path):
    with open(...) as f:
        data = json.load(f)
        collection = Collection(**data)
```

- **Sequential** disk read per `.json` file.
- Runs on **main thread** via `RequestManager.__init__` → `reload_collections()`.
- No lazy load, pagination, or background worker (contrast `EnvironmentStorageWorker`).

### RequestManager index (PASS)

`_rebuild_index` provides O(1) `find_request` after load. Incremental tree updates
(`add_saved_request_to_tree`, `_insert_collection_into_tree`) avoid full rebuild on single saves.

### reload_collections user path (P-014 — P2)

`CollectionsPresenter.load_collections()` calls `reload_collections()` then `refresh_tree()` —
full disk read + full model rebuild. No progress indicator or incremental diff.

### save_collection (P3)

`collection.model_dump_json(indent=2)` writes entire collection atomically. Acceptable for typical
sizes; large collections rewrite full file on every request save.

---

## Memory Patterns

| Surface | Bound | Notes |
| --- | --- | --- |
| HTTP response body | **Unbounded** | List + join + `ResponseData` + `QTextEdit` (P1) |
| History entries | 500 cap | `HistoryManager.DEFAULT_MAX_ENTRIES` |
| MCP activity log | 100 cap | Ring buffer |
| History save snapshot | Full list copy | Async thread; 500 entries × field size |
| Tab isolation | `model_copy(deep=True)` | Intentional per-tab copies |
| Env save coalescing | Deep copy snapshot | `environment_storage_gateway.py` line 68 |

### History async save (P-015 — P3)

`_save_async` copies `list(self._entries)` under lock, then `json.dump(..., indent=2)` in daemon
thread. Debounced via `_save_pending` coalescing. Peak memory: live list + snapshot during write.

### Sensitive data masking duplicate render (P-006)

When `hidden_keys` set, masking path allocates `masked_variables` and re-renders all fields instead
of masking `resolved` wire values in place.

---

## Blocking I/O on Main Thread

| Operation | When | Module | Severity |
| --- | --- | --- | --- |
| `load_collections()` | `MainWindow` init | `request_manager.py` | **P1** |
| `refresh_tree()` | After init / reload | `collections_presenter.py` | P2 |
| `HistoryManager._load()` | `MainWindow` init | `history_manager.py` | P2 |
| `ConfigManager.load_config()` | `StateManager.__init__` | `config_manager.py` | P3 (small file) |
| `ConfigManager.save_config()` | Debounced UI state | `state_manager.py` | P3 |
| `StyleManager` directory scan | `MainWindow` init | `style_manager.py` | P3 |
| `load_environments()` sync path | Encryption off | `env_presenter.py` | P2 if many envs |
| `wait_idle` + `processEvents` | Tests/shutdown | `environment_storage_gateway.py` | P3 reentrancy |

**Startup sequence (`main_window.py` lines 64–101):**

1. `RequestManager(self.storage)` — **sync load all collections**
2. `HistoryManager()` — **sync load history.json**
3. `collections.refresh_tree()` — **sync build tree model**
4. `env.load_environments()` — async if encrypted, else sync

Encrypted startup defers tab/tree restore until `environments_loaded` (PASS). Collection load is
never deferred.

---

## Findings Summary

| ID | Severity | Topic | Recommendation |
| --- | --- | --- | --- |
| P-003 | P1 | Unbounded response buffering | Add configurable max body size; truncate or abort with error |
| P-013 | P1 | Collection load on main thread at startup | Background worker + signal to populate tree (mirror PYPOST-486) |
| P-008 | P2 | JSON pretty-print without size guard | Skip or defer format when body > 100 KB; raw text tab |
| P-006 | P2 | History masking re-renders | Mask `resolved` fields in place when wire values known |
| P-009 | P2 | Full tree rebuild on reload | Diff or virtualize; incremental reload API |
| P-014 | P2 | User-triggered collection reload blocks UI | Same background worker as startup |
| P-012 | P2 | MCP threadpool unconfigured | Document or cap concurrent `call_tool` executions |
| P-011 | P2 | Stream chunks on main thread | Throttle/coalesce UI updates for high-throughput SSE |
| P-005 | P2 | Post-script blocks worker | Document; optional timeout or subprocess isolation |
| P-004 | P2 | Retry sleep in worker | Acceptable; document worker occupancy |
| P-015 | P3 | History save full snapshot | Consider append-only or smaller indent for scale |
| P-007 | P3 | No template render duration metric | Add histogram when touching metrics registry |
| P-010 | P3 | `set_indent_size` full re-parse | Guard with large-doc threshold |

---

## Methodology Notes

Commands executed (2026-06-12):

```bash
rg -c 'render_string' pypost/
rg -l 'QThread' pypost/   # 4 modules
rg -l 'threading\.Thread' pypost/   # 3 modules
rg -n 'iter_content|processEvents|stream=True' pypost/
rg -n 'LARGE_DOC_CHAR_THRESHOLD|DEFAULT_MAX_ENTRIES' pypost/
```

No application code modified. Line numbers reference commit at audit date.

## Related Tests

| Area | Test modules |
| --- | --- |
| Response search large doc | `test_response_view_search.py` |
| Template compile cache | `test_template_service_caching_eval.py` |
| Async env storage | `test_environment_storage_gateway.py`, `test_env_persistence_e2e.py` |
| History cap / async save | `test_history_manager.py` |
| Request worker | `test_worker.py`, tabs presenter integration tests |

## Out of Scope

- Production load tests or memory profiling under sustained MCP traffic
- `requests` connection pool tuning
- Qt rendering/GPU performance
- Observability log/metrics cardinality (PYPOST-688)
- Server-side API optimization
