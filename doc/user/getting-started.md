# Getting Started

## Requirements

- Python 3.11 or newer
- Make (optional; simplifies install and run)

## Install

From the project root:

```bash
make install
```

This creates a `.venv` virtual environment and installs dependencies.

### Manual install

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev,otel]"
```

## Run

```bash
make run
```

Or with an activated virtual environment:

```bash
PYTHONPATH=. python pypost/main.py
```

There is no separate end-user CLI for sending requests — the desktop app is the primary
interface. Local HTTP endpoints exist only for MCP (default port 1080) and Prometheus
metrics (default port 9080).

## First steps

1. Start PyPost with `make run`.
2. Open **Manage Environments** (`Ctrl+E`), create an environment (for example `Local`),
   and add a variable such as `host` = `https://httpbin.org`.
3. Select that environment in the top dropdown.
4. Press `Ctrl+N` for a new tab. Set method **GET** and URL `{{ host }}/get`.
5. Click **Send** (or press `F5` / `Ctrl+Enter`).
6. Inspect status, timing, and body in the response pane.
7. Open **Actions → Save** (`Ctrl+S`) and store the request in a new collection.

### First-run workflow diagram

```text
+-----------------------+     +-----------------------+     +-----------------------+
| 1. Define Environment | --> | 2. Compose Request    | --> | 3. Send & Inspect     |
| [Local v]             |     | [GET] {{ host }}/get  |     | Status: 200 OK        |
| host=https://...      |     | Headers / JSON Body   |     | Time: 120ms | Size    |
+-----------------------+     +-----------------------+     +-----------------------+
                                                                        |
                                                                        v
                                                            +-----------------------+
                                                            | 4. Save to Collection |
                                                            | Actions -> Save       |
                                                            | [My APIs / Get Users] |
                                                            +-----------------------+
```

Next: [Interface](interface.md) or jump to [Common Workflows](workflows.md).

## Where data is stored

PyPost uses platform-standard directories (`platformdirs`):

| Kind | Typical contents |
| ---- | ---------------- |
| Config dir | `settings.json` |
| Data dir | `collections/`, `environments.json`, `history.json`, alert log |

On macOS these usually live under Application Support for the `pypost` app name. Exact
paths depend on your OS.

## Optional: MCP for AI agents

If you want Cursor or another agent to call your saved requests:

1. Mark a request as **MCP Tool** and save it.
2. Open **MCP Servers…**, add a row selecting the request's collection and intended
   environment, then save and start it.
3. Point the agent at that row's `http://<host>:<port>/mcp` URL.

See [MCP Tools for AI Agents](mcp-tools.md).
