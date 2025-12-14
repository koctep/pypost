# PYPOST-23: Fix AttributeError in MCP Server SSE Handling

## Цели

Исправить ошибку `AttributeError: 'SseServerTransport' object has no attribute 'create_initialization_options'`, возникающую при подключении к SSE endpoint'у MCP сервера.

## Пользовательские истории

- Как пользователь, я хочу, чтобы MCP сервер корректно обрабатывал SSE подключения, чтобы я мог использовать инструменты через MCP протокол.

## Критерии готовности

- [ ] Метод `handle_sse` в `pypost/core/mcp_server_impl.py` не вызывает несуществующий метод `create_initialization_options`.
- [ ] Сервер успешно запускается и обрабатывает SSE запросы без падения.
- [ ] Инициализация сервера (`self.server.run`) происходит с корректными аргументами.

## Описание задачи

При обращении к `/sse` происходит падение сервера с ошибкой:
```
AttributeError: 'SseServerTransport' object has no attribute 'create_initialization_options'
```
Это происходит в строке 147 файла `pypost/core/mcp_server_impl.py`.
Необходимо выяснить правильный способ инициализации `server.run` с использованием `SseServerTransport` из установленной версии библиотеки `mcp`.

## Вопросы и ответы

- **Q:** Какая версия библиотеки `mcp` используется?
  - **A:** Нужно проверить в окружении.
- **Q:** Как правильно передать initialization options?
  - **A:** Вероятно, они либо не нужны, либо передаются иначе.
