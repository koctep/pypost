# Copy cURL Feature

## Overview
The "Copy cURL" feature allows developers to generate a valid cURL command based on their currently configured HTTP request in the UI (including method, URL, headers, and body), render it with their current environment variables, and copy it directly to their system clipboard. It also supports copying a previously executed request directly from the History panel.

## Architecture
- **`CurlGenerator` (`pypost/core/curl_generator.py`)**: The core utility class responsible for rendering variables and constructing a shell-escaped cURL command string. It provides two methods: `generate()` for active requests and `generate_from_history()` for resolved history entries.
- **`RequestWidget` (`pypost/ui/widgets/request_editor.py`)**: The UI component that presents the "Copy cURL" action inside the "Actions" drop-down menu. It emits a `copy_curl_requested` signal containing the current `RequestData` when triggered.
- **`TabsPresenter` (`pypost/ui/presenters/tabs_presenter.py`)**: Acts as the orchestrator for `RequestWidget`. It connects to the `copy_curl_requested` signal, uses `CurlGenerator.generate()` to render the command with the currently active environment variables, and copies the resulting string to the system clipboard.
- **`HistoryPanel` (`pypost/ui/widgets/history_panel.py`)**: The sidebar panel showing executed requests. Provides a context menu and a keyboard shortcut (Cmd/Ctrl+C) to copy the selected history entry as a cURL command. Emits a `curl_copied` signal when successful.
- **`MainWindow` (`pypost/ui/main_window.py`)**: Connects to the `HistoryPanel.curl_copied` signal to display a status bar notification when a cURL command is successfully copied from the history.

## API / Usage

### `CurlGenerator.generate(request, variables, template_service)`
Generates a valid cURL command string from the active request data and variables.

- **request** (`RequestData`): The request configuration including URL, method, headers, parameters, and body.
- **variables** (`dict`): The current environment variables to render templates with.
- **template_service** (`TemplateService`): The service responsible for interpolating variables into the strings.
- **Returns** (`str`): The properly escaped cURL command string (uses `subprocess.list2cmdline` on Windows, and `shlex.join` on Unix).

### `CurlGenerator.generate_from_history(entry)`
Generates a valid cURL command string directly from a resolved history entry.

- **entry** (`HistoryEntry`): The history entry containing the resolved URL, method, headers, and body.
- **Returns** (`str`): The properly escaped cURL command string.

### `HistoryPanel` Signals
- **`curl_copied`**: Emitted when a user successfully copies a cURL command from a history entry.

## Configuration
There are no specific configuration settings for this feature. It relies on the active environment variables (for active requests) and the current request data or history entry data.

## Troubleshooting
- **Missing or incorrect variables**: If variables are not correctly resolved in the generated cURL command for an active request, ensure that the active environment contains the expected keys, and check the status of `TemplateService` rendering.
- **Copy to clipboard failing**: In case the copy operation fails or errors out, an error is caught in `_handle_copy_curl_request` (inside `TabsPresenter`) or `_copy_as_curl` (inside `HistoryPanel`), logged, and displayed on the status bar. Ensure that the system supports the clipboard features and `QApplication.clipboard()` is accessible.
