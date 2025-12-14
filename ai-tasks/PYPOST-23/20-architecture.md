# PYPOST-23: Fix AttributeError in MCP Server SSE Handling - Architecture

## Проблема

В методе `MCPServerImpl.create_app` при инициализации SSE соединения вызывается `sse.create_initialization_options()`.
Объект `sse` является экземпляром `SseServerTransport`, который не имеет метода `create_initialization_options`.
Этот метод принадлежит классу `Server` (экземпляр `self.server`).

## Решение

Изменить вызов метода в файле `pypost/core/mcp_server_impl.py`:

```python
# Было
await self.server.run(streams[0], streams[1], sse.create_initialization_options())

# Стало
await self.server.run(streams[0], streams[1], self.server.create_initialization_options())
```

## Влияние

- Исправляет падение сервера при подключении к SSE.
- Не влияет на другие компоненты.
