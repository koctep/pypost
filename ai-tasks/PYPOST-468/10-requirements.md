# PYPOST-468: Add action 'Copy cURL'

## Goals

From a business perspective, users need to easily share or reproduce their API requests outside of the PyPost application. By providing a "Copy cURL" action, users can instantly convert a configured request into a standard command-line format that can be pasted into a terminal or sent to colleagues for debugging.

## User Stories

- As a user, I want to click a "Copy cURL" button or menu item on a request so that I get a valid cURL command copied to my clipboard.
- As a user, I want the copied cURL command to include all relevant request details (method, URL, headers, and body) so that it perfectly matches what PyPost executes.
- As a user, I want to see a brief confirmation or notification when the cURL has been successfully copied.

## Definition of Done

- A "Copy cURL" action is available for API requests in the UI.
- Activating the action copies a correctly formatted cURL string to the system clipboard.
- The cURL string includes: HTTP method, full URL (with query parameters), headers (including authorization), and the request body (if applicable).
- The user is notified (e.g., via a toast or status message) that the command has been copied.

## Task Description

The current system lacks an easy way to export an existing request configuration into a widely-used format. The goal of this task is to implement an action that generates a cURL command equivalent to the selected request.

- **Programming language:** Python
- **Scope:** The feature will affect the UI where requests are managed/viewed, and require a capability to translate a request into a cURL command string. System clipboard integration is required.
- **Constraints/Assumptions:** We assume that the application already has access to the full constructed request (including resolved environment variables) before generating the cURL. 
- **Main Entities:**
  - `Request`: The business object representing an API call (method, URL, headers, body).
  - `Clipboard`: System clipboard service where the result is stored.

## Q&A

- **Q:** Are environment variables resolved in the cURL command?
  - **A:** Yes, the cURL should represent the actual executed request, so variables should be resolved.
- **Q:** How are binary payloads handled?
  - **A:** This will need to be decided during architecture, but generally standard text/JSON payloads are the primary focus.