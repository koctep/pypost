# PYPOST-469: Copy from history page

## Goals

Allow users to easily share or reproduce past requests by copying them as cURL commands directly from the history view.

## User Stories

- As a user, I want to right-click a request in the history list and select "Copy as cURL" so that I can easily share the request or run it in a terminal.
- As a power user, I want to use the standard copy keyboard shortcut (Cmd/Ctrl+C) on a selected history item to quickly copy it as a cURL command.
- As a user, I want to see a confirmation message in the status bar when the request is successfully copied to the clipboard.

## Definition of Done

- A context menu option "Copy as cURL" is available when right-clicking an item in the history list.
- Pressing Cmd/Ctrl+C while a history item is selected copies the item as a cURL command.
- The copied content is a valid cURL command representing the historical request.
- A success message (e.g., "Copied to clipboard") is displayed in the status bar after copying.
- The clipboard contains the expected cURL string.

## Task Description

Implement functionality to copy history items as cURL commands to the system clipboard. The action should be accessible via both a context menu and a keyboard shortcut, with visual feedback provided in the application's status bar.

**Programming Language**: Python

### Functional Requirements
- Generate a cURL command string from a selected history item.
- Add a context menu to the history list widget with a "Copy as cURL" action.
- Bind the standard copy shortcut (Cmd/Ctrl+C) to the copy action in the history list widget.
- Write the generated cURL string to the system clipboard.
- Emit a signal or call a method to display a temporary message in the main window's status bar upon successful copy.

### Non-functional Requirements
- The copy operation should be synchronous but fast enough not to cause noticeable UI lag.
- The generated cURL command must accurately reflect the request method, URL, headers, and body stored in the history.

### Constraints and Assumptions
- Assumes the existence of a cURL generation utility (likely `curl_generator.py` based on git status).
- Assumes the history item contains all necessary request data to generate the cURL.

### Main Entities and Attributes
- **History Item**: Contains request data (URL, method, headers, body).
- **Clipboard**: System clipboard where the text is placed.
- **Status Bar**: UI component for displaying the success message.

## Q&A

- **Q:** What data should be copied? **A:** cURL command.
- **Q:** How should the copy action be triggered? **A:** Context menu (right-click) and Keyboard shortcut (Cmd/Ctrl+C).
- **Q:** What visual feedback should be provided? **A:** Status bar message.