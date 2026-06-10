# PYPOST-469: Copy from history page

## Research

- **History Data**: The `HistoryEntry` model in `pypost/models/models.py` stores the *resolved* request data (`method`, `url`, `headers`, `body`). This means we do not need to perform variable substitution or template rendering when generating a cURL command from a history entry.
- **cURL Generation**: The existing `CurlGenerator` in `pypost/core/curl_generator.py` expects a `RequestData` object and a `TemplateService`. Since `HistoryEntry` is already resolved, it's cleaner and more efficient to add a new method `generate_from_history(entry: HistoryEntry) -> str` to `CurlGenerator` that directly formats the resolved data into a cURL command.
- **UI Components**:
  - `HistoryPanel` (`pypost/ui/widgets/history_panel.py`) contains a `QListWidget` for history items. It already has a context menu (`_on_context_menu`) where we can add the "Copy as cURL" action.
  - Keyboard shortcuts can be added using `QShortcut` with `QKeySequence.Copy` attached to the `HistoryPanel` or its list widget.
  - `MainWindow` (`pypost/ui/main_window.py`) inherits from `QMainWindow`, which provides a built-in status bar via `self.statusBar()`.

## Implementation Plan

1. **Update `CurlGenerator`**:
   - Add a static method `generate_from_history(entry: HistoryEntry) -> str`.
   - The method will build the cURL command using `entry.method`, `entry.url`, `entry.headers`, and `entry.body`, and format it safely using `shlex.join` (or `subprocess.list2cmdline` on Windows).

2. **Update `HistoryPanel`**:
   - Define a new signal: `curl_copied = Signal()`.
   - In `_build_ui`, add a `QShortcut` for `QKeySequence.Copy` (Cmd/Ctrl+C) that triggers a copy action for the selected item.
   - In `_on_context_menu`, add a "Copy as cURL" action before the existing "Delete" action.
   - Implement a `_copy_as_curl(item)` method that retrieves the `HistoryEntry`, calls `CurlGenerator.generate_from_history`, copies the result to `QApplication.clipboard()`, and emits the `curl_copied` signal.

3. **Update `MainWindow`**:
   - In `_wire_signals`, connect `self.history_panel.curl_copied` to a new slot `_on_curl_copied`.
   - Implement `_on_curl_copied` to display a temporary message in the status bar: `self.statusBar().showMessage("Copied to clipboard", 3000)`.

## Architecture

- **`CurlGenerator`**: Extended to handle pre-resolved `HistoryEntry` objects directly, bypassing the `TemplateService` dependency.
- **`HistoryPanel`**: Acts as the initiator of the copy action. It handles the user interaction (context menu, shortcut), interacts with the system clipboard, and decouples itself from the main window by emitting a `curl_copied` signal.
- **`MainWindow`**: Listens for the `curl_copied` signal and handles the application-level visual feedback (status bar message), maintaining the separation of concerns between the widget and the main window.

## Q&A

- **Q:** Do we need to re-render variables for history items when copying as cURL?
  **A:** No, `HistoryEntry` stores the request exactly as it was sent (resolved URL, headers, and body). We can use this data directly.
- **Q:** Where should the clipboard interaction happen?
  **A:** In `HistoryPanel`, as it has direct access to the selected item and the user action context.
- **Q:** How is the status bar updated?
  **A:** `HistoryPanel` will emit a `curl_copied` signal, which `MainWindow` will catch to call `self.statusBar().showMessage(...)`. This avoids passing a reference of `MainWindow` into `HistoryPanel`.
