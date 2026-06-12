# PYPOST-689: Technical Debt Analysis

**Task type:** Performance and scalability audit (no application code changes).

**Source:** `30-audit-report.md` — P1/P2/P3 remediation recommendations.

Twelve remediation items for follow-up ticketing.

## Shortcuts Taken

- **Static analysis only:** No memory profiler, load test, or Qt main-thread instrumentation.
- **Benchmark cross-ref:** PYPOST-455 micro-benchmarks cited; not re-run for this audit.
- **No code fixes in scope:** Findings document gaps; remediation deferred to follow-up work.

## Code Quality Issues

Performance issues observed in the audited codebase (not introduced by this task):

- **Unbounded response buffering (P1):** `HTTPClient` joins full body with no size cap.
- **Collection load on main thread (P1):** `RequestManager.__init__` sync `load_collections`.
- **JSON pretty-print on main thread (P2):** `ResponseView.display_response` lacks large-doc guard.
- **History masking re-renders (P2):** `SensitiveDataMaskingPolicy` when `hidden_keys` set.
- **Full tree rebuild (P2):** `refresh_tree` on every collection reload.

## Missing Tooling

- No configurable `max_response_bytes` setting or metric
- No background collection load worker (unlike `EnvironmentStorageWorker`)
- No template render duration histogram
- No startup timing spans for main-thread I/O phases

## Performance Concerns

See findings P-003 through P-015 in `30-audit-report.md`. Highest risk: OOM on large HTTP
responses and startup freeze with many/large collection files.

## Follow-up Tasks

### P1 — Critical / OOM risk or startup main-thread block

#### R-P1-001 — Cap HTTP response body size in HTTPClient

- **Priority:** P1
- **Finding refs:** P-003
- **Description:** `iter_content` accumulates all chunks into a list and `"".join()` with no
  maximum. Large downloads can exhaust memory in the worker and duplicate in `ResponseView`.
- **Remediation:** Add `AppSettings.max_response_bytes` (or constant default, e.g. 50 MB);
  stop reading when exceeded; return structured `ExecutionError` with partial body option.
  Emit counter `response_body_truncated_total`. Update tests with mocked oversized stream.
