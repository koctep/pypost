# PYPOST-1371: Stress & edge-case payload test suite

## Research

### Existing Codebase Analysis

PyPost's response and editor code folding architecture was recently extended with asynchronous background scanning in `pypost/ui/widgets/fold/`:

1. **`FoldController` (`fold_controller.py`)**:
   - Manages code folding state (`_regions`, `_collapsed_ids`, `_header_by_block`) for host `QPlainTextEdit` instances.
   - Dispatches payload scanning based on size threshold:
     - Documents `< 500 KB` (`LARGE_DOCUMENT_THRESHOLD_BYTES = 500 * 1024`): parsed synchronously on UI thread via `scan_text(text, body_format)`.
     - Documents `>= 500 KB`: offloaded to `FoldScanWorker` (a `QThread` subclass).
   - Manages text edit debouncing via `_scan_timer` (200 ms interval).
   - Tracks document versioning via monotonic integer generation counter (`_generation`).
   - Cancels active in-flight worker threads via `requestInterruption()` when a newer scan generation is triggered.
   - Emits `scan_finished = Signal(list)` on both synchronous completion and background completion.

2. **`FoldScanWorker` (`fold_worker.py`)**:
   - Executes AST / region scanning in a secondary worker thread: `scan_text(self._text, self._body_format, is_interrupted=self.isInterruptionRequested)`.
   - Tracks live active worker instances in `_LIVE_WORKERS: ClassVar[set[FoldScanWorker]]`.
   - Emits `scan_completed = Signal(int, list)` or `scan_failed = Signal(int, str)`.
   - Periodically checks cooperative interruption during long-running scans.

3. **Format Scanners (`json_structure_scanner.py`, `xml_structure_scanner.py`, `yaml_structure_scanner.py`)**:
   - **`JsonStructureScanner`**: Validates syntax with `json.loads(text)`, catching only `json.JSONDecodeError`. If valid, runs state-machine character scanner `_scan_regions` checking `(i & 1023 == 0) and is_interrupted()`.
   - **`XmlStructureScanner`**: Validates syntax with `xml.etree.ElementTree.fromstring(text)`, catching only `ET.ParseError`. If valid, parses tags and attributes with `_scan_regions` checking `(index & 1023 == 0) and is_interrupted()`.
   - **`YamlStructureScanner`**: Parses documents with `yaml.compose_all(stream, Loader=yaml.SafeLoader)`, catching only `yaml.YAMLError`. Recurses through AST nodes with `_collect_regions(node, path, regions)`.

### Vulnerability & Edge-Case Findings

Through inspection of scanner implementations and language specifications, several critical failure vectors and edge cases were identified:

1. **Uncaught Parser Exceptions on Deep Nesting (`RecursionError`)**:
   - `JsonStructureScanner`: When parsing deeply nested structures (e.g. 100+ or 500+ nested brackets `[[[[...]]]]` or nested objects), `json.loads(text)` raises `RecursionError` in Python's standard library parser. Because `JsonStructureScanner` only catches `json.JSONDecodeError`, `RecursionError` escapes uncaught, crashing the worker thread or main thread.
   - `YamlStructureScanner`: Deeply nested mappings (e.g. 150+ levels of indentation) cause PyYAML's `SafeLoader` or recursive `_collect_regions` traversal to exceed Python's recursion limit, raising `RecursionError`. Because only `yaml.YAMLError` is caught, `RecursionError` crashes the application.
   - `XmlStructureScanner`: Deeply nested XML elements (e.g. 150+ nested tags) or hostile XML entity expansion can raise `RecursionError` or `ValueError`, which escape `ET.ParseError` handling.

2. **Truncated and Malformed Payload Boundaries**:
   - Truncated payloads cut at arbitrary byte offsets (e.g., incomplete multi-byte UTF-8, mid-tag `<root><tag attr="val`, partial YAML strings with dangling indentation, unclosed JSON quotes).
   - Scanners must safely handle unexpected EOF without infinite loops, index out of range errors, or unbounded memory allocations, returning an empty list `[]` of fold regions.

3. **Extreme Payloads (>10 MB) Resource & Thread Safety**:
   - Payloads exceeding 10 MB (up to 12 MB) must be processed cleanly without UI freezes.
   - `FoldController.LARGE_DOCUMENT_THRESHOLD_BYTES` (500 KB) guarantees that payloads > 10 MB are dispatched to background `FoldScanWorker` instances off the main Qt thread.
   - Generating 10 MB+ payloads programmatically in test fixtures avoids committing massive binary assets to git while exercising real-world memory bounds and thread lifecycles.
   - PyYAML pure-Python parsing of 10 MB+ payloads is computationally expensive; tests must verify that `FoldScanWorker` handles large payloads with explicit timeouts, and that cancellation during rapid edits cleanly aborts processing without leaking threads in `_LIVE_WORKERS`.

