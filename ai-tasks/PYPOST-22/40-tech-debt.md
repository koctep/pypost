# PYPOST-22: Technical Debt Analysis

## Shortcuts Taken

- Валидация IP адреса (host) отсутствует в UI. `uvicorn` выдаст ошибку при старте, если адрес некорректен, но пользователю это не будет очевидно до запуска.

## Code Quality Issues

- `MainWindow.on_env_changed` отвечает и за обновление переменных, и за управление сервером MCP. Возможно, стоит вынести логику управления состоянием MCP в отдельный контроллер или расширить `MCPServerManager`.

## Missing Tests

- Отсутствуют unit-тесты для `MCPServerManager`, проверяющие корректность передачи `host` в `uvicorn.Config`.
- Нет UI тестов для `SettingsDialog`, проверяющих сохранение нового поля.

## Performance Concerns

- Нет.

## Follow-up Tasks

- Добавить валидацию IP адреса в `SettingsDialog` (например, через `QValidator`).
- Написать тесты для конфигурации MCP сервера.
