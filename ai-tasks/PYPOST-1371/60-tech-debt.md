# PYPOST-1371: Technical Debt Analysis

## Shortcuts Taken

- **Fallback to Empty Fold Regions `[]` on Syntax or Recursion Errors**:
  When a syntax error, recursion limit, or value error occurs during AST parsing in `JsonStructureScanner`, `YamlStructureScanner`, or `XmlStructureScanner`, the scanners catch the exception and immediately return `[]`. While this provides robust crash immunity and prevents editor hangs on malformed or truncated inputs, it discards potential partial or line-based fold regions for syntactically valid outer blocks or indentation-based folds (e.g., folding valid outer objects when an inner token is incomplete while the user is typing).
- **All-or-Nothing Truncation Parsing**:
  Truncated documents are handled as standard parse failures returning `[]`. No heuristic parser recovery or incremental prefix parsing is attempted up to the point of truncation.
- **Deep Recursion Monkeypatching in Unit Tests**:
  While `YamlStructureScanner`'s recursion safety is tested with a real 500-level deeply nested YAML payload triggering PyYAML's recursion limits end-to-end, `JsonStructureScanner` and `XmlStructureScanner` simulate recursion limit handling using `pytest.MonkeyPatch` on `json.loads` and `xml.etree.ElementTree.fromstring`. This avoids C-level stack overflow crashes in CPython's standard library C extensions on extreme recursion depths, but relies on mocked error injection rather than a pure Python parser's natural stack exhaustion.

## Code Quality Issues

- **Duplicated Exception Handling Across Scanners**:
  `JsonStructureScanner.scan_text`, `YamlStructureScanner.scan_text`, and `XmlStructureScanner.scan_text` duplicate identical `try / except (ParserError, RecursionError, ValueError) as exc:` blocks and structured `logger.warning("%s_scan_parse_skipped error_type=%s length=%d", ...)` logging logic. This pattern could be refactored into a reusable function decorator or shared helper (e.g., `@safe_scan(...)` or `_safe_parse_guard(...)`) to eliminate boilerplate and ensure uniform telemetry across all present and future format scanners.
- **Hardcoded Constants in Stress Test Generators**:
  In `tests/test_folding_stress_and_edge_cases.py`, constants such as chunk size (`200_000`), default recursion depth (`200` / `500`), and target size (`10 * 1024 * 1024 + 1024`) are hardcoded literals in the synthetic generator helper functions instead of module-level named constants.
- **Redundant Document Empty Checks**:
  Scanners perform redundant emptiness checks (`if not text or not text.strip(): return []`) both in their public entrypoint `scan_text` and within private traversal functions. While harmless, consolidating the precondition check in the entrypoint would streamline scanner implementations.

## Missing Tests

- **Binary Garbage and Malformed Byte Injection**:
  No tests currently verify how the text editor and scanners behave when binary garbage (e.g., null bytes `\x00`, invalid Unicode surrogates, control sequences, random bytes from compiled binaries) is injected into the editor buffer or `scan_text`.
- **Property-Based Fuzz Testing**:
  The current test suite covers targeted malformed inputs and cut ratios, but lacks property-based fuzz testing (such as with `Hypothesis` or a random bit-flip mutator) to fuzz valid JSON/YAML/XML structures and assert invariant guarantees (e.g., `scan_text` never raises an unhandled exception or enters an infinite loop).
- **Concurrent Multi-Editor Stress Testing**:
  `TestRapidEditsAndDebounce` verifies burst edits against a single `FoldController`. Testing multiple concurrent editor tabs or controllers concurrently dispatching scans and cancellations to the background thread pool would provide deeper verification of thread isolation and system stability under load.
- **Partial and Indentation-Based Fallback Tests**:
  Because fallback to indentation-based line folding is not yet implemented for malformed payloads, tests verifying graceful degradation from AST folding to line-indent folding do not yet exist.

## Performance Concerns

- **Runtime Cost of In-Memory Synthetic 10 MB Payload Generator in CI**:
  `TestOversizedPayloads.test_oversized_payload_background_dispatch_and_completion` generates and parses a 10.5 MB synthetic JSON document dynamically in memory, taking ~1.5 to 2.5 seconds. While well within the 30-second test timeout, running full 10 MB synthetic payload generation on every local fast test run adds non-trivial CPU and memory overhead. Moving large multi-megabyte stress tests to a separate `@pytest.mark.stress` or `@pytest.mark.slow` tier would keep the primary `make test` suite ultra-fast.
- **Memory Spikes During Large Payload Parsing**:
  Generating a 10 MB string, converting it to a `QPlainTextEdit` buffer, and parsing it via `json.loads` creates multiple transient copies in Python and Qt memory, resulting in memory allocation spikes (tens of megabytes). In low-memory CI containers or constrained runner environments, this could lead to memory pressure.
- **Synchronous Scan Latency for Payloads Just Below Threshold**:
  Documents just below the 500 KB threshold (e.g., 400–499 KB) are parsed synchronously on the main thread. If a payload of that size contains intricate nesting or millions of tokens, synchronous AST parsing can cause noticeable UI frame drops or typing latency.

## Follow-up Tasks

- **[PYPOST-1403](https://pypost.atlassian.net/browse/PYPOST-1403): Refactor scanner exception handling into unified `@safe_scan` decorator (2 SP)**:
  Extract duplicated `try/except` and structured warning logging across `JsonStructureScanner`, `YamlStructureScanner`, and `XmlStructureScanner` into a shared parser wrapper to DRY up scanner logic.
- **[PYPOST-1404](https://pypost.atlassian.net/browse/PYPOST-1404): Fallback line/indentation folding for malformed or truncated documents (3 SP)**:
  Investigate and implement partial folding or indentation-based folding fallback when AST parsing fails, preserving outer foldable regions while editing malformed files.
- **[PYPOST-1405](https://pypost.atlassian.net/browse/PYPOST-1405): Property-based fuzz testing and binary garbage injection for editor scanners (3 SP)**:
  Introduce Hypothesis fuzzing and binary payload testing to rigorously verify scanner crash-resilience against random bit flips and control characters.
- **[PYPOST-1406](https://pypost.atlassian.net/browse/PYPOST-1406): Separate `@pytest.mark.stress` tier for > 10 MB payload tests (2 SP)**:
  Tag multi-megabyte payload and background worker stress tests with `@pytest.mark.stress` so fast CI suites can execute a lightweight smoke test while full stress tests run in nightlies or dedicated stress pipelines.
- **NON-BLOCKER — pre-existing**:
  - `tests/test_check_lock.py::test_repro_check_lock_dev_detects_no_drift` under Jira issue **[PYPOST-1397](https://pypost.atlassian.net/browse/PYPOST-1397)** (Dev lock drift detection pre-existing failure in repository tooling suite).
