# PyPost

PyPost is a lightweight HTTP client with a graphical interface, written in Python using PySide6. The application is designed for API testing and sending HTTP requests, providing a convenient tool for developers, similar to Postman.

## Features

*   **Send HTTP Requests**: Support for main methods (GET, POST, PUT, DELETE, PATCH, etc.).
*   **Collection Management**: Organize requests into collections for easy access and reuse.
*   **Request Editor**: Convenient interface for configuring headers, parameters, and request body.
*   **Response Viewer**: Display status, headers, and response body (JSON, text, etc.).
*   **Environment Variables**: Support for environment variables to switch between configurations (e.g., dev/prod).
*   **Templating**: Use Jinja2 for dynamic data generation in requests.

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
    This will create a virtual environment (`venv`) and install all necessary libraries.

### Manual Installation

1.  Create a virtual environment:
    ```bash
    python3 -m venv venv
    ```

2.  Activate the virtual environment:
    *   Linux/macOS: `source venv/bin/activate`
    *   Windows: `venv\Scripts\activate`

3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
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

*   `make lint` — check code with linter (flake8).
*   `make test` — run tests (pytest).
*   `make clean` — clean temporary files and virtual environment.
