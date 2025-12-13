# PYPOST-22: Configurable MCP Server Host

## Исследования

Текущая реализация MCP сервера использует `uvicorn` для запуска ASGI приложения. `uvicorn.Config` принимает параметры `host` и `port`. В данный момент `host` жестко задан как `"127.0.0.1"`, а `port` берется из настроек.

Для реализации задачи необходимо пробросить параметр `host` из `AppSettings` через `MCPServerManager` в `uvicorn.Config`.

## План реализации

1.  **Модель настроек (`pypost/models/settings.py`)**:
    - Добавить поле `mcp_host: str = "127.0.0.1"` в класс `AppSettings`.

2.  **UI настроек (`pypost/ui/dialogs/settings_dialog.py`)**:
    - Добавить `QLineEdit` для ввода хоста.
    - Обновить метод `accept` для сохранения значения.

3.  **MCP Сервер Менеджер (`pypost/core/mcp_server.py`)**:
    - Обновить сигнатуру `start_server` для приема аргумента `host`.
    - Сохранять `host` в атрибуте экземпляра `self._current_host`.
    - Использовать `self._current_host` при создании `uvicorn.Config`.

4.  **Главное окно (`pypost/ui/main_window.py`)**:
    - Обновить вызов `self.mcp_manager.start_server`, передавая `self.settings.mcp_host`.
    - Обновить логику перезапуска сервера при изменении настроек в `open_settings` (при необходимости, если хост изменился).

## Архитектура

### Диаграмма компонентов

```mermaid
graph TD
    SettingsDialog[UI: SettingsDialog] -->|updates| AppSettings[Model: AppSettings]
    MainWindow[UI: MainWindow] -->|reads| AppSettings
    MainWindow -->|calls start_server(host, port)| MCPServerManager[Core: MCPServerManager]
    MCPServerManager -->|runs| Uvicorn[Uvicorn Server]
```

### Изменения в модулях

#### `pypost/models/settings.py`

```python
class AppSettings(BaseModel):
    # ... existing fields ...
    mcp_host: str = "127.0.0.1"  # New field
```

#### `pypost/ui/dialogs/settings_dialog.py`

```python
class SettingsDialog(QDialog):
    def __init__(self, ...):
        # ...
        self.mcp_host_edit = QLineEdit()
        self.mcp_host_edit.setText(current_settings.mcp_host)
        self.form_layout.addRow("MCP Server Host:", self.mcp_host_edit)
        # ...
    
    def accept(self):
        self.new_settings = AppSettings(
            # ...
            mcp_host=self.mcp_host_edit.text(),
            # ...
        )
```

#### `pypost/core/mcp_server.py`

```python
class MCPServerManager(QObject):
    def __init__(self):
        # ...
        self._current_host = "127.0.0.1"

    def start_server(self, port: int, tools: List[RequestData], host: str = "127.0.0.1"):
        # ...
        self._current_host = host
        # ...

    def _run_uvicorn(self):
        # ...
        config = uvicorn.Config(..., host=self._current_host, ...)
        # ...
```

#### `pypost/ui/main_window.py`

```python
class MainWindow(QMainWindow):
    def on_env_changed(self, index):
        # ...
        if selected_env.enable_mcp:
            # ...
            self.mcp_manager.start_server(
                port=self.settings.mcp_port, 
                tools=tools,
                host=self.settings.mcp_host # Pass host
            )
        # ...
```

## Вопросы и ответы

- **Нужно ли перезапускать сервер при изменении хоста?**
  - Да, `uvicorn` не поддерживает динамическую смену биндинга без перезапуска. Логика в `MainWindow` уже обрабатывает перезапуск при смене порта/настроек.

- **Как проверить валидность хоста?**
  - Если пользователь введет некорректный хост, `uvicorn` выбросит исключение при старте. Желательно добавить `try-except` в поток запуска сервера или выводить ошибку, но для текущей задачи достаточно того, что сервер просто не запустится или упадет с ошибкой в лог. В будущем можно добавить валидацию в UI.
