# PYPOST-28: Create Example Collection for MCP Testing

## Исследования

- Анализ `doc/dev/mcp_integration.md`: выявлено наличие двух встроенных серверов (Main MCP: 1080, Metrics MCP: 9091).
- **Корректировка**: Анализ `pypost/models/settings.py` показал, что порт Metrics Server по умолчанию равен **9080**, а не 9091.
- Сервер Metrics (9080) предоставляет стандартный endpoint `/metrics` и MCP endpoints.

## План реализации

1.  Создать директорию `examples/collections/` (если не существует).
2.  Сгенерировать UUID для коллекции и запросов.
3.  Создать JSON структуру, соответствующую `Collection` Pydantic модели.
4.  Заполнить коллекцию запросами к локальным серверам PyPost:
    - Get Metrics (9080)
    - MCP Connect SSE (9080)
    - MCP List Resources (9080)
    - Main MCP Connect SSE (1080)
5.  Установить `expose_as_mcp: true` для всех запросов.

## Архитектура

**Структура файла `examples/collections/mcp.json`:**

```json
{
  "id": "uuid",
  "name": "MCP Test Collection",
  "requests": [
    {
      "id": "uuid",
      "name": "Metrics (GET)",
      "method": "GET",
      "url": "http://localhost:9080/metrics",
      "expose_as_mcp": true,
      ...
    },
    ...
  ]
}
```

## Вопросы и ответы

Нет архитектурных вопросов.

