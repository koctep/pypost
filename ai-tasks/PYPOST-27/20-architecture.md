# PYPOST-27: Экспорт метрик через MCP (в MetricsManager)

## Исследования

1.  **Текущая реализация `MetricsManager`**:
    - Использует `wsgiref.simple_server` (синхронный).
    - Запускает отдельный поток.
    - Обрабатывает только `/metrics`.

2.  **Требуемая реализация**:
    - Должен поддерживать SSE (Server-Sent Events) для MCP.
    - `wsgiref` не поддерживает асинхронность и SSE "из коробки" удобно.
    - Лучшее решение: мигрировать `MetricsManager` на `uvicorn` + `starlette`, аналогично `MCPServerImpl`.

3.  **Совмещение Prometheus и MCP**:
    - `prometheus_client` имеет `make_asgi_app`, который можно монтировать в Starlette.
    - MCP сервер (`mcp.server.Server`) также интегрируется со Starlette.
    - Мы можем создать одно Starlette приложение с роутами:
        - `/metrics` -> Prometheus app.
        - `/sse` -> MCP SSE.
        - `/messages` -> MCP messages.

## План реализации

1.  **Рефакторинг `MetricsManager` (`pypost/core/metrics.py`)**:
    - Заменить `wsgiref` и `make_wsgi_app` на `uvicorn` и `make_asgi_app` (из `prometheus_client`).
    - Инициализировать `mcp.server.Server` внутри `MetricsManager`.
    - Настроить ресурсы MCP (`metrics://all`).
    - Создать `Starlette` приложение, объединяющее Prometheus и MCP роуты.
    - Обновить методы `start_server` и `stop_server` для работы с `uvicorn` в отдельном потоке (аналогично `MCPServerManager`).

## Архитектура

### Изменения в `pypost/core/metrics.py`

```python
import threading
import asyncio
import uvicorn
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from prometheus_client import make_asgi_app, CollectorRegistry, Counter
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.types import Resource, TextResourceContent

class MetricsManager:
    # ... Singleton logic ...

    def __init__(self):
        # ... init logic ...
        self.mcp_server = Server("pypost-metrics")
        
        # Register MCP handlers
        self.mcp_server.list_resources()(self.list_resources)
        self.mcp_server.read_resource()(self.read_resource)
        
        # ... init metrics ...

    async def list_resources(self) -> list[Resource]:
        return [Resource(
            uri="metrics://all",
            name="All Metrics",
            mimeType="text/plain"
        )]

    async def read_resource(self, uri: str) -> list[TextResourceContent]:
        if uri == "metrics://all":
             from prometheus_client import generate_latest
             data = generate_latest(self.registry).decode('utf-8')
             return [TextResourceContent(
                 uri=uri,
                 mimeType="text/plain",
                 text=data
             )]
        raise ValueError("Resource not found")

    def create_app(self):
        # 1. Prometheus app
        prometheus_app = make_asgi_app(registry=self.registry)
        
        # 2. MCP Transport setup (SSE)
        sse = SseServerTransport("/messages")

        async def handle_sse(scope, receive, send):
            async with sse.connect_sse(scope, receive, send) as streams:
                await self.mcp_server.run(streams[0], streams[1], self.mcp_server.create_initialization_options())

        async def handle_messages(scope, receive, send):
            await sse.handle_post_message(scope, receive, send)

        # 3. Combine in Starlette
        return Starlette(routes=[
            Mount("/metrics", app=prometheus_app),
            Route("/sse", endpoint=handle_sse),
            Route("/messages", endpoint=handle_messages, methods=["POST"])
        ])

    def start_server(self, host, port):
        # Logic to start uvicorn in a thread
        pass
```

### Взаимодействие компонентов

- **MetricsManager** теперь самодостаточный сервер, предоставляющий и HTTP (Prometheus), и MCP (SSE) интерфейсы.
- **Основное приложение** продолжает использовать `MetricsManager` для записи метрик через методы `track_*`.

## Вопросы и ответы

**В: Не будет ли `uvicorn` слишком "тяжелым" для простого сервера метрик?**
О: `uvicorn` достаточно легок, и унификация стека (использование той же технологии, что и в основном MCP сервере) упрощает поддержку.

**В: Как управлять жизненным циклом asyncio loop в потоке?**
О: Так же, как в `MCPServerManager`: создавать новый loop при старте потока и передавать его в `uvicorn.Config`.

