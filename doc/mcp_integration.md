# PyPost MCP Integration

PyPost supports the **Model Context Protocol (MCP)**, allowing it to act as a server for AI agents (like Claude Desktop, Cursor, etc.).

## What is it?

You can expose your saved HTTP requests as "tools" for AI. The AI agent can then execute these requests directly from the chat interface.

## How to use

1.  **Configure Request**:
    -   Open a request in PyPost.
    -   Check the **"MCP Tool"** checkbox (next to the URL bar).
    -   Save the request.

2.  **Enable Server**:
    -   Go to **Manage Environments**.
    -   Select your environment.
    -   Check **"Enable MCP Server"**.
    -   (Optional) Change port (default 8000).
    -   Click **Save**.
    -   You should see "MCP: ON" in the top bar.

3.  **Connect Agent**:
    -   In your AI agent configuration (e.g., `claude_desktop_config.json`), add PyPost as an MCP server:

    ```json
    {
      "mcpServers": {
        "pypost": {
          "command": "python", // Or path to python in venv
          "args": ["-m", "pypost.main"], // NOTE: PyPost currently runs as SSE server, not stdio
          // For SSE support, use the URL:
          "url": "http://localhost:8000/sse"
        }
      }
    }
    ```
    *Note: Client support for SSE varies. Check your agent's documentation.*

<<<<<<< HEAD
4.  **Use**:
    -   Ask the agent: "Call the 'Get Users' tool".
    -   The agent will execute the request via PyPost and see the response.
=======
### Cursor

В настройках Cursor (Features > MCP):
1. Добавьте новый сервер.
2. Type: **SSE**.
3. URL: `http://localhost:1080/sse`.

Теперь вы можете в чате Cursor использовать `@MCP` и видеть ваши запросы из PyPost.

## Настройки сервера

Вы можете изменить настройки MCP сервера в глобальных настройках (**Settings**):
- **MCP Server Port**: по умолчанию `1080`.
- **MCP Server Host**: по умолчанию `127.0.0.1`. Измените на `0.0.0.0`, чтобы сделать сервер доступным из внешней сети.

Если порт занят или хост недоступен, сервер не сможет запуститься (следите за ошибками в консоли/логах).
>>>>>>> 24e64fc (feat(mcp): PYPOST-22 configurable MCP server host)
