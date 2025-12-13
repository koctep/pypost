# Architecture: PYPOST-19 - MCP Server Integration

## 1. Исследования

### 1.1. Model Context Protocol (MCP) Python SDK
SDK `mcp` предоставляет абстракции для создания серверов и клиентов.
Для реализации сервера с транспортом SSE (Server-Sent Events) необходимо
использовать интеграцию с ASGI-фреймворком (например, `starlette` или `fastapi`).

**Ключевые компоненты SDK:**
- `mcp.server.Server`: Основной класс сервера.
- `mcp.server.sse.SseServerTransport`: Транспорт для SSE.
- `mcp.types`: Типы данных (Tool, TextContent, etc.).

**Поток работы SSE сервера:**
1. Клиент подключается к `/sse` (GET).
2. Сервер отправляет endpoint для POST запросов (например, `/messages`).
3. Клиент отправляет JSON-RPC сообщения на endpoint POST.
4. Сервер стримит ответы через открытое SSE соединение.

### 1.2. Интеграция с PyPost
Так как PyPost - это PyQt (PySide6) приложение с блокирующим GUI циклом,
MCP сервер (использующий `asyncio`/`uvicorn`) должен запускаться
в **отдельном процессе** или **потоке с отдельным event loop**.
Учитывая GIL и конфликты зависимостей, **отдельный процесс**
(`multiprocessing`/`subprocess`) более надежен для изоляции.
**Отдельный поток** (`threading`) позволит иметь доступ к общим
объектам (Settings, RequestData), но требует синхронизации.
*Решение*: Запуск сервера в отдельном `QThread` или `threading.Thread`, который
запускает `uvicorn.run()` внутри. Так как `uvicorn` блокирует поток,
это не заблокирует GUI. Доступ к данным read-only (копии запросов).

## 2. Архитектура компонентов

### 2.1. `MCPServerManager` (Новый класс)
Отвечает за жизненный цикл сервера.
- **Location**: `pypost/core/mcp_server.py`
- **Responsibilities**:
  - `start_server(port, tools)`: Запуск сервера в отдельном потоке.
  - `stop_server()`: Остановка сервера (graceful shutdown).
  - `update_tools(tools)`: Обновление списка (через рестарт).
- **Signals**:
  - `server_status_changed(bool)`: Для обновления UI.

### 2.2. Модуль сервера (`pypost/core/mcp_server_impl.py`)
Содержит саму логику FastMcp/Starlette приложения.
- Инициализация `mcp.server.Server`.
- Регистрация инструментов (Tools) на основе `RequestData`.
- Реализация хендлера `call_tool`.
- Функция `create_app()` возвращающая Starlette app.

### 2.3. Интеграция в `MainWindow` / `EnvironmentManager`
- При смене активного Environment проверять флаг `enable_mcp`.
- Если `True` -> `MCPServerManager.start()`.
- Если `False` -> `MCPServerManager.stop()`.

### 2.4. Исполнение запросов (Tool Execution)
Когда MCP вызывает инструмент:
1. `MCPServer` получает вызов `call_tool`.
2. Извлекает аргументы.
3. Формирует контекст: `variables = { "mcp": { "request": args } }`.
4. Использует существующий `HTTPClient`/`RequestWorker`.
   - *Важно*: `HTTPClient` синхронный. В `async` хендлере сервера
     его нужно вызывать через `run_in_threadpool`.

## 3. Схема данных

### 3.1. Settings & Environment
- `AppSettings`: `mcp_port: int = 1080`
- `Environment`: `enable_mcp: bool = False`

### 3.2. RequestData
- `expose_as_mcp: bool = False`

## 4. План реализации

1.  **Модели**: Добавить поля в `AppSettings`, `Environment`, `RequestData`.
2.  **Core**: Создать `pypost/core/mcp_server.py` с `Starlette` + `mcp`.
    - Генерация JSON Schema из `{{ mcp.request.x }}`.
    - `call_tool` (рендеринг + отправка).
3.  **Manager**: `MCPServerManager` для управления `uvicorn`.
4.  **UI**:
    - Настройки в `SettingsDialog` (порт).
    - Чекбокс "Enable MCP" в `EnvDialog`.
    - Чекбокс "Expose as MCP Tool" в `RequestEditor`.
    - Индикатор статуса в статус-баре.
5.  **Wiring**: Подключить сигналы смены окружения.

## 5. Вопросы и ответы

**Q: Как передать аргументы в запрос?**
A: Аргументы доступны в Jinja2 как `mcp.request.<arg_name>`.

**Q: Как сервер узнает об изменениях в запросах?**
A: Рестарт сервера при смене окружения.
*Уточнение*: При сохранении коллекции можно триггерить рестарт.