4. **High-Frequency Rapid Edits and Debounce Verification**:
   - When a user or automated stream types or pastes rapidly into a large document, `FoldController` debounces requests by 200 ms.
   - If multiple scans are triggered in quick succession, older in-flight workers must be interrupted, stale scan results (`generation != current_generation`) must be ignored, and only the latest scan results applied.
   - No worker threads must leak or remain running as zombies in `FoldScanWorker._LIVE_WORKERS`.

## Implementation Plan

### High-Level Workflow

The implementation follows a test-driven approach across four phases:

1. **Step 3: Failing Repro Test Suite (`tests/test_folding_stress_and_edge_cases.py`)**:
   - Implement test harness and synthetic payload generators.
   - Write failing repro tests targeting scanner crashes on deeply nested hierarchies (uncaught `RecursionError`) and edge-case malformed/truncated payloads.
   - Validate that tests fail predictably against current unhardened scanners before Step 4 fixes.

2. **Step 4: Scanner Resilience Hardening and Stress Suite Completion**:
   - Harden `JsonStructureScanner`, `XmlStructureScanner`, and `YamlStructureScanner` to catch `(RecursionError, ValueError)` in addition to library-specific parse errors (`JSONDecodeError`, `ET.ParseError`, `YAMLError`).
   - Implement robust error logging and empty region fallback.
   - Complete all test categories: truncated/malformed payloads, 100+ deep nesting, 10 MB+ payloads with background dispatch verification, and rapid edit debouncing/cancellation.
   - Ensure all tests pass with explicit `@pytest.mark.timeout` limits.

3. **Step 5–8: Post-Development Verification and Dev Docs**:
   - Clean up code, audit types and lints (`make lint`, `make typecheck`).
   - Document observability signals and performance metrics.
   - Update developer documentation under `doc/dev/`.

### Mandatory — Failing Repro (next Step 3)

- **Target Test Path**: `tests/test_folding_stress_and_edge_cases.py`
- **Failure Mechanics**:
  - Deeply nested JSON payload (e.g. 200 levels of nested arrays `[` * 200 + `]` * 200): `json.loads` raises `RecursionError`. Currently, `JsonStructureScanner.scan_text` only catches `json.JSONDecodeError`, allowing `RecursionError` to escape and crash the caller.
  - Deeply nested YAML payload (e.g. 200 levels of indented keys `k0:\n  k1:\n    k2:...`): PyYAML's `SafeLoader` or `_collect_regions` raises `RecursionError`. Currently, `YamlStructureScanner.scan_text` only catches `yaml.YAMLError`, allowing `RecursionError` to escape.
  - Deeply nested XML payload (e.g. 200 levels of `<n0><n1>...</n1></n0>`): `ET.fromstring` or recursive tree traversal raises `RecursionError` or `ValueError` that escapes `ET.ParseError`.
- **Expected Desired Behavior**:
  - The scanners and `FoldScanWorker` must catch all parsing exceptions, log a debug warning, and gracefully return an empty list `[]` of fold regions without raising unhandled exceptions or crashing.
- **Sequencing**:
  - Step 3 creates `tests/test_folding_stress_and_edge_cases.py` containing tests asserting that scanning deeply nested, truncated, and malformed payloads never raises exceptions and returns `[]`.
  - Running `make test` will confirm the repro failure (red tests raising `RecursionError`).
  - Step 4 hardens the scanners to catch `RecursionError` and `ValueError`, turning the tests green.

## Architecture

### System Module Diagram

