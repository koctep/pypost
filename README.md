# PyPost

PyPost is a lightweight HTTP client with a graphical interface, written in Python using
PySide6. It helps developers test APIs and turn saved HTTP requests into tools for local
AI agents via the Model Context Protocol (MCP).

## Vision

**Turn your existing HTTP requests into safe MCP tools for your local AI agent — in
seconds, through the UI, without writing server code.**

Today, giving an AI agent access to your APIs usually means building and maintaining an
MCP server by hand: re-describing endpoints, auth, and parameters, with little control
over what the agent sees or whether secrets leak. You already have working requests in
your API client — PyPost closes that gap.

**North star:** any request you mark as an MCP tool is reliably available to your local
agent as a correctly working tool — with a clear name, description, and parameters,
environment variables resolved, and secrets handled safely.

**Principles:** safety by default; you see more than the agent — secrets stay hidden and
are never shared with agents; reuse over rebuild; local-first; operator monitors via
Prometheus, agent gets context in each tool response.

**Observability:** PyPost exposes Prometheus metrics at `/metrics` (default port 9080) for
monitoring request volume, MCP tool usage, and errors. Operational events stay on your
machine — the AI agent gets context in each tool response, not via a separate event stream.

See [Prometheus Monitoring](doc/prometheus_monitoring.md) for scrape setup and counter
reference, and [MCP Integration](doc/mcp_integration.md) for agent setup.

## Features

*   **Send HTTP Requests**: Support for main methods (GET, POST, PUT, DELETE, PATCH, etc.).
*   **Collection Management**: Organize requests into collections for easy access and reuse.
*   **Request Editor**: Convenient interface for configuring headers, parameters, and request body.
*   **Response Viewer**: Display status, headers, and response body (JSON, text, etc.).
*   **Environment Variables**: Support for environment variables to switch between
    configurations (e.g., dev/prod).
*   **Templating**: Use Jinja2 for dynamic data generation in requests.
*   **MCP Tools**: Expose saved requests as MCP tools for local AI agents (e.g. Cursor).
*   **Prometheus Metrics**: Scrape `/metrics` for request, MCP, and error counters (default port
    9080). See [Prometheus Monitoring](doc/prometheus_monitoring.md).

## Requirements

*   Python 3.11+
*   Make (optional, for using Makefile)

## Installation

To simplify the installation and startup process, a `Makefile` is provided in the project.

### Using Make

1.  **Install dependencies:**
    ```bash
    make install
    ```
    This will create a virtual environment (`.venv`) and install all necessary libraries.

### Manual Installation

1.  Create a virtual environment:
    ```bash
    python3 -m venv .venv
    ```

2.  Activate the virtual environment:
    *   Linux/macOS: `source .venv/bin/activate`
    *   Windows: `.venv\Scripts\activate`

3.  Install dependencies:
    ```bash
    pip install -e ".[dev,otel]"
    ```

## Running

### Using Make

```bash
make run
```

### Manual Run

Make sure the virtual environment is activated, and run:
```bash
PYTHONPATH=. python pypost/main.py
```

## Development

Additional commands for developers are available in the project:

*   [Developer documentation](doc/dev/README.md) — setup, architecture, capability docs, and audits.
*   `make lint` — check code with linter (flake8).
*   `make test` — run tests (pytest).
*   `make clean` — clean temporary files and virtual environment.
