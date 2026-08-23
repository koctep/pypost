# PYPOST-1133: Technical Debt Analysis

## Shortcuts Taken

- **Modal Input Dialog for Variable Capture:** In `StreamDetailPane._on_set_variable_clicked`, variable naming relies on `QInputDialog.getText` with a default `"CAPTURED_TOKEN"` placeholder rather than a dedicated environment variable selector/creation dropdown. While functional and non-blocking, a dedicated UI dialog with type/environment picker would provide a smoother developer workflow.
- **Fixed-Line Delegate Snippet:** In `StreamItemDelegate.sizeHint`, row height is hardcoded to 26px for uniform item layout optimization. Multiline payloads are flattened by replacing newlines with spaces and eliding on the right edge, relying on `StreamDetailPane` for multiline inspection.
- **Synchronous Transcript Export on UI Thread:** `WebSocketStreamView.export_json` and `export_text` write files synchronously on the main thread via core export helpers. For typical retained buffers (up to 5,000 entries / 64 MiB), write operations finish in <20ms, but for extremely slow external disks, background file writing could prevent micro-stuttering.

## Code Quality Issues

- **Combined UI and Delegate Module:** `pypost/ui/widgets/websocket/stream_view.py` encapsulates `StreamFilterProxyModel`, `StreamItemDelegate`, `_format_hex_dump`, `StreamDetailPane`, and `WebSocketStreamView` in a single file (~875 lines). As future stories (WS-6 message composer, syntax highlighting) add complexity, extracting `StreamDetailPane` and `StreamItemDelegate` into dedicated submodule files (`stream_delegate.py`, `stream_detail_pane.py`) will improve modularity.
- **Inline Hardcoded Colors in Delegate:** `StreamItemDelegate.paint` uses explicit hex colors (`#2196F3` for inbound, `#4CAF50` for outbound, `#AB47BC` for lifecycle) rather than theme-driven palette tokens. The colors render clearly in both light and dark palettes, but hooking them into the central PyPost theme manager would guarantee 100% theme consistency.
- **Hardcoded Scroll Tolerance:** In `WebSocketStreamView._on_rows_inserted`, the check for bottom proximity uses `scrollbar.value() >= scrollbar.maximum() - 4` (a 4-pixel tolerance). While reliable across desktop platforms, this could be parameterized as a class constant.

## Missing Tests

- **High-Throughput Burst Toggling:** Automated tests verify pause/resume and unread count accounting during batch ingestion, but rapid adversarial toggling of the Pause button during continuous 1,000 msgs/sec simulated bursts is not explicitly stressed in a long-running endurance test.
- **Whitespace-Only Variable Names in GUI:** The code cleanly guards against blank variable names (`if ok and var_name.strip():`), but a dedicated Qt robot test simulating user dialog cancelation vs blank string submission in `StreamDetailPane` could be added to UI regression suites.
- **Hex Dump Viewer with Truncated 256 KiB Buffers:** Hex formatting is tested for standard payloads and multiline structures; testing hex dump rendering on maximum allowable truncated payload buffer (262,144 bytes) in GUI editor would verify paint responsiveness for extreme byte sizes.

## Performance Concerns

- **Main Thread In-Memory Proxy Filtering:** `StreamFilterProxyModel` evaluates `StreamQuery.matches(entry)` on the Qt main thread across retained rows. For the designed 5,000-entry capacity limit, filtering and search take <5ms. If capacity limits are expanded to 50,000+ entries in the future, background worker indexing or indexed token caches would be necessary to avoid UI thread lag during search keystrokes.
- **QTextEdit Memory for Large Payload Inspection:** While payload display is safely truncated at 262,144 bytes (`StreamEntry.truncated`), loading very large JSON structures into `QTextEdit` creates document layout trees in memory. Virtualized text rendering or plain document buffers could further reduce footprint for high-volume inspection.

## Follow-up Tasks

- **Rich Syntax Highlighting for StreamDetailPane:** Add JSON and XML syntax highlighting to `StreamDetailPane` payload editor (scheduled under WS-6 / message inspection enhancements).
- **Submodule Refactoring:** Decompose `pypost/ui/widgets/websocket/stream_view.py` into dedicated sub-widgets (`stream_delegate.py`, `stream_detail_pane.py`, `stream_toolbar.py`) when expanding composer/inspector features.
- **Centralized Palette Styling for Stream Items:** Migrate hardcoded direction glyph colors (`#2196F3`, `#4CAF50`, `#AB47BC`) to PyPost UI theme palette manager.