```mermaid
flowchart TD
    subgraph TestSuite ["Stress Test Suite (tests/test_folding_stress_and_edge_cases.py)"]
        direction TB
        G1["Synthetic Truncated Generators<br/>(XML, YAML, JSON)"]
        G2["Deep Hierarchy Generators<br/>(100+ Nesting Depth)"]
        G3["10 MB+ Payload Generators<br/>(Synthetic In-Memory Buffers)"]
        G4["Rapid Edit Burst Harness<br/>(Simulated Typing / Pasting)"]
    end

    subgraph ControllerLayer ["PyPost Fold Controller & Worker Layer"]
        FC["FoldController<br/>(Debounce: 200ms, Threshold: 500KB)"]
        FW["FoldScanWorker<br/>(QThread Background Dispatch)"]
        LW["Worker Registry<br/>(FoldScanWorker._LIVE_WORKERS)"]
    end

    subgraph ScannerLayer ["Structure Scanners (pypost/ui/widgets/fold/)"]
        SS["scan_text(text, body_format, is_interrupted)"]
        JS["JsonStructureScanner<br/>(Guards: JSONDecodeError, RecursionError)"]
        XS["XmlStructureScanner<br/>(Guards: ParseError, RecursionError, ValueError)"]
        YS["YamlStructureScanner<br/>(Guards: YAMLError, RecursionError, ValueError)"]
    end

    subgraph PresentationLayer ["Editor & Presentation"]
        ED["QPlainTextEdit / FoldablePlainTextEdit"]
        RAW["Raw Document Text Buffer<br/>(Guaranteed Intact & Selectable)"]
    end

    TestSuite --> FC
    TestSuite --> SS
    FC -->|Size < 500 KB| SS
    FC -->|Size >= 500 KB| FW
    FW -->|Worker Thread| SS
    FW -.->|Tracks Lifecycle| LW
    SS --> JS
    SS --> XS
    SS --> YS
    JS -->|Fallback: []| FC
    XS -->|Fallback: []| FC
    YS -->|Fallback: []| FC
    FC -->|Update Visibility| ED
    ED --> RAW
```

### Module Breakdown and Responsibilities

| Module / Component | Path | Responsibility |
| --- | --- | --- |
| **Stress Test Suite** | `tests/test_folding_stress_and_edge_cases.py` | Houses test classes and cases covering truncated payloads, malformed syntax, deeply nested hierarchies (100+), 10 MB+ payloads, and high-frequency edit debouncing. |
| **Synthetic Payload Generators** | `tests/test_folding_stress_and_edge_cases.py` | Programmatic in-memory data builders generating deterministic truncated, malformed, deep, and 10MB+ payload strings without committing static binary blobs to git. |
| **Fold Controller** | `pypost/ui/widgets/fold/fold_controller.py` | UI thread manager orchestrating debounce timers, size threshold dispatch (500 KB), worker cancellation, and visibility application. |
| **Fold Scan Worker** | `pypost/ui/widgets/fold/fold_worker.py` | `QThread` offloading CPU-heavy AST parsing for large payloads; checks interruption flags and signals results. |
| **JSON Structure Scanner** | `pypost/ui/widgets/fold/json_structure_scanner.py` | Scans JSON text; guarded against `json.JSONDecodeError` and `RecursionError`. |
| **XML Structure Scanner** | `pypost/ui/widgets/fold/xml_structure_scanner.py` | Scans XML text; guarded against `ET.ParseError`, `RecursionError`, and `ValueError`. |
| **YAML Structure Scanner** | `pypost/ui/widgets/fold/yaml_structure_scanner.py` | Scans YAML text; guarded against `yaml.YAMLError`, `RecursionError`, and `ValueError`. |

### Test Categories and Specifications

#### Category A: Truncated & Malformed Payloads
- **Truncated XML**: Payload truncated abruptly at various byte offsets:
  - Inside tag name: `<root><pro`
  - Inside attribute key or value: `<root><item id="123`
  - Inside CDATA or comment: `<![CDATA[ some text `
  - Unclosed root element: `<root><child></child>` (missing `</root>`)
- **Malformed XML**:
  - Mismatched tags: `<root><child></other></root>`
  - Multiple root elements: `<root></root><root2></root2>`
  - Illegal characters / bad entity references: `<root>&invalid_entity;</root>`
- **Truncated & Malformed YAML**:
  - Truncated mapping key/value: `items:\n  - key: "val"\n  - incom`
  - Inconsistent indentation mixes (tabs and spaces).
  - Unclosed quotes and incomplete block scalars (`key: >\n  incomplete`).
- **Truncated & Malformed JSON**:
  - Truncated braces / brackets: `{"items": [{"id": 1}, {"id": `
  - Unclosed strings: `{"key": "truncated string...`
  - Trailing commas or duplicate colons.
- **Contract & Assertion**:
  - `scan_text(text, format)` must execute without throwing any uncaught exceptions and return `[]`.
  - Host `QPlainTextEdit` retains the raw text unmodified and readable.