- **Jira:** [PYPOST-753](https://pypost.atlassian.net/browse/PYPOST-753)

#### R-P1-002 — Load collections off the main thread at startup

- **Priority:** P1
- **Finding refs:** P-013
- **Description:** `MainWindow` constructs `RequestManager`, which synchronously reads every
  `collections/*.json` and blocks first paint.
- **Remediation:** Introduce `CollectionStorageWorker` + gateway mirroring
  `EnvironmentStorageGateway`; defer `refresh_tree` until `load_completed` signal. Show splash
  or empty tree with loading state. Preserve `RequestManager` index API.

### P2 — Meaningful latency or scalability gaps
- **Jira:** [PYPOST-754](https://pypost.atlassian.net/browse/PYPOST-754)

#### R-P2-001 — Guard JSON pretty-print in ResponseView for large bodies

- **Priority:** P2
- **Finding refs:** P-008
- **Description:** `display_response` always runs `json.loads` + `json.dumps(indent=…)` on the
  main thread. Search path already uses `LARGE_DOC_CHAR_THRESHOLD` (100 KB); display does not.
- **Remediation:** When `len(body_str) > LARGE_DOC_CHAR_THRESHOLD`, set raw text without
  pretty-print; optional lazy format via `PasteJsonFormatWorker` pattern. Add test mirroring
  `test_response_view_search.py` large-doc cases.
- **Jira:** [PYPOST-755](https://pypost.atlassian.net/browse/PYPOST-755)

#### R-P2-002 — Mask resolved fields in history without re-rendering templates

- **Priority:** P2
- **Finding refs:** P-006
- **Description:** When `hidden_keys` is non-empty, `SensitiveDataMaskingPolicy` re-renders URL,
  headers, and body via `TemplateService` instead of masking `ResolvedRequestFields` in place.
- **Remediation:** Apply placeholder substitution on `resolved.url/headers/body` when
  `resolved` is provided; fall back to re-render only when resolved unavailable (MCP edge cases).
- **Jira:** [PYPOST-756](https://pypost.atlassian.net/browse/PYPOST-756)

#### R-P2-003 — Background collection reload for user-triggered refresh

- **Priority:** P2
- **Finding refs:** P-014
- **Description:** `CollectionsPresenter.load_collections()` sync reloads disk and rebuilds
  entire `QStandardItemModel`.
- **Remediation:** Reuse collection storage worker from R-P1-002; disable reload action while
  busy; incremental `refresh_tree` diff if cheap.
- **Jira:** [PYPOST-757](https://pypost.atlassian.net/browse/PYPOST-757)

#### R-P2-004 — Incremental tree updates instead of full refresh_tree where possible

- **Priority:** P2
- **Finding refs:** P-009
- **Description:** `refresh_tree` clears model and rebuilds all nodes even when single collection
  changed externally.
- **Remediation:** Extend incremental APIs (`add_saved_request_to_tree` pattern) for external
  file changes; full rebuild only on explicit "Reload all".
- **Jira:** [PYPOST-758](https://pypost.atlassian.net/browse/PYPOST-758)

#### R-P2-005 — Document or limit MCP call_tool threadpool concurrency

- **Priority:** P2
- **Finding refs:** P-012
- **Description:** Starlette `run_in_threadpool` uses default pool; concurrent MCP tools share
  one `RequestService` / `HTTPClient` without explicit limit.
- **Remediation:** Document concurrency model in `mcp_integration.md`; consider semaphore or
  configurable max concurrent tool executions; metric for queue depth if limited.
- **Jira:** [PYPOST-759](https://pypost.atlassian.net/browse/PYPOST-759)

#### R-P2-006 — Throttle streaming chunk UI updates

- **Priority:** P2
- **Finding refs:** P-011
- **Description:** Each `iter_content` chunk emits `chunk_received` → `append_body` on the main
  thread. High-frequency SSE can flood Qt event loop.
- **Remediation:** Coalesce chunks in worker (time or byte threshold) before signal emit; or
  buffer in presenter with `QTimer` flush at 16–50 ms.

### P3 — Minor hygiene
- **Jira:** [PYPOST-760](https://pypost.atlassian.net/browse/PYPOST-760)

#### R-P3-001 — Add template render duration histogram

- **Priority:** P3
- **Finding refs:** P-007
- **Description:** Only attempt counters exist; PYPOST-455 used ad-hoc micro-benchmarks.
- **Remediation:** Add `template_expression_render_duration_seconds` histogram labeled by
  `render_path`; optional high-cardinality guard.
- **Jira:** [PYPOST-761](https://pypost.atlassian.net/browse/PYPOST-761)

#### R-P3-002 — Defer or async HistoryManager startup load

- **Priority:** P3
- **Finding refs:** Blocking I/O table
- **Description:** `HistoryManager._load` reads up to 500 entries synchronously during
  `MainWindow` init.
- **Remediation:** Lazy-load on first history panel open, or load in daemon thread with empty
  panel until ready. Low priority if files stay small.
- **Jira:** [PYPOST-762](https://pypost.atlassian.net/browse/PYPOST-762)

#### R-P3-003 — Apply large-doc guard to set_indent_size refresh

- **Priority:** P3
- **Finding refs:** P-010
- **Description:** Changing indent re-parses and reformats entire `QTextEdit` contents.
- **Remediation:** Skip JSON reformat when `len(text) > LARGE_DOC_CHAR_THRESHOLD`.
- **Jira:** [PYPOST-763](https://pypost.atlassian.net/browse/PYPOST-763)

#### R-P3-004 — Document client thread model in dev docs

- **Priority:** P3
- **Finding refs:** Worker inventory
- **Description:** QThread vs daemon thread boundaries are implicit across modules.
- **Remediation:** Add "Thread model" section to `performance_audit.md` with diagram; link
  from `architecture.md`.
- **Jira:** [PYPOST-764](https://pypost.atlassian.net/browse/PYPOST-764)

## Blocker Review

**SAFE TO CLOSE** — audit deliverables complete; no application code changes required.
Response size cap and async collection load should be scheduled first. Twelve remediation items
documented above.
