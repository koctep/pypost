# Copy cURL Feature

## Overview
The "Copy cURL" feature allows developers to generate a valid cURL command based on their currently configured HTTP request in the UI (including method, URL, headers, and body), render it with their current environment variables, and copy it directly to their system clipboard.

## Architecture
- **`CurlGenerator` (`pypost/core/curl_generator.py`)**: The core utility class responsible for taking a `RequestData` object, rendering variables, and constructing a shell-escaped cURL command array/string.
- **`RequestWidget` (`pypost/ui/widgets/request_editor.py`)**: The UI component that presents the "Copy cURL" action inside the "Actions" drop-down menu. It emits a `copy_curl_requested` signal containing the current `RequestData` when triggered.
- **`TabsPresenter` (`pypost/ui/presenters/tabs_presenter.py`)**: Acts as the orchestrator. It connects to the `copy_curl_requested` signal, uses `CurlGenerator` to render the command with the currently active environment variables, and copies the resulting string to the system clipboard using `QApplication.clipboard().setText()`.

## API / Usage

### `CurlGenerator.generate(request, variables, template_service)`
Generates a valid cURL command string from the request data and variables.

- **request** (`RequestData`): The request configuration including URL, method, headers, parameters, and body.
- **variables** (`dict`): The current environment variables to render templates with.
- **template_service** (`TemplateService`): The service responsible for interpolating variables into the strings.
- **Returns** (`str`): The properly escaped cURL command string (uses `subprocess.list2cmdline` on Windows, and `shlex.join` on Unix).

## Configuration
There are no specific configuration settings for this feature. It relies on the active environment variables and the current request data.

## Troubleshooting
- **Missing or incorrect variables**: If variables are not correctly resolved in the generated cURL command, ensure that the active environment contains the expected keys, and check the status of `TemplateService` rendering.
- **Copy to clipboard failing**: In case the copy operation fails or errors out, an error is caught in `_handle_copy_curl_request` (inside `TabsPresenter`), logged, and displayed on the status bar. Ensure that the system supports the clipboard features and `QApplication.clipboard()` is accessible.