#### Category B: Deeply Nested Hierarchies (100+ Levels)
- **Deep JSON**: 100 to 200 levels of nested arrays `[[[[...]]]]` and objects `{"a": {"a": ...}}`.
- **Deep XML**: 100 to 200 levels of `<node><node>...</node></node>`.
- **Deep YAML**: 100 to 200 levels of indented mappings `a:\n  b:\n    c:...`.
- **Contract & Assertion**:
  - Scanners must safely handle deep nesting without crashing on Python's recursion limit (`sys.getrecursionlimit()`).
  - Either valid fold regions are discovered up to safe limits or an empty region list `[]` is returned safely.
  - Zero unhandled `RecursionError` exceptions.

#### Category C: Extreme Payloads (>10 MB)
- **Synthetic 10 MB+ Payloads**:
  - JSON payload generated programmatically to ~10.5 MB consisting of large arrays of objects.
  - XML payload generated programmatically to ~10.5 MB with thousands of nested elements.
  - YAML payload generated programmatically to ~10.5 MB with repetitive structured blocks.
- **Contract & Assertion**:
  - Document size exceeds `LARGE_DOCUMENT_THRESHOLD_BYTES` (500 KB), guaranteeing dispatch to background `FoldScanWorker`.
  - UI thread remains responsive: `qapp.processEvents()` processes interactive events while worker runs in background.
  - Completion is signaled via `scan_finished` signal.
  - Memory consumption remains bounded; worker terminates cleanly and disowns references.
  - Explicit per-test timeout (e.g. `@pytest.mark.timeout(45)` or `timeout(60)`) enforces deterministic CI execution without hanging builds.

#### Category D: High-Frequency Rapid Edits and Cancellation
- **Rapid Edit Burst**:
  - Simulate typing or rapid document replacement on a 1 MB+ document (e.g. 5–10 rapid edits spaced 20 ms apart).
  - Verify that `FoldController` debouncing delays scanning until editing pauses (200 ms).
  - If a background worker is already executing from a previous scan, verify that `requestInterruption()` is invoked and the worker exits cooperatively.
  - Stale generation scan results (`generation != current_generation`) are discarded and do not overwrite the editor's active fold state.
  - Verify that at the end of the burst, exactly one final scan completes, and `FoldScanWorker._LIVE_WORKERS` contains zero leaked worker threads.

### Interface Definitions

```python
# Synthetic Payload Generators in tests/test_folding_stress_and_edge_cases.py
def generate_truncated_payload(format: BodyFormat, sample_text: str, cut_ratio: float = 0.5) -> str:
    """Return payload truncated at cut_ratio of length."""
    ...

def generate_deep_json(depth: int) -> str:
    """Generate syntactically valid JSON with specified nesting depth."""
    ...

def generate_deep_xml(depth: int) -> str:
    """Generate syntactically valid XML with specified nesting depth."""
    ...

def generate_deep_yaml(depth: int) -> str:
    """Generate syntactically valid YAML with specified nesting depth."""
    ...

def generate_oversized_payload(format: BodyFormat, target_bytes: int = 10 * 1024 * 1024 + 512 * 1024) -> str:
    """Generate synthetic payload exceeding 10 MB without disk I/O."""
    ...
```

## Q&A

- **Q1: Why are synthetic generators preferred over committing 10 MB sample files?**
  - **A**: Committing multi-megabyte binary or text files bloats the git repository history permanently, slows down clone operations, and risks merge conflicts. Programmatic generation is deterministic, consumes zero repo storage, and allows precise parameterization (size, depth, syntax error injection).
- **Q2: Why is `RecursionError` considered a scanner vulnerability?**
  - **A**: Python's standard `json.loads` and PyYAML's recursive loaders rely on the Python call stack. When presented with deeply nested documents (e.g., 200+ brackets or indentations), they exceed `sys.getrecursionlimit()`. Standard catch blocks (`except json.JSONDecodeError:` or `except yaml.YAMLError:`) do not catch `RecursionError`, causing unhandled exceptions in worker threads or the UI thread.
- **Q3: How do we prevent 10 MB YAML scans from timing out in CI?**
  - **A**: Pure Python PyYAML parsing can be slow for massive payloads. The stress test suite verifies that `FoldScanWorker` runs in a background thread, that cooperative cancellation works when interrupted, and that explicit per-test timeouts (`@pytest.mark.timeout(60)`) prevent test suite hangs. In production, documents that exceed reasonable execution limits can either be interrupted or cleanly fail back to raw text.
- **Q4: How do the stress tests verify thread safety and absence of leaks?**
  - **A**: `FoldScanWorker` maintains a class-level set `_LIVE_WORKERS`. The test suite verifies that after background processing completes or is cancelled, `len(FoldScanWorker._LIVE_WORKERS) == 0`.
