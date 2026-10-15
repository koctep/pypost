# PYPOST-1370: Technical Debt Analysis

## Shortcuts Taken

- **Dedicated `QThread` Instantiation Per Scan**:
  Instead of utilizing a shared `QThreadPool` or a persistent background worker thread with a task queue, `FoldController._run_scan` instantiates and starts a new dedicated `FoldScanWorker(QThread)` instance whenever a document exceeding `LARGE_DOCUMENT_THRESHOLD_BYTES` (500 KB) triggers a scan. While superseded workers are cooperatively interrupted via `requestInterruption()` and scheduled for cleanup via `worker.finished.connect(worker.deleteLater)` and `_LIVE_WORKERS` registry tracking, rapid burst edits can temporarily spawn multiple OS threads while previous workers wind down.
- **Full Text String Snapshotting**:
  The controller passes full in-memory Python strings (`text = self._editor.toPlainText()`) into `FoldScanWorker` rather than leveraging zero-copy text views (`memoryview`, chunked iterators, or document buffer pointers). For documents between 500 KB and several megabytes, taking a full snapshot of the text buffer is straightforward and thread-safe, but creates transient string allocations on the Python heap.
- **Synchronous Upfront Document Parsing Before Region Traversal**:
  In `JsonStructureScanner`, `json.loads(text)` is executed upfront as a validation pass before token scanning starts. Similarly, `XmlStructureScanner` runs `xml.etree.ElementTree.fromstring(text)` upfront. While this prevents scanning malformed payloads, these standard library C-extensions / parsers run atomically and cannot be cooperatively cancelled midway through their parse pass if an interruption is requested while they are executing.
- **Coarse Cooperative Cancellation Polling Interval**:
  The custom token scanners poll `is_interrupted()` at power-of-two character boundaries (`(i & 1023 == 0)`) in JSON and XML, and between document blocks in YAML `yaml.compose_all`. While this reduces callback overhead during character iteration, it means cancellations are checked every 1 KB of input rather than per token.

## Code Quality Issues

- **Worker Thread Pool vs Dedicated QThread Instance**:
  `FoldScanWorker` subclasses `QThread` directly and manages its lifecycle through a class-level `_LIVE_WORKERS` registry and `deleteLater()` slot connection. A cleaner architectural pattern would be a dedicated worker thread with an event queue or a `QThreadPool` with `QRunnable` tasks managed by a central concurrency manager. This would eliminate per-scan thread creation overhead, OS thread churn, and explicit global worker registry tracking.
- **O(N*M) Collapsed State Re-matching**:
  `FoldController._apply_scan_results` invokes `_region_unchanged` for each collapsed region ID against `new_regions` list linearly. While typical documents have few collapsed regions, documents with thousands of folded structures could benefit from indexing `new_regions` by `region_id` into a dictionary for O(1) membership and geometry lookup.
- **Direct Subclassing and Qt Event Loop Dependency in Worker Tests**:
  `FoldScanWorker` depends directly on PySide6 signals and event loop processing (`QApplication.processEvents()` inside helper methods). Decoupling the AST structure scanning engine completely into pure Python functions without Qt dependencies (as was started with `scan_text(text, body_format)`) makes headless testing faster and allows executing scanners in non-Qt worker contexts (e.g. `multiprocessing` or `concurrent.futures.ProcessPoolExecutor`) if GIL contention ever becomes an issue.

## Missing Tests

- **Stress Testing Multi-Megabyte Payloads (5 MB - 50 MB) and Deep Hierarchies**:
  The current automated suite tests payloads up to ~600 KB to verify the threshold dispatch and thread boundary. Comprehensive stress testing with 5 MB+ payloads, extreme line counts (100k+ lines), and deeply nested AST hierarchies (> 50 levels of JSON arrays/objects, XML tags, or YAML sequences) is explicitly addressed by upcoming task **[PYPOST-1371](https://pypost.atlassian.net/browse/PYPOST-1371)**.
- **High-Frequency Edit Burst Concurrency Tests**:
  Simulating 20+ edits within 50ms to verify that the generation counter, thread interruption, and Qt event delivery gracefully handle rapid thread superseding without thread exhaustion or memory spikes.
- **Format Switching Under In-Flight Worker**:
  Verifying behavior when a user switches format (e.g., JSON -> XML -> YAML -> PLAIN) while an active background scan is running for the previous format.
- **Memory Reclamation / GC Verification**:
  Automated tests verifying that `_LIVE_WORKERS` registry empties and large payload text strings are garbage-collected once background workers finish or are interrupted.

## Performance Concerns

- **Memory Footprint of Full Text Duplication**:
  Calling `self._editor.toPlainText()` duplicates the editor's text buffer into a Python unicode string. For a 5 MB payload, `toPlainText()` allocates ~5-10 MB of memory. If a second edit occurs before the first worker finishes, multiple large text buffers can reside concurrently in memory. Slicing or streaming buffer wrappers could alleviate this pressure for multi-megabyte payloads.
- **Python Global Interpreter Lock (GIL) Contention**:
  Even though `FoldScanWorker` runs on a separate OS thread (`QThread`), AST parsing in pure Python or Python C-extensions (like standard `json` and `yaml`) acquires the GIL. Under heavy parsing workloads, GIL contention could momentarily delay Python-based UI callbacks on the main thread, even though C++ Qt event processing and painting continue uninterrupted.
- **Repeated Line Offset Calculations**:
  `scan_utils.line_at_offset(text, offset)` counts newline characters (`text.count("\n", 0, offset)`) for each fold region boundary. For large payloads with thousands of fold regions, repeatedly scanning string prefixes to compute line numbers scales quadratically with respect to document size. Precomputing newline index offsets via binary search (`bisect`) would reduce this from O(K * N) to O(N + K log L).

## Follow-up Tasks

- **[PYPOST-1371](https://pypost.atlassian.net/browse/PYPOST-1371): Stress and Edge-Case Test Suite (2 SP)**:
  Implement automated stress tests with 5 MB+ payloads, extreme nesting depth, truncated/malformed payloads, and high-frequency edit bursts with bounded timeouts (upcoming Sprint 2031 task).
- **[PYPOST-1400](https://pypost.atlassian.net/browse/PYPOST-1400): [PYPOST-1370] Refactor background fold scanner to persistent worker thread pool (3 SP)**:
  Refactor `FoldScanWorker` from per-scan `QThread` instances to a pooled `QRunnable` or persistent background worker thread to eliminate OS thread creation overhead during frequent document edits.
- **[PYPOST-1401](https://pypost.atlassian.net/browse/PYPOST-1401): [PYPOST-1370] Chunked zero-copy streaming for large document fold scanning (3 SP)**:
  Evaluate chunked text reading or streaming views to reduce memory churn from `toPlainText()` copies on multi-megabyte payloads.
- **[PYPOST-1402](https://pypost.atlassian.net/browse/PYPOST-1402): [PYPOST-1370] Precompute newline index for O(log L) fold boundary line lookups (2 SP)**:
  Precompute newline offsets during scanning so that `line_at_offset` lookups operate in O(log L) time via binary search rather than counting newlines repeatedly across large text slices.
- **NON-BLOCKER — pre-existing**:
  - `tests/test_check_lock.py::test_repro_check_lock_dev_detects_no_drift` under Jira issue **[PYPOST-1397](https://pypost.atlassian.net/browse/PYPOST-1397)** (Dev lock drift detection pre-existing failure in repository tooling suite).
