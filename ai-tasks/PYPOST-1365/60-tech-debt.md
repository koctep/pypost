# PYPOST-1365: Technical Debt Analysis

## Shortcuts Taken

- **Duplication between `CodeEditor` and `FoldableCodeView`**: Rather than refactoring `CodeEditor`
  to inherit from a new shared base class (e.g. `FoldablePlainTextEdit`), `FoldableCodeView` was
  created as a standalone widget subclassing `QPlainTextEdit`. This deliberate shortcut was taken to
  prevent destabilizing `CodeEditor`'s complex editing machinery (variable auto-completion popups,
  bracket pairing, paste JSON format background workers, and validation controllers) while
  delivering read-only code folding in `ResponseView`.
- **Gutter geometry and paint logic replication**: Gutter sizing calculations, line number area
  positioning, and chevron click event handling are replicated between `FoldableCodeView` and
  `CodeEditor` instead of being encapsulated in a reusable mixin or shared gutter controller.

## Code Quality Issues

- **Shared Gutter / Chevron Painting**: The gutter painting logic in `line_number_area_paint_event`
  and mouse press handling in `line_number_area_mouse_press` are nearly identical between
  `FoldableCodeView` and `CodeEditor`. Extracting a shared `FoldableGutterMixin` or consolidating
  gutter event handling into `LineNumberArea` would eliminate code duplication and simplify
  long-term maintenance.
- **YAML Format Sniffing Heuristic**: The heuristic in `detect_body_format` checks for `":"` and
  `"\n"` before invoking `yaml.safe_load`. While effective for standard YAML response payloads,
  arbitrary multi-line text containing colons could trigger unnecessary `yaml.safe_load` parsing
  attempts during fallback detection.

## Missing Tests

- **Edge-case payload streams**: Additional automated test coverage is needed for malformed XML
  and YAML streams (e.g., mismatched closing tags, incomplete entities, deeply recursed documents)
  to ensure scanners recover without throwing unhandled exceptions.
- **Very large response documents (> 10MB)**: Current test cases test typical API response payloads
  and large doc skipping (> 100 KB), but lack dedicated performance tests for documents exceeding
  10 MB to measure memory overhead and scanning latency.
- **Concurrent background updates**: Test coverage for scenarios where response data is replaced
  rapidly while a debounced fold scan timer (`FoldController._scan_timer`) is pending.

## Performance Concerns

- **Main Thread Scanning on Large Documents**: `FoldController` executes `_run_scan`
  synchronously on the main Qt GUI thread after a 200 ms debounce timer. Although format skipping
  handles documents exceeding `LARGE_DOC_CHAR_THRESHOLD` (100 KB) in pretty-printing, for large
  structured payloads (e.g., several megabytes), AST parsing (`json.loads`, `yaml.compose_all`,
  `xml.etree.ElementTree`) could cause momentary frame drops on the main UI thread. A future
  background worker or threaded scanner pattern could offload parsing.

## Follow-up Tasks

- **Extract Shared Foldable Editor Base Class (Priority: Medium)**: Refactor `FoldableCodeView` and
  `CodeEditor` to inherit from a common `FoldablePlainTextEdit` base or share gutter management
  mixins to eliminate duplicate line-number and chevron painting logic.
  Jira: [PYPOST-1369](https://pypost.atlassian.net/browse/PYPOST-1369)
- **Background / Asynchronous Folding Scanner for Large Documents (Priority: Low)**: Offload fold
  region discovery AST parsing to a background `QThread` or worker for payloads exceeding 500 KB,
  ensuring the UI thread remains completely fluid.
  Jira: [PYPOST-1370](https://pypost.atlassian.net/browse/PYPOST-1370)
- **Stress & Edge-Case Payload Test Suite (Priority: Low)**: Implement automated stress tests with
  truncated/malformed YAML/XML payloads and payloads > 10 MB with explicit test timeouts.
  Jira: [PYPOST-1371](https://pypost.atlassian.net/browse/PYPOST-1371)
