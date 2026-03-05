# PyPost User Guide

PyPost is an API testing tool that allows you to send HTTP requests, view responses, and organize requests into collections.

## Contents

1.  [Getting Started](#getting-started)
2.  [Interface](#interface)
3.  [Working with Requests](#working-with-requests)
    *   [Creating a Request](#creating-a-request)
    *   [Parameters and Headers](#parameters-and-headers)
    *   [Request Body](#request-body)
    *   [Scripts](#scripts)
4.  [Collections](#collections)
5.  [Environment Variables](#environment-variables)
6.  [Templating](#templating)
7.  [Hotkeys](#hotkeys)

## Getting Started

Run the application with the command:
```bash
make run
```

Or manually from the virtual environment:
```bash
python pypost/main.py
```

## Interface

The main application window is divided into several main areas:

1.  **Menu Bar (top)**: Provides access to file management (**File**) and help (**Help**).
2.  **Environment Panel (below menu)**: Select active environment and access settings.
3.  **Sidebar (left)**: Tree of collections and saved requests.
4.  **Workspace (right)**: Tabs with request editors.

## Working with Requests

### Creating a Request

To create a new request, press `Ctrl+N` or click the `+` button in the tab bar.

In the request editor, you can configure:
*   **Method**: GET, POST, PUT, DELETE, PATCH.
*   **URL**: Resource address.
*   **Params**: URL parameters (Query params).
*   **Headers**: HTTP headers.
*   **Body**: Request body (for POST/PUT methods).

### Parameters and Headers

In the **Params** and **Headers** tabs, a "Key-Value" table editor is used.
*   Enter key and value.
*   A new empty row is added automatically when the last one is filled.

### Request Body

In the **Body** tab, you can enter the text content of the request (e.g., JSON, XML, Plain Text).

### Scripts

In the **Script** tab, you can write Python code that will be executed **after** receiving a response. This is useful for automation, for example, saving a received token to environment variables.

Available objects:
*   `response`: Response object (methods `.json()`, `.text`, `.status_code`, `.headers`).
*   `request`: Sent request object.
*   `pypost`: Main object for interaction with the application.

**Examples:**

Saving a token from a JSON response to an environment variable:
```python
token = response.json()['token']
pypost.env.set('auth_token', token)
```

Checking status code (output to console/log):
```python
if response.status_code != 200:
    print(f"Error: {response.status_code}")
```

## Collections

Collections allow grouping requests into folders.

*   To save a request to a collection, open **Actions** (right of **Send**) and select
    **Save**, or press `Ctrl+S`.
*   To save a modified request as a new entry, open **Actions** and select **Save As...**.
    This always creates a new request and leaves the original request unchanged.
*   In the save dialog, select an existing collection or create a new one.
*   Requests in the sidebar can be opened with a double click (or single click if configured).

## Environment Variables

Environment variables allow storing configuration data (hosts, tokens, API keys) and switching between them (e.g., `Local`, `Dev`, `Prod`).

1.  Click the **Manage** button in the top panel (or `Ctrl+E`).
2.  Create a new environment (`+` button).
3.  Add variables to the Key-Value table.
4.  Save changes.

Select an environment in the dropdown list at the top to activate its variables.

## Templating

You can use environment variables in URL, headers, parameters, and request body using Jinja2 syntax: `{{ variable_name }}`.

**Example:**
If the active environment has a `host` variable with value `https://api.example.com`, then in the URL field you can write:
`{{ host }}/users`

This will be converted to `https://api.example.com/users` before sending the request.

## Hotkeys

| Action | Shortcut |
| :--- | :--- |
| **Application Control** | |
| Exit | `Ctrl+Q` |
| Settings | `Ctrl+,` or `F12` |
| Environment Manager | `Ctrl+E` |
| **Tab Management** | |
| New Tab | `Ctrl+N` |
| Close Tab | `Ctrl+W` |
| Next Tab | `Ctrl+Tab` |
| Previous Tab | `Ctrl+Shift+Tab` |
| Switch to Tab N | `Alt+1` ... `Alt+9` |
| **Request Editor** | |
| Send Request | `F5` or `Ctrl+Enter` |
| Save Request | `Ctrl+S` |
| Save As Request | `Ctrl+Shift+S` |
| Focus on URL | `Ctrl+L` or `Alt+D` |
| Params Tab | `Ctrl+P` |
| Headers Tab | `Ctrl+H` |
| Body Tab | `Ctrl+B` |
| Script Tab | `Ctrl+T` |
